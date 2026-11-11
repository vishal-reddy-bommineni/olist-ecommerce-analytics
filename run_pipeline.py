"""Run the whole pipeline: load CSVs -> dbt build (models + tests) -> reports -> exports.

Usage:  python run_pipeline.py            # everything
        python run_pipeline.py --skip-load  # reuse the raw tables already in data/olist.duckdb
"""
import argparse
import subprocess
import sys
import time

from src.config import DBT_DIR, ROOT


def step(title):
    print(f"\n=== {title} ===", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-load", action="store_true")
    args = ap.parse_args()
    t0 = time.time()

    if not args.skip_load:
        step("1/5 Load raw CSVs into DuckDB")
        from src.load_raw import load
        load()

    step("2/5 dbt build (models + tests)")
    # run dbt through the current Python so the virtual environment's dbt is used
    cmd = [sys.executable, "-m", "dbt.cli.main", "build", "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)]
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        sys.exit("dbt build failed: a hard test failed or a model errored (warnings alone do not stop the run).")

    step("3/5 Data-quality report")
    from src.data_quality_report import build as dq
    dq()

    step("4/5 Analysis, figures and SQL business questions")
    from analysis.build_report import build as report
    report()
    from scripts.run_business_questions import main as bq
    bq()

    step("5/5 Export marts to Parquet")
    from src.export_marts import export
    export()

    print(f"\nDone in {time.time() - t0:.0f}s. Next: streamlit run app.py")


if __name__ == "__main__":
    main()
