import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from server import app
    print("[OK] server.py import success")
    print("[OK] Flask app created")
    agent_routes = [rule.rule for rule in app.url_map.iter_rules() if 'agent' in rule.rule]
    print(f"[OK] Agent routes available: {agent_routes}")
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    import traceback
    traceback.print_exc()
