import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx, asyncio, base64
from pathlib import Path

# 手动编码图片
def encode_image(path):
    import cv2, numpy as np
    arr = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    scale = min(1.0, 1280 / float(max(w, h)))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LANCZOS4)
    ok, buf = cv2.imencode(".png", img)
    b64 = base64.b64encode(buf).decode("ascii")
    return f"data:image/png;base64,{b64}"

p = Path(r'd:\BaiduNetdiskDownload\医路通Agent_Pro\data\uploads\images\4dbcc9a3890b479ea87e2a660722e577\4b12826a00344a69aaa4d1317eec4c80.jpg')
data_url = encode_image(p)

from app.core.config import SETTINGS
vlm = SETTINGS.get('vlm') or SETTINGS.get('llm') or {}
url = vlm.get('base_url', '') + '/chat/completions'
headers = {'Authorization': vlm.get('api_key', ''), 'Content-Type': 'application/json'}

# 测试两种格式
for fmt_name, content in [
    ('input_image', [
        {'type': 'input_text', 'text': '解析这份医疗报告'},
        {'type': 'input_image', 'image_url': {'url': data_url}}
    ]),
    ('image_url', [
        {'type': 'text', 'text': '解析这份医疗报告'},
        {'type': 'image_url', 'image_url': {'url': data_url}}
    ])
]:
    payload = {
        'model': vlm.get('model_name', ''),
        'messages': [{'role': 'user', 'content': content}],
        'max_tokens': 100
    }
    
    async def test(fmt):
        async with httpx.AsyncClient(trust_env=False, timeout=60) as client:
            resp = await client.post(url, headers=headers, json=payload)
            print(f'[{fmt}] Status:', resp.status_code)
            print(f'[{fmt}] Response:', resp.text[:500])
            print()
    
    asyncio.run(test(fmt_name))
