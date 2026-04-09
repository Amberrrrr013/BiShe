import requests
import json

print("=" * 60)
print("Testing Flask API Endpoint")
print("=" * 60)

base_url = "http://127.0.0.1:5000"

try:
    print("\n[1/3] Testing server health...")
    response = requests.get(base_url, timeout=2)
    print(f"[OK] Server responded: {response.status_code}")
    
    print("\n[2/3] Testing agent/chat endpoint...")
    response = requests.post(
        f"{base_url}/api/agent/chat",
        json={
            "message": "帮我制作一个关于环保的英语演讲视频",
            "history": [],
            "auto_execute": False
        },
        timeout=30
    )
    
    print(f"[RESULT] Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"[SUCCESS] API call successful")
        print(f"  - Success: {result.get('success')}")
        print(f"  - Response: {result.get('response', '')[:200]}...")
        print(f"  - Config: {result.get('config')}")
        print(f"  - Execution history: {len(result.get('execution_history', []))} items")
    else:
        print(f"[ERROR] API call failed")
        print(f"  Response: {response.text[:500]}")
    
    print("\n" + "=" * 60)
    print("API TEST COMPLETE")
    print("=" * 60)

except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to server. Is it running?")
    print("Start server with: python server.py")
except requests.exceptions.Timeout:
    print("[ERROR] Request timeout. Server might be busy or stuck.")
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
