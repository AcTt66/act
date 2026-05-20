#!/usr/bin/env python3
"""测试 settings API"""

import httpx

def test_settings():
    print("=" * 60)
    print("Testing /api/settings API")
    print("=" * 60)
    
    # 尝试多个端口
    ports = [8012, 8000]
    
    for port in ports:
        url = f"http://127.0.0.1:{port}/api/settings"
        print(f"\nTrying: {url}")
        
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url)
                print(f"Status: {resp.status_code}")
                
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"Response:")
                    for key, value in data.items():
                        print(f"  {key}: {value}")
                    
                    llm_enabled = data.get("llm_enabled")
                    print(f"\nLLM Enabled: {llm_enabled}")
                    
                    if llm_enabled:
                        print("✅ Remote model is ENABLED!")
                        return True
                    else:
                        print("❌ Remote model is DISABLED!")
                        print("\nPossible issues:")
                        print("  - enable_llm is false in config.yaml")
                        print("  - api_key is empty in config.yaml")
                else:
                    print(f"Error: {resp.text[:200]}")
                    
        except Exception as e:
            print(f"Connection failed: {e}")
    
    print("\n" + "=" * 60)
    print("No working backend found!")
    print("Please start backend: python main.py")
    print("=" * 60)
    return False

if __name__ == "__main__":
    test_settings()
