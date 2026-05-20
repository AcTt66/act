#!/usr/bin/env python3
"""
测试 DMXAPI 是否能正常工作
"""

import sys
import json
import httpx

# 从配置文件读取
API_KEY = "sk-ayiIjGFk2Xf3hxKqEv7XADkAJeHITfOfCaDXq1DZAdS1ihLu"
BASE_URL = "https://www.dmxapi.cn/v1"

# 测试的模型列表
TEST_MODELS = [
    "qwen-plus",
    "qwen-turbo", 
    "gpt-4o-mini",
    "deepseek-chat",
    "glm-4-flash",
]

def test_chat_completion(model: str):
    """测试 chat completions 接口"""
    print("\n" + "="*60)
    print(f"测试模型: {model}")
    print("="*60)
    
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "你好，请回复'测试成功'"}],
        "temperature": 0.3,
        "max_tokens": 100,
    }
    
    try:
        print(f"发送请求到: {url}")
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            print(f"响应状态码: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                print(f"成功! AI 回复: {content}")
                return True
            else:
                print(f"失败! 响应内容:")
                print(resp.text)
                return False
    except Exception as e:
        print(f"异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("开始测试 DMXAPI...")
    print(f"API Key: {API_KEY[:10]}...")
    print(f"Base URL: {BASE_URL}")
    
    success_models = []
    
    for model in TEST_MODELS:
        if test_chat_completion(model):
            success_models.append(model)
            print(f"\n找到可用模型: {model}")
            print("这个模型可以正常工作!")
            break
    
    print("\n" + "="*60)
    print("测试总结:")
    if success_models:
        print(f"可用模型: {', '.join(success_models)}")
        print("\n建议在 config.yaml 中使用上面的模型!")
    else:
        print("所有模型都测试失败，请检查:")
        print("   1. API Key 是否正确")
        print("   2. 账户是否有余额")
        print("   3. 账户是否已升级为 VIP")
        print("   4. 网络连接是否正常")

if __name__ == "__main__":
    main()
