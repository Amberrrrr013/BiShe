import requests
import json
import sys
from pathlib import Path

log_file = Path("D:/_BiShe/demo_1/api_error.log")

print("=" * 60)
print("Testing Agent API with Detailed Logging")
print("=" * 60)

try:
    print("\n[1/3] Testing server health...")
    r = requests.get("http://127.0.0.1:5000", timeout=3)
    print(f"[OK] Server responding: {r.status_code}")
    
    print("\n[2/3] Sending request...")
    r = requests.post(
        "http://127.0.0.1:5000/api/agent/chat",
        json={
            "message": "你好",
            "history": []
        },
        timeout=30
    )
    
    print(f"[3/3] Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"\n[SUCCESS] API call successful!")
        print(f"  Success: {data.get('success')}")
        print(f"  Response: {data.get('response', '')[:200]}...")
    else:
        print(f"\n[ERROR] Server returned {r.status_code}")
        print(f"\nResponse content:")
        print(r.text)
        
        # Try to parse as JSON
        try:
            data = r.json()
            print(f"\nJSON response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(f"\nCould not parse as JSON")
        
        # Save error to log file
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Status: {r.status_code}\n")
            f.write(f"Headers: {dict(r.headers)}\n")
            f.write(f"\nResponse:\n{r.text}\n")
        
        print(f"\n[INFO] Error details saved to: {log_file}")
    
    print("\n" + "=" * 60)

except requests.exceptions.Timeout:
    print("\n[TIMEOUT] Request took too long")
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
