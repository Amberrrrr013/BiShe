import requests
import sys

print("=" * 60)
print("Quick Server Health Check")
print("=" * 60)

try:
    response = requests.get("http://127.0.0.1:5000", timeout=3)
    print(f"Server is running! Status: {response.status_code}")
    print(f"Response preview: {response.text[:200]}")
    
    print("\n" + "=" * 60)
    print("Server is ready at http://localhost:5000")
    print("=" * 60)
    
except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to server")
    print("Server might not be running or is not accessible")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
