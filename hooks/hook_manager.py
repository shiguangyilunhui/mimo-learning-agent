import asyncio
from dataclasses import dataclass, field
from typing import Callable, Dict, List
from enum import Enum

class HookType(Enum):
    PRE_PROCESS='pre_process'; PRE_AGENT='pre_agent'; POST_AGENT='post_agent'
    PRE_RESPONSE='pre_response'; POST_RESPONSE='post_response'; ON_ERROR='on_error'; ON_COMPLETE='on_complete'

@dataclass
class Hook:
    name: str; hook_type: HookType; handler: Callable; priority: int = 0; enabled: bool = True

class HookManager:
    def __init__(self): self.hooks: Dict[HookType, List[Hook]] = {t: [] for t in HookType}
    def register(self, hook):
        self.hooks[hook.hook_type].append(hook)
        self.hooks[hook.hook_type].sort(key=lambda h: h.priority)
    async def execute_hooks(self, hook_type, data, context=None):
        result = data.copy()
        for hook in self.hooks.get(hook_type, []):
            if not hook.enabled: continue
            try:
                r = await hook.handler(result, context) if asyncio.iscoroutinefunction(hook.handler) else hook.handler(result, context)
                if r is not None: result = r
            except: pass
        return result

def create_content_filter_hook():
    def fn(data, context):
        content = data.get('content', '')
        if chr(96)*3 in content and 'def ' in content:
            data['content'] = chr(65288) + '系统：检测到完整代码，已过滤。请尝试自己实现。' + chr(65289)
            data['filtered'] = True
        return data
    return Hook('content_filter', HookType.POST_AGENT, fn, 10)

def create_difficulty_adjuster_hook():
    def fn(data, context):
        if not context: return data
        level = context.get('understanding_level', 5)
        content = data.get('content', '')
        if level < 3:
            content = content.replace('时间复杂度', '运行时间').replace('空间复杂度', '内存使用')
        data['content'] = content
        return data
    return Hook('difficulty_adjuster', HookType.PRE_RESPONSE, fn, 5)

def create_learning_tracker_hook():
    return Hook('learning_tracker', HookType.POST_RESPONSE, lambda d, c: d, 100)
