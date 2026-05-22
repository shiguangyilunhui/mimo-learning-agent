import json
from typing import Optional
from pathlib import Path
from agents.base import AgentContext

class StudentStateManager:
    def __init__(self, storage_dir='./data/states'):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_state(self, student_id, context):
        try:
            data = {'student_id': context.student_id, 'understanding_level': context.understanding_level,
                    'weak_points': context.weak_points, 'strong_points': context.strong_points,
                    'current_topic': context.current_topic, 'session_turns': context.session_turns,
                    'question_history': context.question_history}
            safe_id = ''.join(c for c in student_id if c.isalnum() or c in '-_')
            with open(self.storage_dir / f'{safe_id}.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except: return False

    def load_state(self, student_id):
        try:
            safe_id = ''.join(c for c in student_id if c.isalnum() or c in '-_')
            path = self.storage_dir / f'{safe_id}.json'
            if not path.exists(): return None
            with open(path, 'r', encoding='utf-8') as f: data = json.load(f)
            return AgentContext(student_id=data['student_id'], understanding_level=data.get('understanding_level',0),
                weak_points=data.get('weak_points',[]), strong_points=data.get('strong_points',[]),
                current_topic=data.get('current_topic'), session_turns=data.get('session_turns',0),
                question_history=data.get('question_history',[]))
        except: return None
