"""Seller concentration and risk."""
import numpy as np

from analysis.common import df


def scorecard():
    return df("select * from marts.seller_scorecard order by revenue desc")


def concentration(sc):
    r = np.sort(sc.revenue.to_numpy())[::-1]
    total = r.sum()
    n = len(r)
    share = lambda frac: r[: max(1, int(round(n * frac)))].sum() / total
    # Gini coefficient of seller revenue
    x = np.sort(r)
    gini = (2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum())
    sellers_for_half = int(np.searchsorted(np.cumsum(r) / total, 0.5) + 1)
    return {"sellers": n, "top1pct_share": share(0.01), "top10pct_share": share(0.10),
            "top20pct_share": share(0.20), "gini": gini, "sellers_for_50pct": sellers_for_half,
            "lorenz": np.concatenate([[0], np.cumsum(x) / total])}


def risk_summary(sc):
    est = sc[sc.is_established]
    risk = est[est.is_at_risk]
    return {"established": len(est), "at_risk": len(risk),
            "at_risk_revenue_share": risk.revenue.sum() / sc.revenue.sum(),
            "at_risk_low_review": risk.low_review_rate.mean(), "others_low_review": est[~est.is_at_risk].low_review_rate.mean(),
            "at_risk_late": risk.late_rate.mean(), "others_late": est[~est.is_at_risk].late_rate.mean()}
