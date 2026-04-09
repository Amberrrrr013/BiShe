import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Testing AI Agent Module Import")
print("=" * 60)

try:
    print("\n[1/5] Importing ai_agent module...")
    from ai_agent import create_agent, FullAutoAgent
    print("[OK] ai_agent module imported successfully")
    
    print("\n[2/5] Creating agent instance...")
    agent = create_agent()
    print("[OK] Agent instance created")
    
    print("\n[3/5] Testing agent.chat() method...")
    result = agent.chat("帮我制作一个关于环保的英语演讲视频", [])
    
    print(f"\n[RESULT] Success: {result.get('success')}")
    print(f"[RESULT] Error: {result.get('error')}")
    
    if result.get('success'):
        messages = result.get('messages', [])
        if messages:
            last_msg = messages[-1]
            print(f"[RESULT] Last message type: {type(last_msg).__name__}")
            if hasattr(last_msg, 'content'):
                print(f"[RESULT] Last message content: {last_msg.content[:200]}")
            if hasattr(last_msg, 'tool_calls'):
                print(f"[RESULT] Tool calls: {last_msg.tool_calls}")
        
        config = result.get('config', {})
        print(f"[RESULT] Config: {config}")
        
        execution_history = result.get('execution_history', [])
        print(f"[RESULT] Execution history count: {len(execution_history)}")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
    else:
        print(f"\n[ERROR] Agent execution failed: {result.get('error')}")
        import traceback
        if 'traceback' in result:
            print("\n[TRACEBACK]:")
            print(result['traceback'])
        
except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("TEST FAILED!")
    print("=" * 60)
