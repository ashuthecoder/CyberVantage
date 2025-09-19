import os, sys
from pathlib import Path

print("CWD:", Path.cwd())
print(".env exists?", Path(".env").exists())

# Try python-dotenv if available
try:
    from dotenv import load_dotenv, find_dotenv
    found = find_dotenv()
    print("find_dotenv() ->", found)
    load_dotenv()
except Exception as e:
    print("dotenv import/load failed:", e)

print("GOOGLE_API_KEY =", os.getenv("GOOGLE_API_KEY"))