import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

@dataclass
class Config:
    mimo_api_key: str = ''
    mimo_api_base: str = 'https://api.xiaomimimo.com/v1'
    mimo_model: str = 'MiMo-V2.5-Pro'
    debug: bool = False
    log_level: str = 'INFO'
    state_storage_dir: str = './data/states'
    max_turns: int = 20
    temperature: float = 0.7
    max_tokens: int = 4096
    def __post_init__(self):
        self.mimo_api_key = os.getenv('MIMO_API_KEY', self.mimo_api_key)
        self.mimo_api_base = os.getenv('MIMO_API_BASE', self.mimo_api_base)
        self.mimo_model = os.getenv('MIMO_MODEL', self.mimo_model)
    def validate(self):
        return bool(self.mimo_api_key and self.mimo_api_key != 'your_api_key_here')
    @classmethod
    def from_env(cls): return cls()
