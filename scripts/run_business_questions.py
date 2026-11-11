"""Run every query in sql/business_questions.sql and write reports/business_questions.md.

Usage:  python -m scripts.run_business_questions
"""
import math
import re

import pandas as pd

import duckdb

from src.config import DB_PATH, REPORTS_DIR, ROOT

SQL_FILE = ROOT / "sql" / "business_questions.sql"


def parse(text):
    """Split the file into (name, question, sql) blocks on '-- name:' lines."""
    blocks = []
    for chunk in re.split(r"^-- name:\s*", text, flags=re.M)[1:]:
        name, _, body = chunk.partition("\n")
        q = re.search(r"^-- Q:\s*(.+)$", body, flags=re.M)
        sql = "\n".join(l for l in body.splitlines() if not l.startswith("--")).strip().rstrip(";")
        blocks.append((name.strip(), q.group(1).strip() if q else "", sql))
    return blocks


def to_md(df, max_rows=25):
    df = df.head(max_rows)
    cols = list(df.columns)

    def fmt(v):
        if v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NaT:
            return "-"
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d") if v == v.normalize() else str(v)
        if isinstance(v, float):
            if v.is_integer() and abs(v) >= 1:
                return f"{v:,.0f}"
            return f"{v:.4f}".rstrip("0").rstrip(".") if abs(v) < 1 else f"{v:,.2f}"
        return str(v)
    L = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    L += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(L)


def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    L = ["# Business questions in SQL (auto-generated, do not edit)", "",
         "Queries: `sql/business_questions.sql`. Run against the dbt marts.", ""]
    for name, question, sql in parse(SQL_FILE.read_text(encoding="utf-8")):
        df = con.execute(sql).df()
        L += [f"## {question}", "", f"`{name}`", "", "```sql", sql, "```", "", to_md(df), ""]
        print(f"{name:28s} {len(df):>4} rows")
    con.close()
    (REPORTS_DIR / "business_questions.md").write_text("\n".join(L), encoding="utf-8")
    print(f"Written {REPORTS_DIR / 'business_questions.md'}")


if __name__ == "__main__":
    main()
