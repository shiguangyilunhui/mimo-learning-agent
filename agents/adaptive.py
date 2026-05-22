from typing import Any, Dict
from .base import BaseAgent, AgentContext, AgentResult, AgentStatus

class AdaptiveTutorAgent(BaseAgent):
    def __init__(self):
        super().__init__('AdaptiveTutor', '评估学生反馈，动态调整讲解策略')
    async def execute(self, input_data, context):
        student_response = input_data.get('student_response', '')
        if not student_response:
            return AgentResult(False, {}, '学生回答为空', status=AgentStatus.ERROR)
        has_explanation = any(kw in student_response for kw in ['因为','所以','首先','然后'])
        score = (1 if len(student_response) > 50 else 0) + (2 if has_explanation else 0)
        expected = context.understanding_level // 2
        delta = 1 if score >= expected + 1 else (-1 if score <= expected - 1 else 0)
        context.update_understanding(delta)
        if delta > 0: context.strong_points.append(context.current_topic or '')
        elif delta < 0: context.weak_points.append(context.current_topic or '')
        adjustment = {
            'level_delta': delta, 'updated_level': context.understanding_level,
            'next_strategy': '回退' if delta < 0 else ('基础巩固' if context.understanding_level < 3 else '循序渐进' if context.understanding_level < 7 else '挑战提升'),
            'follow_up_questions': ['让我们回到上一步'] if delta < 0 else ['很好！你能把这个思路应用到更复杂的情况吗？'] if delta > 0 else ['让我们继续深入']
        }
        context.add_history('adaptive', f'评估结果：{delta:+d}', {'delta': delta})
        return AgentResult(True, adjustment, f'理解程度{context.understanding_level}/10',
            next_agent='SocraticGuide' if context.understanding_level < 8 else None)
