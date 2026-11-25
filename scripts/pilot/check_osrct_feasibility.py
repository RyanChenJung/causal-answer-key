"""Feasibility check: can we grade observational estimators against the RCT truth?

Design: observational sampling from an RCT (OSRCT; Gentzel, Pruthi & Jensen, ICML 2021).
For each unit we compute a "targeting" probability p(X). A treated unit is kept with
probability p(X)/2 and a control unit with probability 1 - p(X). Because the RCT is
2:1 treatment:control, P(keep | X) = 1/3 for every X, so the kept sample has the same
covariate distribution as the full RCT (same ATE), while P(T=1 | X, kept) = p(X).
Naive comparisons are therefore confounded by X, and the full-RCT difference in means
is the ground truth that every estimator should recover.

Estimators here are hand-rolled with sklearn so the check runs without DoWhy/EconML;
the project itself should use the packages.

Usage: python3 -I check_osrct_feasibility.py <karlan_list_2007.dta> [n_draws]
"""
import sys
import time
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold

# numpy 1.26 with macOS Accelerate emits spurious "encountered in matmul" warnings; results are finite.
warnings.filterwarnings("ignore", message=".*encountered in matmul")

path = sys.argv[1]
n_draws = int(sys.argv[2]) if len(sys.argv) > 2 else 20

df = pd.read_stata(path, convert_categoricals=False)
X_COLS = ["hpa", "freq", "years", "mrm2", "dormant", "female", "couple", "red0"]
df = df.dropna(subset=X_COLS + ["gave", "treatment"]).reset_index(drop=True)
T_all = df.treatment.to_numpy()
Y_all = df.gave.to_numpy()
truth = Y_all[T_all == 1].mean() - Y_all[T_all == 0].mean()
print(f"rows after dropping missing covariates: {len(df)} | RCT truth ATE(gave) = {truth*100:.3f} pp")

z = lambda s: (s - s.mean()) / s.std()
# Targeting rules: fundraisers send the matching-grant letter to "warm" donors.
warm_linear = z(np.log1p(df.freq)) - z(df.mrm2) + z(np.log1p(df.hpa))
warm_nonlin = 1.5 * ((df.mrm2 <= 6) & (df.freq >= 5)).astype(float) - 1.0 * (df.dormant == 1) \
    + 0.8 * (df.hpa > 50).astype(float) * (df.years > 5).astype(float)
SCENARIOS = {
    "A linear targeting": (warm_linear, X_COLS),
    "B nonlinear targeting": (z(warm_nonlin), X_COLS),
    "C hidden (mrm2 dropped)": (z(df.mrm2) * -1.5, [c for c in X_COLS if c != "mrm2"]),
}
GAMMA = 1.0  # targeting strength on the logit scale


def ps_model(X, T):
    return LogisticRegression(max_iter=2000).fit(X, T).predict_proba(X)[:, 1]


def estimators(X, T, Y, seed):
    out = {"naive": Y[T == 1].mean() - Y[T == 0].mean()}
    Xc = sm.add_constant(X)
    out["OLS adjust"] = sm.OLS(Y, np.column_stack([Xc, T])).fit().params[-1]
    e = np.clip(ps_model(X, T), 0.01, 0.99)
    w1, w0 = T / e, (1 - T) / (1 - e)
    out["IPW (Hajek)"] = (w1 @ Y) / w1.sum() - (w0 @ Y) / w0.sum()
    q = pd.qcut(e, 5, labels=False, duplicates="drop")
    strata = [(Y[(q == k) & (T == 1)].mean() - Y[(q == k) & (T == 0)].mean(), (q == k).mean()) for k in np.unique(q)]
    out["PS strata (5)"] = sum(d * w for d, w in strata)

    gb = lambda: HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, min_samples_leaf=100, random_state=seed)
    gbc = lambda: HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, min_samples_leaf=100, random_state=seed)
    s = gb().fit(np.column_stack([X, T]), Y)
    out["S-learner GB"] = (s.predict(np.column_stack([X, np.ones(len(T))])) - s.predict(np.column_stack([X, np.zeros(len(T))]))).mean()
    m1, m0 = gb().fit(X[T == 1], Y[T == 1]), gb().fit(X[T == 0], Y[T == 0])
    mu1, mu0 = m1.predict(X), m0.predict(X)
    out["T-learner GB"] = (mu1 - mu0).mean()
    d1, d0 = Y[T == 1] - mu0[T == 1], mu1[T == 0] - Y[T == 0]
    tau1, tau0 = gb().fit(X[T == 1], d1).predict(X), gb().fit(X[T == 0], d0).predict(X)
    out["X-learner GB"] = (e * tau0 + (1 - e) * tau1).mean()

    # cross-fitted nuisances for DR (AIPW) and DML (partialling out)
    mu1_cf, mu0_cf, my_cf, e_cf = (np.zeros(len(T)) for _ in range(4))
    for tr, te in KFold(3, shuffle=True, random_state=seed).split(X):
        a1 = tr[T[tr] == 1]
        a0 = tr[T[tr] == 0]
        mu1_cf[te] = gb().fit(X[a1], Y[a1]).predict(X[te])
        mu0_cf[te] = gb().fit(X[a0], Y[a0]).predict(X[te])
        my_cf[te] = gb().fit(X[tr], Y[tr]).predict(X[te])
        e_cf[te] = gbc().fit(X[tr], T[tr]).predict_proba(X[te])[:, 1]
    e_cf = np.clip(e_cf, 0.01, 0.99)
    psi = mu1_cf - mu0_cf + T * (Y - mu1_cf) / e_cf - (1 - T) * (Y - mu0_cf) / (1 - e_cf)
    out["DR / AIPW"] = psi.mean()
    out["_DR_se"] = psi.std(ddof=1) / np.sqrt(len(T))
    ry, rt = Y - my_cf, T - e_cf
    out["DML (PLR)"] = (rt * ry).sum() / (rt * rt).sum()
    return out, e


rng = np.random.default_rng(0)
t0 = time.time()
for name, (score, adj_cols) in SCENARIOS.items():
    p = 1 / (1 + np.exp(-GAMMA * score.to_numpy()))
    rows, ps_ranges, cover = [], [], 0
    for d in range(n_draws):
        u = rng.random(len(df))
        keep = np.where(T_all == 1, u < p / 2, u < 1 - p)
        X = df.loc[keep, adj_cols].to_numpy(float)
        est, e = estimators(X, T_all[keep], Y_all[keep], seed=d)
        lo, hi = est["DR / AIPW"] - 1.96 * est["_DR_se"], est["DR / AIPW"] + 1.96 * est["_DR_se"]
        cover += lo <= truth <= hi
        est.pop("_DR_se")
        rows.append(est)
        ps_ranges.append((e.min(), e.max()))
    r = pd.DataFrame(rows) * 100
    summ = pd.DataFrame({"mean": r.mean(), "bias": r.mean() - truth * 100, "sd": r.std(),
                         "rmse": np.sqrt(((r - truth * 100) ** 2).mean())}).round(3)
    print(f"\n== {name}: n_kept ~ {keep.sum()}, givers ~ {int(Y_all[keep].sum())}, "
          f"PS range ~ [{np.mean([a for a, _ in ps_ranges]):.3f}, {np.mean([b for _, b in ps_ranges]):.3f}], "
          f"DR 95% CI coverage {cover}/{n_draws}  (pp; truth {truth*100:.3f})")
    print(summ.to_string())
print(f"\nelapsed {time.time() - t0:.0f}s")
