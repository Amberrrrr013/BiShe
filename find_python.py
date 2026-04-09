import sys

print("Python Environment Info")
print("=" * 60)
print(f"Current Python: {sys.executable}")
print(f"Version: {sys.version}")

# Check key packages
packages = [
    'langchain_openai',
    'langchain_core',
    'langgraph',
    'flask',
    'werkzeug'
]

print("\nChecking packages:")
for pkg in packages:
    try:
        mod = __import__(pkg)
        loc = getattr(mod, '__file__', 'built-in')
        print(f"  [OK] {pkg}: {loc}")
    except ImportError:
        print(f"  [MISSING] {pkg}")

print("\n" + "=" * 60)
