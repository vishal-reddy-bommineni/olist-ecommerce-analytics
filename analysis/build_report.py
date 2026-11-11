"""Step 3: run every analysis, save figures and write reports/INSIGHTS.md (auto-generated).

Usage:  python -m analysis.build_report
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

from analysis import customers, late_delivery, sellers
from analysis.common import BLUE, DARK, GREY, RED, df, save, style
from src.config import FIG_DIR, REPORTS_DIR

pct = lambda v, d=1: f"{v * 100:.{d}f}%"
fmt_p = lambda p: "p < 0.001" if p < 0.001 else f"p = {p:.3f}"
money = lambda v: f"R${v / 1e6:,.2f}M" if v >= 1e6 else f"R${v:,.0f}"


def overview():
    o = df("""
        select count(*) as orders, count(*) filter (where is_valid_order) as valid_orders,
               sum(order_value) filter (where is_valid_order) as gmv,
               avg(order_value) filter (where is_valid_order and items > 0) as aov,
               avg(is_late::int) filter (where is_delivered) as late_rate,
               median(delivery_days) filter (where is_delivered) as median_delivery_days,
               avg(review_score) as avg_review,
               min(order_date) as first_day, max(order_date) as last_day
        from marts.fct_orders""").iloc[0].to_dict()
    o["sellers"] = df("select count(*) as n from marts.dim_sellers").n[0]
    o["customers"] = df("select count(*) as n from marts.dim_customers").n[0]
    return o


def fig_monthly(m):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.bar(m.order_month, m.gmv / 1e6, width=20, color=BLUE)
    style(ax, "Monthly GMV (bars) and late-delivery rate (line)", None, "R$ millions")
    ax2 = ax.twinx()
    ax2.plot(m.order_month, m.late_rate * 100, color=RED, marker="o", ms=3)
    ax2.set_ylabel("Late deliveries (%)", color=RED)
    ax2.spines["top"].set_visible(False)
    save(fig, FIG_DIR / "monthly_gmv_late_rate.png")


def fig_lateness(b):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    colors = [GREY if "early" in str(x) or "day" in str(x) else RED for x in b.bucket]
    ax.bar(b.bucket.astype(str), b.low_review_rate * 100, color=colors)
    for i, r in b.iterrows():
        ax.text(i, r.low_review_rate * 100 + 1.5, f"{r.low_review_rate:.0%}\n(n={r.orders:,})", ha="center", fontsize=7)
    ax.set_ylim(0, 100)
    style(ax, "Share of 1-2 star reviews by delivery vs promised date", "Delivered relative to promised date", "1-2 star reviews (%)")
    ax.tick_params(axis="x", labelsize=8)
    save(fig, FIG_DIR / "low_reviews_by_lateness.png")


def fig_odds(t):
    labels = {"late": "Delivered late", "multi_seller": "Items from 2+ sellers", "multi_item": "2+ items",
              "freight_share": "Freight share (+1.0)", "log_value": "Order value (x e)",
              "promised_days": "Promised days (+1)"}
    t = t.sort_values("odds_ratio")
    fig, ax = plt.subplots(figsize=(7, 3.4))
    y = np.arange(len(t))
    ax.errorbar(t.odds_ratio, y, xerr=[t.odds_ratio - t.ci_low, t.ci_high - t.odds_ratio], fmt="o", color=DARK, capsize=3)
    ax.axvline(1, color=GREY, ls="--", lw=1)
    ax.set_xscale("log")
    ax.set_yticks(y, [labels[i] for i in t.index])
    for yi, v in zip(y, t.odds_ratio):
        ax.text(v * 1.15, yi + 0.15, f"{v:.2f}", fontsize=8)
    style(ax, "Adjusted odds ratios for a 1-2 star review (95% CI, log scale)", "Odds ratio", None)
    save(fig, FIG_DIR / "odds_ratios.png")


def fig_retention(curve):
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.plot(curve.months_since_first, curve.retention * 100, marker="o", color=BLUE)
    ax.set_ylim(0, max(0.8, curve.retention.max() * 130))
    style(ax, "Customers ordering again N months after their first order (all cohorts)",
          "Months since first order", "Customers active (%)")
    save(fig, FIG_DIR / "retention_curve.png")


def fig_lorenz(c):
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    x = np.linspace(0, 1, len(c["lorenz"]))
    ax.plot(x * 100, c["lorenz"] * 100, color=BLUE, label="Sellers")
    ax.plot([0, 100], [0, 100], color=GREY, ls="--", lw=1, label="Equal revenue")
    ax.legend(frameon=False, fontsize=8)
    style(ax, f"Seller revenue concentration (Gini {c['gini']:.2f})", "Sellers, smallest to largest (%)", "Cumulative revenue (%)")
    save(fig, FIG_DIR / "seller_lorenz.png")


def fig_categories(cat):
    top = cat.head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.barh(top.category, top.revenue / 1e6, color=BLUE)
    for i, r in enumerate(top.itertuples()):
        ax.text(r.revenue / 1e6 + 0.02, i, f"{r.avg_review_score:.2f}★", va="center", fontsize=8)
    style(ax, "Top 12 categories by revenue (label: average review)", "Product revenue, R$ millions", None)
    save(fig, FIG_DIR / "top_categories.png")


def build():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ov = overview()
    monthly = df("select * from marts.mart_monthly_kpis order by order_month")
    d = late_delivery.load()
    buckets = late_delivery.lateness_buckets(d)
    lr = late_delivery.fit(d)
    rep = customers.repeat_summary()
    second = customers.days_to_second_order()
    split = customers.same_day_split_orders()
    curve = customers.retention_curve()
    first = customers.first_review_vs_return()
    sc = sellers.scorecard()
    conc = sellers.concentration(sc)
    risk = sellers.risk_summary(sc)
    cat = df("select * from marts.mart_category_performance order by revenue desc")
    states = df("select * from marts.mart_state_delivery order by delivered_orders desc")

    fig_monthly(monthly); fig_lateness(buckets); fig_odds(lr["table"]); fig_retention(curve)
    fig_lorenz(conc); fig_categories(cat)

    # growth: first vs last 6 complete months
    h1_17 = monthly[(monthly.order_month >= np.datetime64("2017-01-01")) & (monthly.order_month < np.datetime64("2017-07-01"))]
    h1_18 = monthly[(monthly.order_month >= np.datetime64("2018-01-01")) & (monthly.order_month < np.datetime64("2018-07-01"))]
    growth = h1_18.gmv.sum() / h1_17.gmv.sum() - 1
    late_or = lr["table"].loc["late"]
    # chi-square: first experience vs coming back
    first["returned"] = (first.customers * first.repeat_rate).round().astype(int)
    lo, hi = first.iloc[0], first.iloc[-1]
    chi = chi2_contingency([[lo.returned, lo.customers - lo.returned], [hi.returned, hi.customers - hi.returned]])
    slow = states.query("delivered_orders >= 500").sort_values("late_rate", ascending=False)
    top_bad = cat[(cat.orders >= 500) & (cat.category != "unknown")].sort_values("avg_review_score").head(3)
    early = buckets[buckets.bucket.astype(str).str.contains("early")]
    early_rate = (early.orders * early.low_review_rate).sum() / early.orders.sum()

    L = ["# Insights (auto-generated by `python -m analysis.build_report`, do not edit)", "",
         f"Data: {ov['orders']:,} orders ({ov['first_day']:%Y-%m-%d} to {ov['last_day']:%Y-%m-%d}), "
         f"{ov['customers']:,} customers, {ov['sellers']:,} sellers. Trends use complete months only (2017-01 to 2018-08).", "",
         "## Headline numbers", "",
         "| Metric | Value |", "|---|---|",
         f"| Valid orders (not canceled / unavailable) | {ov['valid_orders']:,} |",
         f"| GMV (items + freight, valid orders) | {money(ov['gmv'])} |",
         f"| Average order value | R${ov['aov']:,.2f} |",
         f"| GMV growth, H1 2018 vs H1 2017 | {pct(growth)} ({growth + 1:.1f}x) |",
         f"| Delivered after the promised date | {pct(ov['late_rate'])} |",
         f"| Median delivery time | {ov['median_delivery_days']:.1f} days |",
         f"| Average review score | {ov['avg_review']:.2f} / 5 |",
         f"| Customers who bought again on a later day | {pct(rep['repeat_rate'])} ({int(rep['repeat_customers']):,}) |",
         f"| Revenue from the top 10% of sellers | {pct(conc['top10pct_share'])} |", "",
         "## 1. Late delivery is the strongest driver of bad reviews", "",
         "![lateness](figures/low_reviews_by_lateness.png)", "",
         f"- Orders delivered early or on time get a 1-2 star review **{pct(early_rate)}** of the time; "
         f"orders 4-7 days late **{pct(buckets.iloc[4].low_review_rate, 0)}**, 8-14 days late **{pct(buckets.iloc[5].low_review_rate, 0)}**.",
         f"- Logistic regression on {lr['n']:,} delivered, reviewed orders, controlling for order value, item count, "
         f"multiple sellers, freight share, promised delivery time, customer state and month: "
         f"**odds ratio {late_or.odds_ratio:.1f}** (95% CI {late_or.ci_low:.1f}-{late_or.ci_high:.1f}, p < 0.001) "
         f"for a 1-2 star review when late (unadjusted {lr['raw_or']:.1f}).",
         f"- In probability terms: the model predicts a **{pct(lr['p_if_late'], 0)}** chance of a 1-2 star review if every order "
         f"were late vs **{pct(lr['p_if_on_time'], 0)}** if every order were on time.",
         f"- Orders split across **2+ sellers** (odds ratio {lr['table'].loc['multi_seller'].odds_ratio:.1f}) and with "
         f"**2+ items** ({lr['table'].loc['multi_item'].odds_ratio:.1f}) are also reviewed worse, consistent with parts of the order "
         "arriving separately or missing.",
         "- This is observational data: lateness is not randomly assigned, so the odds ratio is a strong association "
         "after controls, not a proven causal effect.", "",
         "![odds](figures/odds_ratios.png)", "",
         "## 2. Almost nobody comes back", "",
         f"- Only **{pct(rep['repeat_rate'])}** of {int(rep['customers']):,} customers bought again on a later day; they bring "
         f"{pct(rep['repeat_revenue_share'])} of revenue.",
         f"- {split['same_day_only']:,} of the {split['multi_order_customers']:,} customers with 2+ orders placed them all on the "
         "same day (split checkouts), so counting orders per customer overstates retention by "
         f"{pct(split['same_day_only'] / split['multi_order_customers'], 0)}.",
         f"- Month-1 retention averages **{pct(curve.retention.iloc[0], 2)}** across {curve.cohorts.iloc[0]} cohorts. "
         f"Returning customers came back after a median of {second['median_days']:.0f} days.",
         f"- Customers whose first order got 1-2 stars returned {pct(lo.repeat_rate)} of the time vs {pct(hi.repeat_rate)} after "
         f"4-5 stars (chi-square {fmt_p(chi[1])}). A bad first experience lowers return, but even happy customers rarely come back: "
         "retention is a structural problem, not only a service problem.", "",
         "![retention](figures/retention_curve.png)", "",
         "## 3. Revenue depends on a small group of sellers", "",
         f"- The top 1% of sellers bring **{pct(conc['top1pct_share'])}** of product revenue, the top 10% **{pct(conc['top10pct_share'])}**, "
         f"and just **{conc['sellers_for_50pct']}** of {conc['sellers']:,} sellers make half of it (Gini {conc['gini']:.2f}).",
         f"- Of {risk['established']} established sellers (30+ orders), **{risk['at_risk']}** are flagged at risk (late rate > 15% "
         f"or 1-2 star rate > 25%). They hold {pct(risk['at_risk_revenue_share'])} of revenue, deliver late "
         f"{pct(risk['at_risk_late'])} of the time (others {pct(risk['others_late'])}) and get 1-2 stars "
         f"{pct(risk['at_risk_low_review'])} of the time (others {pct(risk['others_low_review'])}).", "",
         "![lorenz](figures/seller_lorenz.png)", "",
         "## 4. Categories and regions", "",
         "![categories](figures/top_categories.png)", "",
         "| Category | Revenue | Share | Avg review | Late rate | Growth H1 18 vs 17 |", "|---|---|---|---|---|---|"]
    for r in cat.head(10).itertuples():
        L.append(f"| {r.category} | {money(r.revenue)} | {pct(r.revenue_share)} | {r.avg_review_score:.2f} | "
                 f"{pct(r.late_rate)} | {pct(r.growth_h1_2018_vs_2017, 0)} |")
    L += ["", "Lowest-rated large categories (500+ orders): " + ", ".join(
              f"{r.category} ({r.avg_review_score:.2f})" for r in top_bad.itertuples()) + ".", "",
          "States with the most late deliveries (500+ delivered orders):", "",
          "| State | Delivered orders | Late rate | Median delivery days | Avg review |", "|---|---|---|---|---|"]
    for r in slow.head(5).itertuples():
        L.append(f"| {r.state} | {r.delivered_orders:,} | {pct(r.late_rate)} | {r.median_delivery_days:.1f} | {r.avg_review_score:.2f} |")
    sp = states[states.state == "SP"].iloc[0]
    L += [f"| SP (largest, for comparison) | {sp.delivered_orders:,} | {pct(sp.late_rate)} | {sp.median_delivery_days:.1f} | {sp.avg_review_score:.2f} |",
          "", "![monthly](figures/monthly_gmv_late_rate.png)", "",
          "## Recommendations", "",
          "1. **Make delivery promises realistic where they are missed most.** Missing the promised date matters far more "
          f"than the promise itself (each extra promised day: odds ratio {lr['table'].loc['promised_days'].odds_ratio:.3f}; "
          "being late: " f"{late_or.odds_ratio:.1f}), and orders arriving early are rated best. Promising more accurate "
          "dates in the late-prone states above is a cheap first step to test.",
          "2. **Put the at-risk sellers on an improvement plan** with the scorecard (late and 1-2 star rates), starting with "
          "those with the most revenue.",
          "3. **Warn about or consolidate multi-seller orders**, which are reviewed much worse.",
          "4. **Invest in a second purchase**: with ~2% repeat, a post-delivery offer timed around the observed median gap "
          f"({second['median_days']:.0f} days) is worth testing with an A/B test before rolling out.",
          "5. **Reduce dependence on top sellers** by onboarding and supporting mid-tier sellers.", ""]
    (REPORTS_DIR / "INSIGHTS.md").write_text("\n".join(L), encoding="utf-8")
    lr["table"].round(4).to_csv(REPORTS_DIR / "late_delivery_odds_ratios.csv")
    buckets.round(4).to_csv(REPORTS_DIR / "low_reviews_by_lateness.csv", index=False)
    print(f"Written {REPORTS_DIR / 'INSIGHTS.md'} and {len(list(FIG_DIR.glob('*.png')))} figures")
    return {"overview": ov, "logit": lr, "repeat": rep, "concentration": conc, "risk": risk}


if __name__ == "__main__":
    build()
