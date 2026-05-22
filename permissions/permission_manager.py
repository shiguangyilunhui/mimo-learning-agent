from dataclasses import dataclass
from typing import Optional
from enum import Enum

class PermissionLevel(Enum):
    ALLOW='allow'; DENY='deny'; ASK='ask'; HINT='hint'

class ActionType(Enum):
    GIVE_CODE='give_code'; GIVE_PSEUDOCODE='give_pseudocode'; GIVE_HINT='give_hint'
    GIVE_ANSWER='give_answer'; ANALYZE='analyze'; GUIDE='guide'
    EXPLAIN_CONCEPT='explain_concept'; PROVIDE_EXAMPLE='provide_example'; CHECK_SOLUTION='check_solution'

@dataclass
class PermissionRule:
    action: ActionType; level: PermissionLevel; condition: Optional[str] = None; reason: str = ''

class PermissionManager:
    DEFAULT_RULES = [
        PermissionRule(ActionType.GIVE_CODE, PermissionLevel.DENY, reason='不直接给出完整代码'),
        PermissionRule(ActionType.GIVE_ANSWER, PermissionLevel.DENY, reason='不直接给出答案'),
        PermissionRule(ActionType.GIVE_PSEUDOCODE, PermissionLevel.HINT, reason='可以给出伪代码框架'),
        PermissionRule(ActionType.GIVE_HINT, PermissionLevel.ALLOW, reason='提示是引导思考的重要手段'),
        PermissionRule(ActionType.ANALYZE, PermissionLevel.ALLOW, reason='分析能力需要培养'),
        PermissionRule(ActionType.GUIDE, PermissionLevel.ALLOW, reason='引导是核心教学方式'),
        PermissionRule(ActionType.EXPLAIN_CONCEPT, PermissionLevel.ALLOW, reason='概念解释是学习的基础'),
        PermissionRule(ActionType.CHECK_SOLUTION, PermissionLevel.ALLOW, reason='检查解法有助于纠正错误')]
    def __init__(self, custom_rules=None):
        self.rules = {r.action: r for r in self.DEFAULT_RULES}
        if custom_rules:
            for r in custom_rules: self.rules[r.action] = r
    def check_permission(self, action, context=None):
        rule = self.rules.get(action)
        if not rule: return {'allowed': True, 'level': PermissionLevel.ALLOW}
        allowed = rule.level in (PermissionLevel.ALLOW, PermissionLevel.HINT)
        return {'allowed': allowed, 'level': rule.level, 'reason': rule.reason, 'hint_only': rule.level == PermissionLevel.HINT}
    def get_hint_level(self, understanding_level):
        if understanding_level >= 7: return 1
        elif understanding_level >= 4: return 2
        else: return 3
