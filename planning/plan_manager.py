from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
import time

class PlanStatus(Enum):
    DRAFT='draft'; PENDING='pending'; APPROVED='approved'; REJECTED='rejected'
    EXECUTING='executing'; COMPLETED='completed'; CANCELLED='cancelled'

class StepStatus(Enum):
    PENDING='pending'; IN_PROGRESS='in_progress'; COMPLETED='completed'
    FAILED='failed'; SKIPPED='skipped'

@dataclass
class PlanStep:
    step_id: str; description: str; reasoning: str = ''; expected_outcome: str = ''
    status: StepStatus = StepStatus.PENDING; depends_on: List[str] = field(default_factory=list)

@dataclass
class Plan:
    plan_id: str; title: str; description: str
    steps: List[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    def get_progress(self):
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        return {'total': total, 'completed': completed, 'percentage': round(completed/total*100, 1) if total else 0}
    def to_dict(self):
        return {'plan_id': self.plan_id, 'title': self.title, 'description': self.description,
                'status': self.status.value, 'progress': self.get_progress(),
                'steps': [{'step_id': s.step_id, 'description': s.description, 'status': s.status.value} for s in self.steps]}

class PlanManager:
    def __init__(self): self.plans = {}
    def create_plan(self, plan_id, question, analysis):
        kp = analysis.get('knowledge_points', [])
        kp_str = chr(12289).join(kp[:2]) if kp else '编程基础'
        difficulty = analysis.get('difficulty', 'medium')
        steps = [
            PlanStep('step_1', '理解问题：明确输入输出和约束条件', '正确理解问题是解题的第一步', '能用自己的话描述问题'),
            PlanStep('step_2', f'算法分析：运用{kp_str}设计解题思路', f'题目涉及{kp_str}', '能描述算法的主要步骤'),
            PlanStep('step_3', '边界分析：考虑特殊输入和边界条件', '边界情况是代码健壮性的关键', '列出至少3个边界情况'),
            PlanStep('step_4', '代码实现：将思路转化为代码', '在充分理解后再动手编码', '完成核心逻辑的代码', depends_on=['step_1','step_2']),
            PlanStep('step_5', '验证测试：用例子验证正确性', '测试是确保代码正确的必要步骤', '通过所有测试用例', depends_on=['step_4'])]
        plan = Plan(plan_id=plan_id, title=f'解题计划：{question[:30]}...', description=f'针对{question}的{difficulty}难度解题计划', steps=steps, status=PlanStatus.PENDING)
        self.plans[plan_id] = plan
        return plan
    def approve_plan(self, plan_id):
        plan = self.plans.get(plan_id)
        if not plan: return False
        plan.status = PlanStatus.APPROVED
        return True
