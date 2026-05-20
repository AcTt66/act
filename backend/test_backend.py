#!/usr/bin/env python3
"""
测试我们自己的后端API是否能正常工作
"""

import sys
import json
import httpx

BACKEND_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("="*60)
    print("测试 1: 健康检查")
    print("="*60)
    try:
        url = f"{BACKEND_URL}/"
        print(f"请求: {url}")
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            print(f"状态码: {resp.status_code}")
            if resp.status_code == 200:
                print("成功! 后端服务正常运行")
                return True
            else:
                print(f"响应: {resp.text}")
                return False
    except Exception as e:
        print(f"失败: {e}")
        return False

def test_config():
    """检查配置是否加载"""
    print("\n" + "="*60)
    print("测试 2: 检查配置")
    print("="*60)
    
    try:
        from app.core.config import SETTINGS
        print("LLM 配置:")
        print(f"  - API Key: {SETTINGS['llm']['api_key'][:10]}...")
        print(f"  - Base URL: {SETTINGS['llm']['base_url']}")
        print(f"  - Model: {SETTINGS['llm']['model_name']}")
        print(f"  - Enabled: {SETTINGS['features']['enable_llm']}")
        return True
    except Exception as e:
        print(f"无法加载配置: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_client():
    """测试LLM客户端"""
    print("\n" + "="*60)
    print("测试 3: 测试LLM客户端")
    print("="*60)
    
    try:
        import asyncio
        from app.services.llm_client import LLMClient
        
        client = LLMClient()
        print(f"LLM enabled: {client.enabled}")
        print(f"API type: {client.api_type}")
        
        # 测试简单的chat
        print("\n发送测试消息...")
        result = asyncio.run(client.chat(
            [{"role": "user", "content": "你好，请回复'后端测试成功'"}],
            timeout=30.0
        ))
        print(f"成功! 回复: {result}")
        return True
        
    except Exception as e:
        print(f"失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("开始测试后端...")
    print(f"后端地址: {BACKEND_URL}")
    
    results = []
    results.append(("健康检查", test_health()))
    results.append(("配置加载", test_config()))
    
    # 只在健康检查通过时才测试LLM
    if results[0][1]:
        results.append(("LLM客户端", test_llm_client()))
    
    print("\n" + "="*60)
    print("测试总结:")
    print("="*60)
    for name, success in results:
        status = "成功" if success else "失败"
        print(f"  {name}: {status}")
    
    all_success = all(r[1] for r in results)
    if all_success:
        print("\n所有测试通过! 后端配置正确!")
        print("\n现在可以在浏览器中使用了!")
    else:
        print("\n部分测试失败，请检查上面的错误信息")

if __name__ == "__main__":
    main()
