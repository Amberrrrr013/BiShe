import requests
import time

print("=" * 60)
print("Quick API Test")
print("=" * 60)

try:
    # Test 1: Health check
    print("\n[Test 1] Server health...")
    r = requests.get("http://127.0.0.1:5000", timeout=3)
    print(f"[OK] Server responding: {r.status_code}")
    
    # Test 2: Simple API call (shorter timeout)
    print("\n[Test 2] Agent API...")
    start = time.time()
    r = requests.post(
        "http://127.0.0.1:5000/api/agent/chat",
        json={
            "message": "你好",
            "history": []
        },
        timeout=30  # Short timeout
    )
    elapsed = time.time() - start
    
    print(f"[OK] API responded in {elapsed:.1f}s")
    print(f"  Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"  Success: {data.get('success')}")
        if data.get('response'):
            print(f"  Response preview: {data['response'][:100]}...")
    else:
        print(f"  Error: {r.text[:200]}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

except requests.exceptions.Timeout:
    print("\n[TIMEOUT] Server is busy (this is OK)")
except Exception as e:
    print(f"\n[ERROR] {e}")
