import os, time
from typing import Any, Dict, List, Optional
import aiohttp
from dotenv import load_dotenv
load_dotenv()

class MiMoClient:
    def __init__(self, api_key=None, base_url=None, model='MiMo-V2.5-Pro'):
        self.api_key = api_key or os.getenv('MIMO_API_KEY')
        self.base_url = base_url or os.getenv('MIMO_API_BASE', 'https://api.xiaomimimo.com/v1')
        self.model = model or os.getenv('MIMO_MODEL', 'MiMo-V2.5-Pro')
        self.session = None
        self.total_tokens_used = 0
        self.request_count = 0

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'})
        return self

    async def __aexit__(self, *args):
        if self.session: await self.session.close()

    async def chat_completion(self, messages, temperature=0.7, max_tokens=None, tools=None, retry_count=3):
        payload = {'model': self.model, 'messages': messages, 'temperature': temperature}
        if max_tokens: payload['max_tokens'] = max_tokens
        if tools: payload['tools'] = tools
        for attempt in range(retry_count):
            try:
                if not self.session: raise RuntimeError('Session not initialized')
                async with self.session.post(f'{self.base_url}/chat/completions', json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.total_tokens_used += result.get('usage', {}).get('total_tokens', 0)
                        self.request_count += 1
                        return result
                    elif resp.status == 429: time.sleep(2 ** attempt)
                    else: raise Exception(f'API error {resp.status}')
            except Exception as e:
                if attempt == retry_count - 1: raise
                time.sleep(1)
        return {}

    def get_usage_stats(self):
        return {'total_tokens_used': self.total_tokens_used, 'request_count': self.request_count, 'model': self.model}
