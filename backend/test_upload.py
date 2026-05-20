"""
测试文件上传功能
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.core.auth import create_access_token, decode_access_token
from app.core.database import get_user_by_id

# 获取一个测试用户 - 尝试常见用户名
users = None
for uid in ["test_user", "admin", "user", "demo"]:
    u = get_user_by_id(uid)
    if u:
        users = u
        break

if not users:
    print("[FAIL] No test user found in database")
    print("Please register a user first via the web interface")
    sys.exit(1)

# 创建token
token = create_access_token(users)
print(f"Token created: {token[:50]}...")

# 解码验证
payload = decode_access_token(token)
print(f"Token valid: {payload}")

# 测试VLM
from app.services.vlm_service import VLMService
vlm = VLMService()
print(f"VLM Enabled: {vlm.enabled}")
print(f"VLM Model: {vlm.model_name}")

# 测试上传配置
from app.core.config import SETTINGS
upload_cfg = SETTINGS.get("upload", {})
print(f"Upload config: {upload_cfg}")

# 检查存储目录
from pathlib import Path
storage_dir = Path(upload_cfg.get("storage_dir", "./data/uploads"))
print(f"Storage dir exists: {storage_dir.exists()}")
storage_dir.mkdir(parents=True, exist_ok=True)
print(f"Storage dir ready: {storage_dir}")
