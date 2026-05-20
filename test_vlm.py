import httpx, asyncio
from app.services.document_processor import encode_image_file
from pathlib import Path

p = Path(r'd:\BaiduNetdiskDownload\医路通Agent_Pro\data\uploads\images\4dbcc9a3890b479ea87e2a660722e577\4b12826a00344a69aaa4d1317eec4c80.jpg')
img = encode_image_file(p)

from app.core.config import SETTINGS
vlm = SETTINGS.get('vlm') or SETTINGS.get('llm') or {}
url = vlm.get('base_url', '') + '/chat/completions'
headers = {'Authorization': vlm.get('api_key', ''), 'Content-Type': 'application/json'}
payload = {
    'model': vlm.get('model_name', ''),
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'input_text', 'text': '解析这份医疗报告'},
            {'type': 'input_image', 'image_url': {'url': img.data_url}}
        ]
    }],
    'max_tokens': 100
}

async def test():
    async with httpx.AsyncClient(trust_env=False, timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        print('Status:', resp.status_code)
        print('Response:', resp.text[:800])

asyncio.run(test())
