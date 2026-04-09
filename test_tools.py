import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Testing Tool Bindings")
print("=" * 60)

try:
    print("\n[1/3] Importing necessary modules...")
    from ai_agent import get_llm, get_all_tools, create_agent
    from langchain_core.messages import HumanMessage
    
    print("[OK] All imports successful")
    
    print("\n[2/3] Checking tools...")
    tools = get_all_tools()
    print(f"[INFO] Number of tools: {len(tools)}")
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool.name}: {tool.description[:50]}...")
    
    print("\n[3/3] Testing LLM with tools...")
    llm = get_llm("glm")
    
    print(f"[INFO] LLM model: {llm.model_name}")
    print(f"[INFO] LLM has tools: {hasattr(llm, 'tool_choice')}")
    
    # Test if tools are properly bound
    messages = [
        HumanMessage(content="帮我制作一个关于环保的英语演讲视频。请调用generate_english_speech工具生成演讲稿。")
    ]
    
    print("\n[TEST] Sending message to LLM...")
    response = llm.invoke(messages)
    
    print(f"[RESULT] Response type: {type(response).__name__}")
    print(f"[RESULT] Has tool_calls: {hasattr(response, 'tool_calls')}")
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"[SUCCESS] Tool calls found: {len(response.tool_calls)}")
        for tc in response.tool_calls:
            print(f"  - Tool: {tc.get('name')}")
            print(f"    Args: {tc.get('args')}")
    else:
        print(f"[INFO] No tool calls. Response content:")
        print(response.content[:500])
    
    print("\n[4/3] Testing complete agent workflow...")
    agent = create_agent()
    result = agent.chat("帮我制作一个关于环保的英语演讲视频", [])
    
    if result.get('success'):
        messages = result.get('messages', [])
        tool_call_count = 0
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_call_count += len(msg.tool_calls)
        
        print(f"[RESULT] Total tool calls in conversation: {tool_call_count}")
        print(f"[RESULT] Execution history: {len(result.get('execution_history', []))} items")
        
        if tool_call_count > 0:
            print("\n" + "=" * 60)
            print("SUCCESS! Agent is calling tools!")
            print("=" * 60)
        else:
            print("\n[WARNING] Agent is not calling tools yet.")
            print("Check if the system prompt is properly instructing the LLM to use tools.")
    else:
        print(f"[ERROR] Agent failed: {result.get('error')}")

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
