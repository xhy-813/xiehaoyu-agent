"""临时脚本：检查 olist.db 存在性及各表行数，验证 gold SQL。"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
db = ROOT / "chatbi" / "data" / "olist.db"

if not db.exists():
    print("DB NOT FOUND:", db)
    sys.exit(1)

print(f"DB exists  size={db.stat().st_size // 1024} KB")

conn = sqlite3.connect(str(db))
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])
for (name,) in tables:
    cnt = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"  {name}: {cnt} rows")

# ── 验证所有 gold SQL 可执行 ──
sys.path.insert(0, str(ROOT))
from tests.eval_text2sql import EVAL_CASES

print(f"\n验证 {len(EVAL_CASES)} 条 gold SQL ...")
errors = []
for case in EVAL_CASES:
    try:
        conn.execute(case["gold_sql"]).fetchone()
    except Exception as e:
        errors.append(f"  {case['id']}: {e}")

if errors:
    print("FAILED:")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("ALL gold SQL OK")

conn.close()
