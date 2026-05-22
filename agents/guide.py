from typing import Any, Dict
from .base import BaseAgent, AgentContext, AgentResult, AgentStatus

class SocraticGuideAgent(BaseAgent):
    def __init__(self):
        super().__init__('SocraticGuide', '通过苏格拉底式提问引导学生逐步思考')
    async def execute(self, input_data, context):
        question = input_data.get('question', '')
        analysis = input_data.get('analysis', {})
        if not question:
            return AgentResult(False, {}, '输入问题为空', status=AgentStatus.ERROR)
        strategy = '基础引导' if context.understanding_level < 3 else '进阶引导' if context.understanding_level < 7 else '挑战引导'
        kp = analysis.get('knowledge_points', [])
        if '二分查找' in str(kp):
            questions = ['你能描述一下二分查找的基本思想吗？','如果要在有序数组中查找一个数，你会如何缩小搜索范围？','每次比较后，我们可以排除掉多少数据？']
        elif '递归' in str(kp):
            questions = ['这个问题可以分解为更小的子问题吗？','递归的终止条件是什么？','每次递归调用，问题的规模如何变化？']
        else:
            questions = ['你能用自己的话描述一下这个问题吗？','解决这个问题需要哪些步骤？','如果给出一个简单的例子，你会如何手动解决它？']
        guidance = {'strategy': strategy, 'questions': questions, 'hints': ['试着从输入和输出的关系入手','考虑边界情况','画图或写例子可能有帮助']}
        context.add_history('guide', f'使用{strategy}策略', {'strategy': strategy})
        return AgentResult(True, guidance, f'采用{strategy}策略', next_agent='AdaptiveTutor')
