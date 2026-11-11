# Power BI build guide

This guide builds a 3-page Power BI report on the same star schema the Streamlit dashboard uses.
You need **Power BI Desktop** (free, Windows; Microsoft Store or microsoft.com/power-bi/desktop) and
the pipeline already run (`python run_pipeline.py`), so that `data/marts/*.parquet` exist.
It takes about 1.5-2 hours the first time. Section 7 has the numbers your report must show.

## 0. Before loading anything
Power BI guesses relationships from column names, and here it would guess some wrong ones.
Turn that off first:

**File > Options and settings > Options > (Current file) Data Load** > untick
**"Autodetect new relationships after data is loaded"** > OK.

## 1. Load the tables (Power Query)
1. **Home > Transform data**. The Power Query Editor opens.
2. **Home > Manage Parameters > New Parameter**:
   - Name: `DataFolder`
   - Type: Text
   - Current Value: the full path of the repository's `data\marts\` folder **ending with a backslash**,
     e.g. `C:\...\olist-ecommerce-analytics\data\marts\`
   - OK.
3. **Home > New Source > Blank Query**, then **Home > Advanced Editor**, replace everything with:
   ```
   let
       Source = Parquet.Document(File.Contents(DataFolder & "fct_orders.parquet"))
   in
       Source
   ```
   Click Done. In the Query Settings pane on the right, rename the query from `Query1` to `fct_orders`.
4. Repeat step 3 for each table, changing the file name and the query name:
   `fct_order_items`, `dim_customers`, `dim_products`, `dim_sellers`, `dim_date`, `seller_scorecard`.
5. Check column types (icon left of each column header): `order_date`, `order_month`, `cohort_month`,
   `date`, `month_start` = **Date**; `*_at` columns = **Date/Time**; `is_*` columns = **True/False**;
   `order_value`, `price`, `revenue`, `*_rate` = **Decimal number**. Parquet keeps the types, so these
   should already be right.
6. **Home > Close & Apply**. Seven tables appear in the Data pane.

If Parquet does not load (very old Power BI versions), run `python -m src.export_marts --csv` and
load the CSVs from `powerbi/data/` with **Get data > Text/CSV** instead.

## 2. Relationships (Model view)
Open the **Model view** (third icon on the left). Create each relationship by dragging the column on
the fact table onto the matching column of the dimension table:

| From (many side) | To (one side) | Notes |
|---|---|---|
| `fct_orders[order_date]` | `dim_date[date]` | |
| `fct_orders[customer_unique_id]` | `dim_customers[customer_unique_id]` | |
| `fct_order_items[order_date]` | `dim_date[date]` | |
| `fct_order_items[product_id]` | `dim_products[product_id]` | |
| `fct_order_items[seller_id]` | `dim_sellers[seller_id]` | |

- Every relationship: cardinality **Many to one**, cross filter direction **Single** (the default).
- Do **not** connect `fct_order_items` to `fct_orders`, or `seller_scorecard` to anything. The scorecard
  is a ready-made summary table (one row per seller) and is used on its own on page 3.
- `dim_customers` only holds customers with at least one valid order, so customers whose only order
  was canceled show as "(Blank)". That is expected.

Then:
- Select `dim_date` in the Data pane > **Table tools > Mark as date table** > Date column: `date` > OK.
- Select `dim_date[month_name]` > **Column tools > Sort by column** > `month`.
- Hide technical columns from report view (right-click > Hide in report view): `order_id`,
  `customer_id`, `order_item_key`, `order_item_id`, `product_id`.

## 3. Measures
1. **Home > Enter data**, name the table `_Measures`, click **Load** (it holds measures only).
2. For each measure in `powerbi/measures.dax`: select `_Measures` in the Data pane > **New measure**,
   paste the measure (name line and formula), press Enter. Do them in order: later measures use earlier ones.
3. Formats (select the measure > **Measure tools**):
   - GMV, Product Revenue, GMV Previous Year, GMV Running Total: Currency, 0 decimals
   - Avg Order Value: Currency, 2 decimals
   - Every measure with Rate, Share or % in its name: Percentage, 1 decimal
   - Avg Review Score: Decimal, 2 decimals
4. Delete the empty `Column1` from `_Measures`. The table icon turns into a calculator icon.

### Calculated column for delivery buckets
Select `fct_orders` > **Table tools > New column**, paste:
```
Delivery Bucket =
VAR d = fct_orders[days_late]
RETURN
    IF (
        fct_orders[is_delivered] = FALSE () || ISBLANK ( d ), BLANK (),
        SWITCH (
            TRUE (),
            d <= -8, "1. 8+ days early",
            d < 0,   "2. 1-7 days early",
            d = 0,   "3. On the day",
            d <= 3,  "4. 1-3 days late",
            d <= 7,  "5. 4-7 days late",
            d <= 14, "6. 8-14 days late",
            "7. 15+ days late"
        )
    )
```
The number prefix keeps the buckets in order on the axis. These are the same buckets as the Python report.

## 4. Page 1: Executive overview
Rename the page "Overview" (double-click the tab at the bottom).
1. **Slicer**: field `dim_date[month_start]`. In Format > Slicer settings choose style **Between**.
   Set it to 1/1/2017 - 8/1/2018 (complete months only).
2. **Slicer**: field `fct_orders[customer_state]`, style **Dropdown**, multi-select on.
3. **Cards** (one card visual per measure): Valid Orders, GMV, Avg Order Value, Late Delivery Rate,
   Avg Review Score. Line them up across the top.
4. **Line and clustered column chart**:
   - X-axis: `dim_date[month_start]`. Right-click it in the field well and choose `month_start`, not
     Date Hierarchy.
   - Column y-axis: GMV
   - Line y-axis: Late Delivery Rate
   - Title: "Monthly GMV and late-delivery rate"
5. **Line chart**: X-axis `dim_date[month_start]`, Y-axis Avg Review Score. Title "Average review by month".
   The dips should line up with the late-delivery spikes (Nov 2017, Feb-Mar 2018).

## 5. Page 2: Delivery & satisfaction
1. **Clustered column chart**: X-axis `fct_orders[Delivery Bucket]`, Y-axis Low Review Rate.
   Sort the axis ascending by Delivery Bucket (the "..." menu > Sort axis). In the Filters pane, set
   Delivery Bucket to "is not blank". Turn on data labels. Title: "Share of 1-2 star reviews by delivery
   vs promised date".
2. **Table**: `fct_orders[customer_state]`, Delivered Orders, Late Delivery Rate, Median Delivery Days,
   Avg Review Score. Sort by Delivered Orders descending.
   Conditional formatting: in the Visualizations pane, right-click Late Delivery Rate >
   **Conditional formatting > Background color** > Format style Gradient (white to red).
3. **Card**: Low Review Rate.
4. Copy the two slicers from page 1 (Ctrl+C / Ctrl+V). When asked, choose **Sync** so both pages filter together.

## 6. Page 3: Sellers & categories
1. **Cards**: At-Risk Sellers, Top 10% Seller Revenue Share.
2. **Scatter chart**:
   - Values: `seller_scorecard[seller_id]`
   - X-axis: `seller_scorecard[late_rate]` (Average)
   - Y-axis: `seller_scorecard[avg_review_score]` (Average)
   - Size: `seller_scorecard[revenue]`
   - Legend: `seller_scorecard[is_at_risk]`
   - Filter on this visual: `seller_scorecard[is_established]` is True
   - Title: "Established sellers: late rate vs review (size = revenue)"
3. **Table**: `seller_scorecard[revenue_rank]`, `seller_id`, `state`, `orders`, `revenue`, `late_rate`,
   `avg_review_score`, `is_at_risk`. Filter: `is_at_risk` is True. Sort by `revenue_rank`.
4. **Bar chart** (clustered bar): Y-axis `dim_products[category]`, X-axis Product Revenue.
   Filters pane > `category` > Filter type **Top N** > Show items **Top 15** > By value: drag
   Product Revenue > Apply filter.

The seller visuals use the scorecard table. It has no date, so the month slicer does not change
them; add a text box saying "Seller metrics: all months".

## 7. Check the numbers
Your report must match the Python output exactly, because it reads the same tables.

**With the month slicer at 2017-01 to 2018-08 and no state selected** (same as the Streamlit Overview tab):

| Card | Value |
|---|---|
| Valid Orders | 97,910 |
| GMV | R$15,683,707 |
| Avg Order Value | R$160.19 |
| Late Delivery Rate | 6.8% |
| Avg Review Score | 4.09 |

**With the slicer cleared** (all months, matches `reports/INSIGHTS.md`):

| Card | Value |
|---|---|
| Valid Orders | 98,207 |
| GMV | R$15,735,527 |
| Avg Order Value | R$160.24 |
| Late Delivery Rate | 6.8% |
| Avg Review Score | 4.09 |
| Low Review Rate | 14.7% |
| Product Revenue | R$13,494,401 |
| Repeat Customer Rate | 2.2% |

**Page 3**: At-Risk Sellers = 61; Top 10% Seller Revenue Share = 67.4%.

If a number is off:
- **Too high**: check that the `is_valid_order` filter is in the measure, and that no extra relationship was auto-created (Model view).
- **Blank**: the `is_*` columns must be True/False, not text.
- **Repeat Customer Rate does not change with the slicers**: that is expected. It counts customers in
  `dim_customers`, and the slicers filter the fact tables, not the customer table.

## 8. Finish and publish
1. **View > Themes**: pick one with a dark blue primary color, so it looks like the Streamlit app.
2. Save as `powerbi/olist_dashboard.pbix`.
3. **File > Export > Export to PDF**, then save it as `powerbi/olist_dashboard.pdf`.
4. Take a screenshot of each page (Windows: Win+Shift+S) and save them as `powerbi/screenshots/page1.png`,
   `page2.png`, `page3.png`.
5. Add the screenshots to the README under "Dashboard":
   ```markdown
   ### Power BI
   ![Power BI overview](powerbi/screenshots/page1.png)
   ```
6. Commit the `.pbix`, the PDF and the screenshots. The `.pbix` contains the data (about 20 MB),
   which is fine for GitHub.
   Publishing to the Power BI Service needs a work or school account; the PDF and screenshots are enough for a portfolio.
