import requests
import json

print("=" * 60)
print("Testing API with Error Capture")
print("=" * 60)

base_url = "http://127.0.0.1:5000"

try:
    print("\n[1/3] Testing server health...")
    response = requests.get(base_url, timeout=2)
    print(f"[OK] Server is running: {response.status_code}")
    
    print("\n[2/3] Testing agent/chat with error details...")
    response = requests.post(
        f"{base_url}/api/agent/chat",
        json={
            "message": "帮我制作一个关于气候变化的英语演讲视频",
            "history": [],
            "auto_execute": False
        },
        timeout=90
    )
    
    print(f"[RESULT] Status: {response.status_code}")
    print(f"[RESULT] Content-Type: {response.headers.get('Content-Type')}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n[SUCCESS]")
        print(f"  Success: {result.get('success')}")
        response_text = result.get('response', '')
        print(f"\n  AI Response (first 500 chars):")
        print(f"  {response_text[:500]}")
        
        execution_history = result.get('execution_history', [])
        print(f"\n  Execution history: {len(execution_history)} items")
        
        if execution_history:
            print(f"\n  Tools executed:")
            for i, item in enumerate(execution_history, 1):
                print(f"    {i}. {item['tool']}")
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
    else:
        print(f"\n[ERROR] Server returned {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        try:
            error_json = response.json()
            print(f"\nError response (JSON):")
            print(json.dumps(error_json, indent=2, ensure_ascii=False))
        except:
            print(f"\nRaw response:")
            print(response.text[:1000])
        
        print("\n" + "=" * 60)
        print("FAILED")
        print("=" * 60)
            
except requests.exceptions.Timeout:
    print("\n[TIMEOUT] Request took too long (>90s)")
    print("This might mean the agent is working but taking a long time.")
except requests.exceptions.ConnectionError as e:
    print(f"\n[CONNECTION ERROR] {e}")
    print("Server might have crashed or is not responding.")
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
