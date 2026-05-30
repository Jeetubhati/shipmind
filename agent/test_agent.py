import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from coral_runner import check_connection, run_query
from queries import RELEASE_QUERIES

print("=== ShipMind Core Test ===\n")

print("1. Testing Coral connection...")
conn = check_connection()
if conn["connected"]:
    print(f"   OK. Sources: {conn['sources']}")
else:
    print(f"   FAILED: {conn['error']}")
    sys.exit(1)

print()
for key, q in RELEASE_QUERIES.items():
    print(f"2. Query [{key}]: {q['title']}")
    result = run_query(q["sql"])
    if result["error"]:
        print(f"   ERROR: {result['error']}")
    else:
        print(f"   OK: {result['row_count']} rows in {result['duration_ms']}ms")
        if result["columns"]:
            print(f"   Columns: {', '.join(result['columns'][:6])}")

print("\n=== Test complete ===")
