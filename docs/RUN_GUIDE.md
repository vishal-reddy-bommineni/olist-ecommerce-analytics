# Run guide

Commands are shown for Windows PowerShell; on macOS/Linux use `source .venv/bin/activate`.

## 1. Setup
```powershell
git clone https://github.com/vishal-reddy-bommineni/olist-ecommerce-analytics.git
cd olist-ecommerce-analytics
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Data
Download the dataset from https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce (free account),
unzip it, and copy the 8 CSVs listed in `data/README.md` into `data/raw/`. The geolocation file is not needed.

## 3. Pipeline
```powershell
python run_pipeline.py
```
Steps (about 15 seconds):
1. Loads the CSVs into `data/olist.duckdb` (schema `raw`) with explicit column types.
2. `dbt build`: creates the staging views, intermediate views and mart tables, and runs 55 tests.
   9 warnings are expected (known source issues, see `reports/DATA_QUALITY.md`); any failure stops the run.
3. Writes `reports/DATA_QUALITY.md`.
4. Runs the analysis: `reports/INSIGHTS.md`, `reports/business_questions.md`, charts in `reports/figures/`.
5. Exports the marts to `data/marts/*.parquet`.

Run single steps:
```powershell
python -m src.load_raw
dbt build --project-dir dbt --profiles-dir dbt
dbt test --project-dir dbt --profiles-dir dbt --select tag:data_quality
python -m src.data_quality_report
python -m analysis.build_report
python -m scripts.run_business_questions
python -m src.export_marts            # add --csv for Power BI CSVs in powerbi/data/
```
dbt docs (lineage graph in the browser):
```powershell
dbt docs generate --project-dir dbt --profiles-dir dbt
dbt docs serve --project-dir dbt --profiles-dir dbt
```

## 4. Tests
```powershell
python -m pytest -q
```

## 5. Dashboard
```powershell
streamlit run app.py
```
Stop with Ctrl+C.

## 6. Deploy on Streamlit Community Cloud
share.streamlit.io -> Create app -> this repository, branch `main`, main file `app.py`,
Python 3.13. No secrets are needed: the app reads the Parquet files in `data/marts/`.
To install only what the app needs, rename `requirements-app.txt` to `requirements.txt` in a
deployment branch (optional; the full requirements also work).

## 7. Power BI
Follow `powerbi/BUILD_GUIDE.md`.
