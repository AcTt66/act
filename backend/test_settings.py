#!/usr/bin/env python3
"""
测试 /api/settings 接口
"""

import sys
import httpx

BACKEND_URL = "http://127.0.0.1:8000"

def test_settings():
    """测试 settings 接口"""
    print("=" * 60)
    print("测试 /api/settings 接口")
    print("=" * 60)
    
    try:
        url = f"{BACKEND_URL}/api/settings"
        print(f"请求: {url}")
        
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            print(f"状态码: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"响应数据:")
                for key, value in data.items():
                    print(f"  {key}: {value}")
                return data
            else:
                print(f"响应: {resp.text}")
                return None
                
    except Exception as e:
        print(f"失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("开始测试 settings 接口...")
    settings_data = test_settings()
    
    print("\n" + "=" * 60)
    if settings_data:
        print("✅ settings 接口测试成功!")
        print(f"   llm_enabled: {settings_data.get('llm_enabled')}")
        print(f"   api_key_configured: {settings_data.get('api_key_configured')}")
    else:
        print("❌ settings 接口测试失败")

if __name__ == "__main__":
    main()
