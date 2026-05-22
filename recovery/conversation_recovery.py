import json, zlib, time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path

@dataclass
class ConversationSnapshot:
    snapshot_id: str; student_id: str; timestamp: float
    conversation_history: List[Dict]; student_context: Dict
    plan_state: Optional[Dict] = None; permission_state: Optional[Dict] = None
    metadata: Dict = field(default_factory=dict)
    def to_json(self): return json.dumps(asdict(self), ensure_ascii=False, indent=2)
    @classmethod
    def from_dict(cls, data): return cls(**data)

class ConversationRecovery:
    def __init__(self, storage_dir='./data/snapshots'):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    def create_snapshot(self, snapshot_id, student_id, history, context, plan_state=None, permission_state=None):
        return ConversationSnapshot(snapshot_id=snapshot_id, student_id=student_id, timestamp=time.time(),
            conversation_history=history, student_context=context, plan_state=plan_state, permission_state=permission_state)
    def save_snapshot(self, snapshot, compress=True):
        try:
            data = snapshot.to_json()
            safe_id = ''.join(c for c in snapshot.snapshot_id if c.isalnum() or c in '-_')
            path = self.storage_dir / f'{safe_id}.json'
            if compress:
                path = path.with_suffix('.json.z')
                with open(path, 'wb') as f: f.write(zlib.compress(data.encode('utf-8')))
            else:
                with open(path, 'w', encoding='utf-8') as f: f.write(data)
            return True
        except: return False
    def load_snapshot(self, snapshot_id):
        try:
            safe_id = ''.join(c for c in snapshot_id if c.isalnum() or c in '-_')
            compressed = self.storage_dir / f'{safe_id}.json.z'
            if compressed.exists():
                with open(compressed, 'rb') as f: data = zlib.decompress(f.read()).decode('utf-8')
            else:
                plain = self.storage_dir / f'{safe_id}.json'
                if not plain.exists(): return None
                with open(plain, 'r', encoding='utf-8') as f: data = f.read()
            return ConversationSnapshot.from_dict(json.loads(data))
        except: return None
    def compress_context(self, history, max_turns=50, strategy='sliding_window'):
        if len(history) <= max_turns: return history
        return history[-max_turns:]
