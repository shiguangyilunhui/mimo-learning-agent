from typing import Any, Dict, List
from .base import BaseAgent, AgentContext, AgentResult, AgentStatus

class ExamAnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__('ExamAnalyzer', '分析编程题目，提取核心知识点和考察范围')
    async def execute(self, input_data, context):
        question = input_data.get('question', '')
        if not question:
            return AgentResult(False, {}, '输入问题为空', status=AgentStatus.ERROR)
        analysis = {
            'knowledge_points': [k for k in ['算法','数据结构','递归','动态规划','二分查找'] if k in question] or ['待分析'],
            'difficulty': 'medium' if len(question) > 100 else 'easy',
            'related_concepts': ['时间复杂度', '空间复杂度'],
            'question_type': 'implementation' if '实现' in question else 'conceptual'
        }
        context.current_topic = analysis['knowledge_points'][0]
        return AgentResult(True, analysis, '分析完成', next_agent='SocraticGuide')
