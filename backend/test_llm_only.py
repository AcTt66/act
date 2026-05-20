#!/usr/bin/env python3
"""
只测试LLM客户端
"""

import sys
import json
import asyncio
from app.services.llm_client import LLMClient

def test_llm_client():
    """测试LLM客户端"""
    print("="*60)
    print("测试: LLM客户端")
    print("="*60)
    
    try:
        client = LLMClient()
        print(f"LLM enabled: {client.enabled}")
        print(f"API type: {client.api_type}")
        print(f"Model: {client.config['model_name']}")
        
        # 测试简单的chat
        print("\n发送测试消息...")
        result = asyncio.run(client.chat(
            [{"role": "user", "content": "你好，请回复'LLM测试成功'"}],
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
    print("开始测试LLM客户端...")
    success = test_llm_client()
    
    print("\n" + "="*60)
    if success:
        print("LLM客户端测试成功!")
        print("\n现在可以在浏览器中使用了!")
    else:
        print("LLM客户端测试失败")

if __name__ == "__main__":
    main()
