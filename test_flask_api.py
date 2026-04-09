import requests
import json

print("=" * 60)
print("Testing Flask API Endpoint")
print("=" * 60)

base_url = "http://127.0.0.1:5000"

try:
    print("\n[1/5] Testing server health...")
    try:
        response = requests.get(base_url, timeout=5)
        print(f"[OK] Server responded: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to server. Is it running?")
        print("Please start server first: python server.py")
        exit(1)
    
    print("\n[2/5] Testing agent/chat endpoint...")
    try:
        response = requests.post(
            f"{base_url}/api/agent/chat",
            json={
                "message": "帮我制作一个关于气候变化的英语演讲视频",
                "history": [],
                "auto_execute": False
            },
            timeout=60
        )
        
        print(f"[RESULT] Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[SUCCESS] API call successful!")
            print(f"  Success: {result.get('success')}")
            
            if result.get('success'):
                response_text = result.get('response', '')
                print(f"\n  AI Response preview:")
                print(f"    {response_text[:400]}...")
                
                config = result.get('config', {})
                print(f"\n  Config: {config}")
                
                execution_history = result.get('execution_history', [])
                print(f"\n  Execution history: {len(execution_history)} items")
                
                if execution_history:
                    print(f"\n  Tool executions:")
                    for i, item in enumerate(execution_history, 1):
                        print(f"    {i}. {item['tool']}")
                
                print("\n" + "=" * 60)
                print("FULL SUCCESS! Agent is working!")
                print("=" * 60)
            else:
                print(f"\n[ERROR] API returned success=False")
                print(f"  Error: {result.get('error')}")
                if 'traceback' in result:
                    print(f"\n  Traceback:")
                    print(result['traceback'])
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("[ERROR] Request timeout after 60 seconds")
        print("[INFO] Agent might be stuck or taking too long")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        import traceback
        traceback.print_exc()

except KeyboardInterrupt:
    print("\n[INFO] Interrupted")
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
