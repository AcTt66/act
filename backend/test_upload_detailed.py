"""
文件上传诊断脚本 - 模拟实际文件上传过程
"""
import asyncio
import sys
import os

# 设置环境变量，避免代理问题
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

sys.path.insert(0, '.')

async def test_upload():
    print("="*60)
    print("File Upload Diagnostic Test")
    print("="*60)
    
    # 1. 检查配置
    print("\n[1] Configuration Check")
    from app.core.config import SETTINGS
    upload_cfg = SETTINGS.get("upload", {})
    print(f"    Storage dir: {upload_cfg.get('storage_dir')}")
    print(f"    Max file size: {upload_cfg.get('max_file_mb')} MB")
    print(f"    Allowed extensions: {upload_cfg.get('allowed_extensions')}")
    
    # 2. 检查VLM
    print("\n[2] VLM Service Check")
    from app.services.vlm_service import VLMService
    vlm = VLMService()
    print(f"    VLM Enabled: {vlm.enabled}")
    print(f"    Model: {vlm.model_name}")
    print(f"    Base URL: {vlm.base_url}")
    
    if not vlm.enabled:
        print("\n    [FAIL] VLM is not enabled!")
        print("    Please check your config.yaml for vlm.api_key, vlm.base_url, vlm.model_name")
        return False
    
    # 3. 检查存储目录
    print("\n[3] Storage Directory Check")
    from pathlib import Path
    storage_dir = Path(upload_cfg.get("storage_dir", "./data/uploads"))
    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
        test_file = storage_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        print(f"    [OK] Storage directory is writable: {storage_dir}")
    except Exception as e:
        print(f"    [FAIL] Cannot write to storage directory: {e}")
        return False
    
    # 4. 测试API连接
    print("\n[4] API Connection Test")
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{vlm.base_url}/models")
            print(f"    [OK] Can reach DMXAPI")
    except Exception as e:
        print(f"    [FAIL] Cannot reach DMXAPI: {e}")
        return False
    
    # 5. 模拟小文件上传测试
    print("\n[5] Simulated Upload Test")
    print("    Creating test image...")
    
    # 创建测试图像 (1x1 PNG)
    test_img_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x18, 0xDD,
        0x8D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
        0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82              # IEND chunk
    ])
    
    test_file = storage_dir / "test_image.png"
    test_file.write_bytes(test_img_bytes)
    print(f"    Test file created: {test_file}")
    
    # 测试文档处理
    print("\n[6] Document Processing Test")
    from app.services.document_processor import file_to_images, is_supported
    try:
        supported = is_supported(test_file)
        print(f"    File type supported: {supported}")
        
        images = file_to_images(test_file)
        print(f"    Converted to {len(images)} image(s)")
    except Exception as e:
        print(f"    [FAIL] Document processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 清理测试文件
    test_file.unlink()
    
    print("\n" + "="*60)
    print("All checks passed! File upload should work.")
    print("="*60)
    return True

if __name__ == "__main__":
    result = asyncio.run(test_upload())
    sys.exit(0 if result else 1)
