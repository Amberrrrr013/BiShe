import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Direct Agent Test - Same as Flask would do")
print("=" * 60)

try:
    from ai_agent import create_agent
    from langchain_core.messages import HumanMessage
    
    print("\n[1/4] Creating agent...")
    agent = create_agent()
    print("[OK] Agent created")
    
    print("\n[2/4] Testing chat method...")
    result = agent.chat("帮我制作一个关于气候变化的英语演讲视频", [])
    
    print(f"\n[3/4] Result analysis:")
    print(f"  Success: {result.get('success')}")
    print(f"  Error: {result.get('error')}")
    
    if result.get('success'):
        messages = result.get('messages', [])
        print(f"  Messages count: {len(messages)}")
        
        if messages:
            last_msg = messages[-1]
            print(f"  Last message type: {type(last_msg).__name__}")
            if hasattr(last_msg, 'content'):
                print(f"  Content preview: {last_msg.content[:200]}...")
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                print(f"  Tool calls: {len(last_msg.tool_calls)}")
                for tc in last_msg.tool_calls:
                    print(f"    - {tc.get('name')}: {tc.get('args')}")
        
        execution_history = result.get('execution_history', [])
        print(f"  Execution history: {len(execution_history)} items")
        
        config = result.get('config', {})
        print(f"  Config: {config}")
        
        print("\n" + "=" * 60)
        if len(execution_history) > 0:
            print("SUCCESS! Agent executed tools!")
            print("=" * 60)
            print("\nExecution details:")
            for i, item in enumerate(execution_history, 1):
                print(f"{i}. Tool: {item['tool']}")
                result_str = str(item['result'])[:100]
                print(f"   Result: {result_str}...")
        else:
            print("Agent completed but no tools were executed")
            print("(This might be OK if LLM decided to respond without tools)")
            print("=" * 60)
    else:
        print(f"\n[ERROR] Agent failed: {result.get('error')}")
        if 'traceback' in result:
            print("\nTraceback:")
            print(result['traceback'])

except Exception as e:
    print(f"\n[CRITICAL ERROR] {e}")
    import traceback
    traceback.print_exc()
