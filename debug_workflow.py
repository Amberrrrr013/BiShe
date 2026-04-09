import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Detailed Agent Workflow Debug")
print("=" * 60)

try:
    from ai_agent import create_agent, VideoGenerationConfig
    
    print("\n[1/4] Creating agent...")
    agent = create_agent()
    print("[OK] Agent created")
    
    print("\n[2/4] Initial state:")
    test_state = {
        "messages": [],
        "extracted_config": {},
        "is_complete": False,
        "skill_execution_log": []
    }
    print(f"State keys: {test_state.keys()}")
    
    print("\n[3/4] Testing graph streaming...")
    thread_id = "test-thread-123"
    
    from langchain_core.messages import HumanMessage
    
    initial_messages = [
        HumanMessage(content="帮我制作一个关于环保的英语演讲视频")
    ]
    
    from typing import Dict, Any, List
    from typing import Annotated, Sequence
    from dataclasses import dataclass, field
    from langgraph.graph.message import add_messages
    from langchain_core.messages import BaseMessage
    
    class AgentState(dict):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        extracted_config: Dict[str, Any] = field(default_factory=dict)
        is_complete: bool = False
        current_skill_result: Any = None
        conversation_turns: int = 0
        skill_execution_log: List[Dict[str, Any]] = field(default_factory=list)
    
    state = AgentState(
        messages=initial_messages,
        extracted_config={},
        is_complete=False,
        skill_execution_log=[]
    )
    
    print("\n[TEST] Invoking graph with single message...")
    print(f"Input state - messages: {len(state['messages'])}")
    print(f"Input message: {state['messages'][0].content[:50]}...")
    
    stream_count = 0
    for state_chunk in agent.graph.stream(
        state,
        config={"configurable": {"thread_id": thread_id}}
    ):
        stream_count += 1
        print(f"\n--- Stream Step {stream_count} ---")
        for node_name, node_state in state_chunk.items():
            print(f"Node: {node_name}")
            if "messages" in node_state:
                msgs = node_state["messages"]
                print(f"  Messages count: {len(msgs)}")
                if msgs:
                    last_msg = msgs[-1]
                    print(f"  Last message type: {type(last_msg).__name__}")
                    if hasattr(last_msg, 'content'):
                        content = last_msg.content
                        print(f"  Last message content: {content[:100]}...")
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        print(f"  Tool calls: {len(last_msg.tool_calls)}")
                        for tc in last_msg.tool_calls[:2]:
                            print(f"    - {tc.get('name')}: {tc.get('args')}")
    
    print(f"\n[RESULT] Total stream steps: {stream_count}")
    print(f"[RESULT] Execution history: {len(agent.execution_history)} items")
    
    if agent.execution_history:
        print("\n[EXECUTION LOG]:")
        for i, item in enumerate(agent.execution_history, 1):
            print(f"  {i}. {item['tool']} -> {str(item['result'])[:50]}...")
    
    print("\n" + "=" * 60)
    if stream_count > 1:
        print("SUCCESS! Graph executed multiple steps (tool calling working)")
    else:
        print("WARNING: Graph only executed 1 step (possible issue)")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
