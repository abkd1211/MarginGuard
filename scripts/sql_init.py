"""
Initialise (or re-initialise) marginguard.db from schema.sql.
Always run from any directory — paths are anchored to this file's location.
"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # MarginGuard/
DB_PATH   = ROOT / "marginguard.db"
SQL_PATH  = ROOT / "schema.sql"

# Wipe and recreate all tables
if DB_PATH.exists():
    DB_PATH.unlink()
    print(f"Removed existing database at: {DB_PATH}")
conn = sqlite3.connect(str(DB_PATH))
with open(SQL_PATH) as f:
    conn.executescript(f.read())
conn.commit()
conn.close()

print(f"Database initialised at: {DB_PATH}")

# Quick sanity check — list the tables that now exist
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
conn.close()
print("Tables:", tables)