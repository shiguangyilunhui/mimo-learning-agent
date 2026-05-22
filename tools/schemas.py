from dataclasses import dataclass, field
from typing import Any, List, Optional
from enum import Enum

class ParameterType(Enum):
    STRING='string'; INTEGER='integer'; NUMBER='number'; BOOLEAN='boolean'; ARRAY='array'; OBJECT='object'

@dataclass
class ToolParameter:
    name: str; type: ParameterType; description: str; required: bool = True; default: Any = None; enum: Optional[List[str]] = None

@dataclass
class ToolSchema:
    name: str; description: str; parameters: List[ToolParameter] = field(default_factory=list); returns: Optional[str] = None
    def to_dict(self):
        properties, required = {}, []
        for p in self.parameters:
            prop = {'type': p.type.value, 'description': p.description}
            if p.enum: prop['enum'] = p.enum
            properties[p.name] = prop
            if p.required: required.append(p.name)
        return {'type': 'function', 'function': {'name': self.name, 'description': self.description,
            'parameters': {'type': 'object', 'properties': properties, 'required': required}}}

ANALYZE_QUESTION_SCHEMA = ToolSchema('analyze_question', '分析编程题目，提取核心知识点',
    [ToolParameter('question', ParameterType.STRING, '题目描述'), ToolParameter('language', ParameterType.STRING, '编程语言', required=False)])

GUIDE_THINKING_SCHEMA = ToolSchema('guide_thinking', '生成苏格拉底式引导问题',
    [ToolParameter('question', ParameterType.STRING, '当前问题'), ToolParameter('knowledge_points', ParameterType.ARRAY, '已识别的知识点'),
     ToolParameter('understanding_level', ParameterType.INTEGER, '学生当前理解程度 (0-10)')])

ASSESS_RESPONSE_SCHEMA = ToolSchema('assess_response', '评估学生回答质量',
    [ToolParameter('response', ParameterType.STRING, '学生回答'), ToolParameter('expected_concepts', ParameterType.ARRAY, '预期涉及的概念')])
