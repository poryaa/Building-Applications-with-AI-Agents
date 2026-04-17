import sqlite3
import re
import textwrap
import pandas as pd
from pathlib import Path

# ── Constants ──────────────────────────────────────────────
DB_PATH = "db/movielens.db"

# ══════════════════════════════════════════════════════════
# STEP 1: Seed MovieLens → SQLite
# ══════════════════════════════════════════════════════════
def seed_movielens(csv_folder: str, db_path: str = DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    for csv_file in Path(csv_folder).glob("*.csv"):
        table_name = csv_file.stem.lower()
        df = pd.read_csv(csv_file)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"✓ [SQLite] '{table_name}' — {len(df)} rows")
    conn.close()
    print("MovieLens SQLite DB ready.\n")

seed_movielens("data/movielens-latest-small")

# ══════════════════════════════════════════════════════════
# STEP 2: Load Chinook & Northwind → Pandas
# ══════════════════════════════════════════════════════════
def load_dataset(csv_folder: str) -> dict[str, pd.DataFrame]:
    dfs = {}
    for f in Path(csv_folder).glob("*.csv"):
        name = f.stem.lower()
        dfs[name] = pd.read_csv(f)
        print(f"✓ [Pandas] '{name}' — {dfs[name].shape}")
    return dfs

chinook_dfs   = load_dataset("data/Chinook")
northwind_dfs = load_dataset("data/Northwind")

# Single unified dict — this is what the agent's exec sandbox will use
ALL_PANDAS_DFS: dict[str, pd.DataFrame] = {**chinook_dfs, **northwind_dfs}
print(f"\nPandas backend: {list(ALL_PANDAS_DFS.keys())}\n")

# ══════════════════════════════════════════════════════════
# STEP 3: Context helpers for LLM prompts
# ══════════════════════════════════════════════════════════
def get_sql_schema(db_path: str = DB_PATH) -> str:
    """Returns DDL + row counts for every table — injected into SQL system prompt."""
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    parts = []
    for (table,) in cur.fetchall():
        cur.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
        parts.append(cur.fetchone()[0])
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        parts.append(f"-- {table}: {cur.fetchone()[0]} rows\n")
    conn.close()
    return "\n".join(parts)

def get_pandas_context(dfs: dict[str, pd.DataFrame] = ALL_PANDAS_DFS) -> str:
    """Returns shape + column names for every DataFrame — injected into Pandas system prompt."""
    lines = ["Available DataFrames (access via dfs['name']):"]
    for name, df in dfs.items():
        lines.append(f'  dfs["{name}"] → {df.shape} | columns: {", ".join(df.columns)}')
    return "\n".join(lines)

SQL_SCHEMA = get_sql_schema()
PANDAS_CONTEXT = get_pandas_context()
# ══════════════════════════════════════════════════════════
# STEP 4: Data-source registry — drives the router
# ══════════════════════════════════════════════════════════
DATA_SOURCE_REGISTRY: dict[str, str] = {
    # MovieLens → SQLite
    "movielens": "SQL",
    "movie":     "SQL",
    "rating":    "SQL",
    "tag":       "SQL",
    "link":      "SQL",
    # Chinook → Pandas
    "chinook":   "Pandas",
    "artist":    "Pandas",
    "album":     "Pandas",
    "track":     "Pandas",
    "invoice":   "Pandas",
    "customer":  "Pandas",
    "employee":  "Pandas",
    "genre":     "Pandas",
    "playlist":  "Pandas",
    # Northwind → Pandas
    "northwind": "Pandas",
    "order":     "Pandas",
    "product":   "Pandas",
    "supplier":  "Pandas",
    "shipper":   "Pandas",
    "category":  "Pandas",
}

# ── Quick smoke test ───────────────────────────────────────
if __name__ == "__main__":
    print("=== SQL Schema ===")
    print(get_sql_schema())
    print("\n=== Pandas Context ===")
    print(get_pandas_context())