import subprocess
import time
import requests
import sys

print("=" * 60)
print("Starting Flask Server and Testing API")
print("=" * 60)

print("\n[1/4] Starting Flask server in background...")
server_process = subprocess.Popen(
    [sys.executable, "server.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd="D:\_BiShe\demo_1"
)

print("[INFO] Waiting for server to start...")
time.sleep(5)

try:
    print("\n[2/4] Testing server health...")
    try:
        response = requests.get("http://127.0.0.1:5000", timeout=2)
        print(f"[OK] Server responded: {response.status_code}")
    except:
        print("[WARNING] Server might still be starting...")
        time.sleep(3)
    
    print("\n[3/4] Testing /api/agent/chat endpoint...")
    try:
        response = requests.post(
            "http://127.0.0.1:5000/api/agent/chat",
            json={
                "message": "帮我制作一个关于环保的英语演讲视频",
                "history": [],
                "auto_execute": False
            },
            timeout=60
        )
        
        print(f"[RESULT] Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[SUCCESS] API call successful!")
            print(f"  - Success: {result.get('success')}")
            response_text = result.get('response', '')
            print(f"  - Response preview:")
            print(f"    {response_text[:300]}...")
            print(f"\n  - Config: {result.get('config')}")
            print(f"  - Execution history: {len(result.get('execution_history', []))} items")
            
            if result.get('execution_history'):
                print(f"\n[EXECUTION LOG]:")
                for i, item in enumerate(result.get('execution_history'), 1):
                    print(f"  {i}. Tool: {item['tool']}")
                    result_text = str(item['result'])[:50]
                    print(f"     Result: {result_text}...")
        else:
            print(f"[ERROR] API call failed")
            print(f"  Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("[ERROR] Request timeout after 60 seconds")
        print("[INFO] The agent might be stuck in an infinite loop or waiting for API")
    except Exception as e:
        print(f"[ERROR] API call failed: {e}")
    
    print("\n[4/4] Stopping server...")
    server_process.terminate()
    server_process.wait(timeout=5)
    print("[OK] Server stopped")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

except KeyboardInterrupt:
    print("\n[INFO] Interrupted by user")
    server_process.terminate()
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
    server_process.terminate()
