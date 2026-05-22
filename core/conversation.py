from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import asyncio
from agents import ExamAnalyzerAgent, SocraticGuideAgent, AdaptiveTutorAgent
from agents.base import AgentContext, AgentResult
from permissions import PermissionManager, ActionType
from planning import PlanManager, PlanStatus
from hooks import HookManager, HookType, create_content_filter_hook, create_difficulty_adjuster_hook
from recovery import ConversationRecovery
from .state import StudentStateManager

@dataclass
class ConversationTurn:
    turn_id: int; user_input: str
    agent_results: List[AgentResult] = field(default_factory=list)
    final_response: str = ''
    timestamp: float = field(default_factory=lambda: __import__('time').time())

class ConversationManager:
    def __init__(self, student_id):
        self.student_id = student_id
        self.context = AgentContext(student_id=student_id)
        self.state_manager = StudentStateManager()
        self.analyzer = ExamAnalyzerAgent()
        self.guide = SocraticGuideAgent()
        self.adaptive = AdaptiveTutorAgent()
        self.permission_manager = PermissionManager()
        self.plan_manager = PlanManager()
        self.hook_manager = HookManager()
        self.recovery = ConversationRecovery()
        self._setup_hooks()
        self.conversation_history: List[ConversationTurn] = []
        self.current_turn = 0
        self.snapshot_counter = 0

    def _setup_hooks(self):
        self.hook_manager.register(create_content_filter_hook())
        self.hook_manager.register(create_difficulty_adjuster_hook())

    async def process_message(self, user_input):
        self.current_turn += 1
        turn = ConversationTurn(turn_id=self.current_turn, user_input=user_input)
        if self.current_turn == 1 or self._is_new_question(user_input):
            result = await self._handle_new_question(user_input)
        else:
            result = await self._handle_student_response(user_input)
        turn.agent_results = result.get('agent_results', [])
        turn.final_response = result.get('response', '')
        self.conversation_history.append(turn)
        self.state_manager.save_state(self.student_id, self.context)
        return result

    async def _handle_new_question(self, question):
        agent_results = []
        hook_data = await self.hook_manager.execute_hooks(HookType.PRE_PROCESS, {'question': question}, {'student_id': self.student_id})
        question = hook_data.get('question', question)
        analyzer_result = await self.analyzer.execute({'question': question}, self.context)
        agent_results.append(analyzer_result)
        if not analyzer_result.success:
            return {'success': False, 'response': '抱歉，我无法理解你的问题。请尝试更详细地描述。', 'agent_results': agent_results}
        plan_id = f'plan_{self.student_id}_{self.current_turn}'
        plan = self.plan_manager.create_plan(plan_id, question, analyzer_result.data)
        guide_result = await self.guide.execute({'question': question, 'analysis': analyzer_result.data}, self.context)
        agent_results.append(guide_result)
        hook_data = await self.hook_manager.execute_hooks(HookType.POST_AGENT,
            {'analysis': analyzer_result.data, 'guidance': guide_result.data},
            {'understanding_level': self.context.understanding_level})
        response = self._format_guidance_response(analyzer_result.data, guide_result.data, plan)
        hook_data = await self.hook_manager.execute_hooks(HookType.PRE_RESPONSE, {'content': response},
            {'understanding_level': self.context.understanding_level})
        response = hook_data.get('content', response)
        self._create_snapshot()
        return {'success': True, 'response': response, 'agent_results': agent_results,
                'analysis': analyzer_result.data, 'guidance': guide_result.data, 'plan': plan.to_dict()}

    async def _handle_student_response(self, response):
        agent_results = []
        previous_guidance = {}
        if self.conversation_history:
            for r in self.conversation_history[-1].agent_results:
                if r.data and 'questions' in r.data: previous_guidance = r.data; break
        adaptive_result = await self.adaptive.execute({'student_response': response, 'previous_guidance': previous_guidance}, self.context)
        agent_results.append(adaptive_result)
        if not adaptive_result.success:
            return {'success': False, 'response': '让我重新理解一下你的思路...', 'agent_results': agent_results}
        adjustment = adaptive_result.data
        if adjustment['updated_level'] >= 8:
            response = self._format_completion_response(adjustment)
        else:
            guide_result = await self.guide.execute({'question': response, 'analysis': {'knowledge_points': [self.context.current_topic or '']}}, self.context)
            agent_results.append(guide_result)
            response = self._format_guidance_response({}, guide_result.data)
        return {'success': True, 'response': response, 'agent_results': agent_results, 'adjustment': adjustment}

    def _is_new_question(self, text):
        if ('?' in text or '？' in text) and len(text) > 30: return True
        return any(kw in text for kw in ['怎么','如何','实现','编写','代码','算法'])

    def _format_guidance_response(self, analysis, guidance, plan=None):
        parts = []
        if analysis.get('knowledge_points'):
            parts.append(f'这个问题涉及的知识点：{chr(44).join(analysis["knowledge_points"])}')
        if plan and plan.status == PlanStatus.PENDING:
            parts.append('')
            parts.append('我为你制定了一个解题计划：')
            parts.append(f'   {plan.description}')
            parts.append('')
            parts.append('   步骤预览：')
            for i, step in enumerate(plan.steps[:3], 1):
                parts.append(f'   {i}. {step.description}')
            parts.append('')
            parts.append("   你可以回复'确认计划'开始执行，或者直接开始思考。")
        questions = guidance.get('questions', [])
        if questions:
            parts.append('')
            parts.append('让我们一步步来思考：')
            for i, q in enumerate(questions[:3], 1):
                parts.append(f'{i}. {q}')
        hints = guidance.get('hints', [])
        if hints:
            parts.append('')
            parts.append(f'小提示：{hints[0]}')
        return '\n'.join(parts)

    def _create_snapshot(self):
        self.snapshot_counter += 1
        snapshot_id = f'{self.student_id}_snapshot_{self.snapshot_counter}'
        history = [{'turn': t.turn_id, 'input': t.user_input, 'response': t.final_response} for t in self.conversation_history]
        snapshot = self.recovery.create_snapshot(snapshot_id, self.student_id, history,
            {'understanding_level': self.context.understanding_level, 'weak_points': self.context.weak_points,
             'strong_points': self.context.strong_points, 'current_topic': self.context.current_topic})
        self.recovery.save_snapshot(snapshot)

    def _format_completion_response(self, adjustment):
        parts = ['很棒！你对这个问题的理解已经很不错了。', f'当前理解程度：{adjustment["updated_level"]}/10']
        fq = adjustment.get('follow_up_questions', [])
        if fq: parts.append(''); parts.append('想再挑战一下自己吗？'); parts.append(fq[0])
        return '\n'.join(parts)

    def get_conversation_summary(self):
        return {'student_id': self.student_id, 'total_turns': self.current_turn,
                'understanding_level': self.context.understanding_level,
                'weak_points': self.context.weak_points, 'strong_points': self.context.strong_points,
                'history': [{'turn': t.turn_id, 'input': t.user_input, 'response': t.final_response} for t in self.conversation_history]}
