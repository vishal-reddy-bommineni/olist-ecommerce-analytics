"""Does a late delivery cause a bad review? Logistic regression with controls.

Outcome: low review (1-2 stars). Exposure: delivered after the promised date.
Controls: order value (log), number of items, multiple sellers, freight share, promised delivery
time, customer state and purchase month. Odds ratios with 95% CIs (cluster-robust by customer).
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analysis.common import df

SQL = """
select order_id, customer_unique_id, review_score, is_late, days_late, delivery_days, promised_days,
       order_value, items, distinct_sellers, freight_value, items_value, customer_state,
       strftime(order_month, '%Y-%m') as month
from marts.fct_orders
where is_delivered and review_score is not null and items > 0
  and order_month >= '2017-01-01' and order_month < '2018-09-01'
"""


def load():
    d = df(SQL)
    d["low_review"] = (d.review_score <= 2).astype(int)
    d["late"] = d.is_late.astype(int)
    d["log_value"] = np.log(d.order_value)
    d["multi_item"] = (d["items"] > 1).astype(int)
    d["multi_seller"] = (d.distinct_sellers > 1).astype(int)
    d["freight_share"] = d.freight_value / d.order_value
    return d


def lateness_buckets(d):
    bins = [-np.inf, -8, -1, 0, 3, 7, 14, np.inf]
    labels = ["8+ days early", "1-7 days early", "on the day", "1-3 late", "4-7 late", "8-14 late", "15+ late"]
    d = d.assign(bucket=pd.cut(d.days_late, bins=bins, labels=labels))
    return (d.groupby("bucket", observed=True)
              .agg(orders=("order_id", "size"), avg_score=("review_score", "mean"),
                   low_review_rate=("low_review", "mean"))
              .reset_index())


def fit(d):
    formula = ("low_review ~ late + log_value + multi_item + multi_seller + freight_share"
               " + promised_days + C(customer_state) + C(month)")
    m = smf.logit(formula, data=d).fit(disp=False, cov_type="cluster",
                                       cov_kwds={"groups": pd.factorize(d.customer_unique_id)[0]})
    raw = smf.logit("low_review ~ late", data=d).fit(disp=False)
    keep = ["late", "log_value", "multi_item", "multi_seller", "freight_share", "promised_days"]
    ci = m.conf_int()
    table = pd.DataFrame({"odds_ratio": np.exp(m.params[keep]), "ci_low": np.exp(ci.loc[keep, 0]),
                          "ci_high": np.exp(ci.loc[keep, 1]), "p_value": m.pvalues[keep]})
    # average marginal effect of lateness on the probability of a low review
    p1 = m.predict(d.assign(late=1)).mean()
    p0 = m.predict(d.assign(late=0)).mean()
    return {"model": m, "table": table, "raw_or": float(np.exp(raw.params["late"])),
            "p_if_late": float(p1), "p_if_on_time": float(p0), "n": int(m.nobs),
            "pseudo_r2": float(m.prsquared)}
