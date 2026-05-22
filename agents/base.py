from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

class AgentStatus(Enum):
    IDLE='idle'; RUNNING='running'; COMPLETED='completed'; ERROR='error'

@dataclass
class AgentContext:
    student_id: str
    question_history: List[Dict[str, Any]] = field(default_factory=list)
    understanding_level: int = 0
    weak_points: List[str] = field(default_factory=list)
    strong_points: List[str] = field(default_factory=list)
    current_topic: Optional[str] = None
    session_turns: int = 0
    def update_understanding(self, delta):
        self.understanding_level = max(0, min(10, self.understanding_level + delta))
    def add_history(self, role, content, metadata=None):
        self.question_history.append({'turn': self.session_turns, 'role': role, 'content': content, 'metadata': metadata or {}})
        self.session_turns += 1

@dataclass
class AgentResult:
    success: bool; data: Any; reasoning: str = ''
    next_agent: Optional[str] = None; status: AgentStatus = AgentStatus.COMPLETED

class BaseAgent(ABC):
    def __init__(self, name, description):
        self.name = name; self.description = description; self.status = AgentStatus.IDLE
    @abstractmethod
    async def execute(self, input_data, context): pass
    def get_system_prompt(self): return f'You are a {self.name}. {self.description}'
