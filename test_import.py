import sys
print("=" * 60)
print("Module Import Test")
print("=" * 60)

modules_to_test = [
    'langchain_openai',
    'langchain_core.messages',
    'langgraph',
    'langgraph.graph',
    'langgraph.graph.message'
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"[OK] {module_name}")
    except ImportError as e:
        print(f"[FAIL] {module_name}: {e}")

print("\n" + "=" * 60)

print("\nTesting ai_agent import...")
try:
    from ai_agent import create_agent
    print("[OK] ai_agent imported successfully")
    
    print("\nCreating agent...")
    agent = create_agent()
    print("[OK] Agent created")
    
    print("\n" + "=" * 60)
    print("ALL IMPORTS SUCCESSFUL!")
    print("=" * 60)
    
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()
