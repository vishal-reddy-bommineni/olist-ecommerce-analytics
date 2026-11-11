"""Olist e-commerce dashboard. Reads the Parquet marts in data/marts (no database needed).

Run:  streamlit run app.py
"""
from pathlib import Path

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

MARTS = Path(__file__).parent / "data" / "marts"
BLUE, RED, GREY = "#2b6cb0", "#c53030", "#a0aec0"

st.set_page_config(page_title="Olist E-commerce Analytics", page_icon="📦", layout="wide")


@st.cache_resource
def con():
    c = duckdb.connect()
    for f in MARTS.glob("*.parquet"):
        c.execute(f"CREATE VIEW {f.stem} AS SELECT * FROM read_parquet('{f.as_posix()}')")
    return c


def as_pct(d: pd.DataFrame, *cols) -> pd.DataFrame:
    """Rates 0-1 -> percentages for display with one decimal."""
    d = d.copy()
    for c in cols:
        d[c] = d[c] * 100
    return d


PCT = lambda label: st.column_config.NumberColumn(label, format="%.1f%%")


@st.cache_data
def q(sql: str, params: tuple = ()) -> pd.DataFrame:
    return con().execute(sql, list(params)).df()


if not (MARTS / "fct_orders.parquet").exists():
    st.error("No data found in data/marts. Run `python run_pipeline.py` first.")
    st.stop()

# ---------------- sidebar filters ----------------
st.sidebar.header("Filters")
months = q("select distinct order_month from mart_monthly_kpis order by 1").order_month.dt.date.tolist()
start, end = st.sidebar.select_slider("Order month", options=months, value=(months[0], months[-1]),
                                      format_func=lambda d: d.strftime("%Y-%m"))
states = q("select distinct customer_state from fct_orders order by 1").customer_state.tolist()
pick_states = st.sidebar.multiselect("Customer state", states, placeholder="All states")
st.sidebar.caption("Complete months only (2017-01 to 2018-08). Valid orders exclude canceled and unavailable.")

where = "order_month between ? and ?"
params = [start, end]
if pick_states:
    where += f" and customer_state in ({', '.join('?' * len(pick_states))})"
    params += pick_states
params = tuple(params)

st.title("Olist E-commerce Analytics")
st.caption("100k real orders from a Brazilian marketplace (2016-2018). Models built with dbt + DuckDB; "
           "every number here is computed from the marts in this repository.")

tab_overview, tab_delivery, tab_customers, tab_sellers, tab_categories = st.tabs(
    ["Overview", "Delivery & reviews", "Customers", "Sellers", "Categories"])

# ---------------- overview ----------------
with tab_overview:
    k = q(f"""
        select count(*) filter (where is_valid_order) as orders,
               sum(order_value) filter (where is_valid_order) as gmv,
               avg(order_value) filter (where is_valid_order and items > 0) as aov,
               avg(is_late::int) filter (where is_delivered) as late_rate,
               avg(review_score) as review,
               count(distinct customer_unique_id) filter (where is_valid_order) as customers
        from fct_orders where {where}""", params).iloc[0]
    c = st.columns(6)
    c[0].metric("Orders", f"{k.orders:,.0f}")
    c[1].metric("GMV", f"R${k.gmv / 1e6:,.1f}M" if pd.notna(k.gmv) else "-")
    c[2].metric("Avg order value", f"R${k.aov:,.2f}" if pd.notna(k.aov) else "-")
    c[3].metric("Customers", f"{k.customers:,.0f}")
    c[4].metric("Late deliveries", f"{k.late_rate:.1%}" if pd.notna(k.late_rate) else "-")
    c[5].metric("Avg review", f"{k.review:.2f}" if pd.notna(k.review) else "-")

    m = q(f"""
        select order_month,
               sum(order_value) filter (where is_valid_order) as gmv,
               count(*) filter (where is_valid_order) as orders,
               avg(is_late::int) filter (where is_delivered) as late_rate,
               avg(review_score) as avg_review
        from fct_orders where {where} group by 1 order by 1""", params)
    base = alt.Chart(m).encode(x=alt.X("order_month:T", title=None, axis=alt.Axis(format="%Y-%m")))
    left, right = st.columns(2)
    left.subheader("Monthly GMV")
    left.altair_chart(base.mark_bar(color=BLUE).encode(
        y=alt.Y("gmv:Q", title="R$"), tooltip=[alt.Tooltip("order_month:T", format="%Y-%m"),
                                             alt.Tooltip("gmv:Q", format=",.0f"), alt.Tooltip("orders:Q", format=",")]),
        width="stretch")
    right.subheader("Late deliveries vs average review")
    late = base.mark_line(color=RED, point=alt.OverlayMarkDef(color=RED)).encode(y=alt.Y("late_rate:Q", title="Late rate", axis=alt.Axis(format="%")))
    rev = base.mark_line(color=BLUE, strokeDash=[4, 3]).encode(
        y=alt.Y("avg_review:Q", title="Avg review (dashed)", scale=alt.Scale(domain=[3.5, 4.5])))
    right.altair_chart(alt.layer(late, rev).resolve_scale(y="independent"), width="stretch")
    st.caption("Months with delivery problems (Nov 2017, Feb-Mar 2018) are the months with the lowest reviews.")

# ---------------- delivery ----------------
with tab_delivery:
    b = q(f"""
        select case when days_late <= -8 then '1. 8+ days early' when days_late < 0 then '2. 1-7 days early'
                    when days_late = 0 then '3. on the day' when days_late <= 3 then '4. 1-3 days late'
                    when days_late <= 7 then '5. 4-7 days late' when days_late <= 14 then '6. 8-14 days late'
                    else '7. 15+ days late' end as bucket,
               count(*) as orders, avg((review_score <= 2)::int) as low_review_rate, avg(review_score) as avg_review
        from fct_orders where is_delivered and review_score is not null and {where}
        group by 1 order by 1""", params)
    b["late"] = b.bucket.str.contains("late")
    st.subheader("Share of 1-2 star reviews by delivery vs promised date")
    st.altair_chart(alt.Chart(b).mark_bar().encode(
        x=alt.X("bucket:N", title=None, sort=None, axis=alt.Axis(labelAngle=0, labelExpr="slice(datum.label, 3)")),
        y=alt.Y("low_review_rate:Q", title="1-2 star reviews", axis=alt.Axis(format="%")),
        color=alt.Color("late:N", scale=alt.Scale(domain=[False, True], range=[GREY, RED]), legend=None),
        tooltip=["bucket", alt.Tooltip("orders:Q", format=","), alt.Tooltip("low_review_rate:Q", format=".1%"),
                 alt.Tooltip("avg_review:Q", format=".2f")]), width="stretch")
    st.caption("Adjusted for order value, items, sellers, freight, promised time, state and month, a late delivery "
               "multiplies the odds of a 1-2 star review by about 18 (see reports/INSIGHTS.md).")
    s = q(f"""
        select customer_state as state, count(*) as delivered_orders,
               avg(is_late::int) as late_rate, median(delivery_days) as median_days,
               avg(promised_days) as avg_promised_days, avg(review_score) as avg_review
        from fct_orders where is_delivered and {where} group by 1 order by delivered_orders desc""", params)
    st.subheader("By customer state")
    st.dataframe(as_pct(s, "late_rate"), hide_index=True, width="stretch", column_config={
        "state": "State",
        "late_rate": st.column_config.ProgressColumn("Late rate", format="%.1f%%", min_value=0, max_value=25),
        "median_days": st.column_config.NumberColumn("Median delivery days", format="%.1f"),
        "avg_promised_days": st.column_config.NumberColumn("Avg promised days", format="%.1f"),
        "avg_review": st.column_config.NumberColumn("Avg review", format="%.2f"),
        "delivered_orders": st.column_config.NumberColumn("Delivered orders", format="localized")})

# ---------------- customers ----------------
with tab_customers:
    r = q("select * from dim_customers")
    c = st.columns(3)
    c[0].metric("Customers", f"{len(r):,}")
    c[1].metric("Bought again on a later day", f"{r.is_repeat_customer.mean():.1%}")
    c[2].metric("Revenue from repeat customers",
                f"{r.loc[r.is_repeat_customer, 'lifetime_value'].sum() / r.lifetime_value.sum():.1%}")
    st.subheader("Cohort retention: share of each month's new customers who ordered again")
    h = q("""select strftime(cohort_month, '%Y-%m') as cohort, cohort_size, months_since_first, retention_rate
             from mart_cohort_retention where months_since_first between 1 and 12""")
    st.altair_chart(alt.Chart(h).mark_rect().encode(
        x=alt.X("months_since_first:O", title="Months since first order"),
        y=alt.Y("cohort:O", title="First-order month"),
        color=alt.Color("retention_rate:Q", title="Retention", scale=alt.Scale(scheme="blues"),
                        legend=alt.Legend(format="%")),
        tooltip=["cohort", "cohort_size", "months_since_first", alt.Tooltip("retention_rate:Q", format=".2%")]),
        width="stretch")
    st.caption("Fewer than 1% of customers order again in any later month. Cohort filters ignore the sidebar.")

# ---------------- sellers ----------------
with tab_sellers:
    sc = q("select * from seller_scorecard order by revenue desc")
    c = st.columns(4)
    c[0].metric("Sellers with sales", f"{len(sc):,}")
    c[1].metric("Top 10% share of revenue", f"{sc.head(round(len(sc) * 0.1)).revenue.sum() / sc.revenue.sum():.1%}")
    c[2].metric("Established (30+ orders)", f"{sc.is_established.sum():,}")
    c[3].metric("Flagged at risk", f"{sc.is_at_risk.sum():,}")
    only_risk = st.toggle("Show only at-risk sellers (late > 15% or 1-2 stars > 25%, 30+ orders)")
    min_orders = st.slider("Minimum orders", 1, 200, 30)
    view = sc[sc.orders >= min_orders]
    if only_risk:
        view = view[view.is_at_risk]
    st.altair_chart(alt.Chart(view).mark_circle(opacity=0.6).encode(
        x=alt.X("late_rate:Q", title="Late-delivery rate", axis=alt.Axis(format="%")),
        y=alt.Y("avg_review_score:Q", title="Average review", scale=alt.Scale(domain=[1, 5])),
        size=alt.Size("revenue:Q", title="Revenue (R$)"),
        color=alt.Color("is_at_risk:N", title="At risk", scale=alt.Scale(domain=[False, True], range=[BLUE, RED])),
        tooltip=["seller_id", "state", "orders", alt.Tooltip("revenue:Q", format=",.0f"),
                 alt.Tooltip("late_rate:Q", format=".1%"), alt.Tooltip("avg_review_score:Q", format=".2f")]),
        width="stretch")
    st.dataframe(as_pct(view[["revenue_rank", "seller_id", "state", "orders", "revenue", "late_rate", "avg_review_score",
                              "low_review_rate", "is_at_risk"]], "late_rate", "low_review_rate"),
                 hide_index=True, width="stretch", column_config={
        "revenue_rank": "Rank", "seller_id": "Seller", "state": "State", "orders": "Orders", "is_at_risk": "At risk",
        "revenue": st.column_config.NumberColumn("Revenue (R$)", format="%,.0f"),
        "late_rate": PCT("Late rate"),
        "low_review_rate": PCT("1-2 star rate"),
        "avg_review_score": st.column_config.NumberColumn("Avg review", format="%.2f")})
    st.caption("Seller metrics use all complete and partial months; sidebar filters do not apply here.")

# ---------------- categories ----------------
with tab_categories:
    cat = q(f"""
        select category, count(distinct order_id) as orders, sum(price) as revenue, avg(price) as avg_price,
               avg(review_score) as avg_review, avg(is_late::int) as late_rate
        from fct_order_items where is_valid_order and {where}
        group by 1 order by revenue desc""", params)
    n = st.slider("Categories shown", 5, 40, 15)
    st.altair_chart(alt.Chart(cat.head(n)).mark_bar(color=BLUE).encode(
        x=alt.X("revenue:Q", title="Product revenue (R$)"), y=alt.Y("category:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
        tooltip=["category", alt.Tooltip("revenue:Q", format=",.0f"), alt.Tooltip("orders:Q", format=","),
                 alt.Tooltip("avg_review:Q", format=".2f"), alt.Tooltip("late_rate:Q", format=".1%")]),
        width="stretch")
    st.dataframe(as_pct(cat, "late_rate"), hide_index=True, width="stretch", column_config={
        "category": "Category", "orders": "Orders",
        "revenue": st.column_config.NumberColumn("Revenue (R$)", format="%,.0f"),
        "avg_price": st.column_config.NumberColumn("Avg item price", format="%.2f"),
        "avg_review": st.column_config.NumberColumn("Avg review", format="%.2f"),
        "late_rate": PCT("Late rate")})

st.divider()
st.caption("Data: Olist Brazilian E-Commerce Public Dataset (Kaggle), CC BY-NC-SA 4.0.")
