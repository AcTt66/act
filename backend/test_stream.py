#!/usr/bin/env python3
"""
测试LLM的流式输出
"""

import sys
import asyncio
from app.services.llm_client import LLMClient

async def test_chat_stream():
    """测试流式输出"""
    print("="*60)
    print("测试: LLM流式输出")
    print("="*60)
    
    try:
        client = LLMClient()
        print(f"LLM enabled: {client.enabled}")
        print(f"API type: {client.api_type}")
        print(f"Model: {client.config['model_name']}")
        
        # 测试流式chat
        print("\n开始流式输出...")
        full_text = []
        async for delta in client.chat_stream(
            [{"role": "user", "content": "你好，请回复'流式测试成功'"}],
            timeout=30.0,
            max_tokens=100,
            temperature=0.3
        ):
            print(delta, end="", flush=True)
            full_text.append(delta)
        
        print("\n\n流式输出完成!")
        print(f"完整内容: {''.join(full_text)}")
        return True
        
    except Exception as e:
        print(f"\n失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("开始测试LLM流式输出...")
    success = asyncio.run(test_chat_stream())
    
    print("\n" + "="*60)
    if success:
        print("流式输出测试成功!")
        print("\n现在可以在浏览器中使用了!")
    else:
        print("流式输出测试失败")

if __name__ == "__main__":
    main()
