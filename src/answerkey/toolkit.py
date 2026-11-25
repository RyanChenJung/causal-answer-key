# %% [markdown]
# # Shared toolkit
#
# This section holds the code that several later sections share: constants, data loading, the OSRCT
# sampler, the estimators and the scoring functions. Later sections call these functions by name.
# Read it as a reference and come back to it when a section uses one of the names below.
# The project spec is `docs/spec.md`; ticket keys such as `[C1]` name the GitHub issue that owns a block.

# %%
import hashlib
import os
from pathlib import Path

import numpy as np
import pandas as pd

__all__ = [
    "DATA_FILE", "DATA_SHA256", "CORE_COVARIATES", "FEATURES", "SEED", "FROZEN",
    "TRUTH_PP_EXPECTED", "TRUTH_SE_PP_EXPECTED", "TIE_BAND_PP",
    "find_data_file", "load_data", "complete_cases", "with_features", "difference_in_means_pp",
]

# %% [markdown]
# **Constants** (spec §3, §6.2, §6.6). `FROZEN` holds the LightGBM settings shared by every
# estimator; add `random_state=<seed>` at each call, for example `LGBMRegressor(**FROZEN, random_state=s)`.

# %%
DATA_FILE = "data/karlan_list_2007.dta"
DATA_SHA256 = "7d13b9c4394c567a663c9eed27e1212204b65fe284f64edc772d7f61bdb330b5"

CORE_COVARIATES = ["hpa", "freq", "years", "mrm2", "dormant", "female", "couple", "red0"]
FEATURES = ["log_hpa", "log_freq", "years", "mrm2", "dormant", "female", "couple", "red0"]

SEED = 20261208
FROZEN = dict(
    n_estimators=150,
    learning_rate=0.05,
    num_leaves=31,
    min_child_samples=100,
    subsample=1.0,
    colsample_bytree=1.0,
    verbose=-1,
    n_jobs=1,
)

# Pre-registered answer key (spec §3). The truth is recomputed below and checked against these.
TRUTH_PP_EXPECTED = 0.4479
TRUTH_SE_PP_EXPECTED = 0.1318
TIE_BAND_PP = 0.1318

# %% [markdown]
# **`find_data_file`** looks for `data/karlan_list_2007.dta` in the current folder and its parents,
# so the same code works from the repo root, from `notebooks/` and from `build/`.

# %%
def find_data_file(name=DATA_FILE):
    here = Path.cwd().resolve()
    for folder in [here, *here.parents]:
        candidate = folder / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"{name} not found in {here} or any parent folder")

# %% [markdown]
# **`load_data`** reads the file with numeric factor codes, checks its SHA-256 and prints it.
# Codes: `ratio` 0 = control, 1 to 3 = 1:1 to 3:1; `size` 0 = control, 1 = $25k, 2 = $50k,
# 3 = $100k, 4 = unstated; `ask` 0 = control, 1 = 1x, 2 = 1.25x, 3 = 1.5x (spec §12.2).

# %%
def load_data(path=None, verbose=True):
    path = Path(path) if path is not None else find_data_file()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != DATA_SHA256:
        raise ValueError(f"SHA-256 mismatch for {path.name}: {digest}")
    if verbose:
        print(f"Loaded {path.name}, SHA-256 {digest} (matches the spec)")
    return pd.read_stata(path, convert_categoricals=False)

# %% [markdown]
# **`complete_cases`** keeps the 48,899 rows with all 8 core covariates, in file order (spec §3, §6.4).

# %%
def complete_cases(df):
    return df.dropna(subset=CORE_COVARIATES).reset_index(drop=True)

# %% [markdown]
# **`with_features`** returns a copy with the two log features used by every estimator (spec §6.2).

# %%
def with_features(df):
    out = df.copy()
    out["log_hpa"] = np.log1p(out["hpa"])
    out["log_freq"] = np.log1p(out["freq"])
    return out

# %% [markdown]
# **`difference_in_means_pp`** gives the difference in means of a 0/1 outcome, in percentage points,
# with the unpooled (Neyman) standard error.

# %%
def difference_in_means_pp(y, t):
    y = np.asarray(y, dtype=float)
    t = np.asarray(t).astype(bool)
    y1, y0 = y[t], y[~t]
    estimate = y1.mean() - y0.mean()
    se = np.sqrt(y1.var(ddof=1) / len(y1) + y0.var(ddof=1) / len(y0))
    return 100 * estimate, 100 * se

# %% [markdown]
# **The truth** (spec §3): recomputed from the data every run and checked against the pre-registered values.

# %%
_cc = complete_cases(load_data(verbose=False))
TRUTH_PP, TRUTH_SE_PP = difference_in_means_pp(_cc.gave, _cc.treatment)
assert abs(TRUTH_PP - TRUTH_PP_EXPECTED) < 5e-5 and abs(TRUTH_SE_PP - TRUTH_SE_PP_EXPECTED) < 5e-5
del _cc
__all__ += ["TRUTH_PP", "TRUTH_SE_PP"]

# %% [markdown]
# **Run mode and results paths** (spec §12.5, §12.8). `RUN_MODE` comes from the environment
# (`dev`, `full` or `cache`; default `dev`). In `dev`, everything written goes under `results/dev/`,
# so dev runs never touch the committed results.

# %%
RUN_MODE = os.environ.get("RUN_MODE", "dev")
if RUN_MODE not in ("dev", "full", "cache"):
    raise ValueError(f"RUN_MODE must be dev, full or cache, not {RUN_MODE!r}")
REPO_ROOT = find_data_file().parents[1]
RESULTS_DIR = REPO_ROOT / "results"


def results_path(name, dev=None):
    """Path under results/ (or results/dev/ in dev mode) for a §12.8 file name like 'refuters.csv'."""
    dev = (RUN_MODE == "dev") if dev is None else dev
    path = (RESULTS_DIR / "dev" / name) if dev else (RESULTS_DIR / name)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


__all__ += ["RUN_MODE", "REPO_ROOT", "RESULTS_DIR", "results_path"]

# %% [markdown]
# **`record_key`** writes one slide number into `key_numbers.csv` (spec §12.6, §12.8), replacing any
# earlier row with the same key. Keys are lowercase snake_case, for example `bias_a_e8_pp`.

# %%
KEY_UNITS = ("pp", "per1000", "usd", "p", "pct", "n", "ratio", "id")


def record_key(key, value, unit, source):
    if unit not in KEY_UNITS:
        raise ValueError(f"unit {unit!r} not in {KEY_UNITS}")
    if key != key.lower() or " " in key:
        raise ValueError(f"key {key!r} must be lowercase snake_case")
    path = results_path("key_numbers.csv")
    table = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["key", "value", "unit", "source"])
    table = table[table.key != key]
    row = pd.DataFrame([{"key": key, "value": value, "unit": unit, "source": source}])
    table = pd.concat([table, row], ignore_index=True).sort_values("key")
    table.to_csv(path, index=False)


__all__ += ["KEY_UNITS", "record_key"]

# %% [markdown]
# **Plot style and `save_figure`** (spec §12.4, §12.8). Every figure uses this style and is saved
# under one of the fixed names at 13.33 × 7.5 in, dpi 150. Owned by workstream D.

# %%
FIGURE_NAMES = (
    "fig01_osrct_diagram", "fig02_overlap_A0", "fig03_dag_rct", "fig04_dag_C_true_vs_convenient",
    "fig05_scoreboard", "fig06_diagnostics_crosstab", "fig07_sensitivity_C0", "fig08_red_blue",
    "fig09_policy_lists", "fig10_balance_smd", "fig11_ratio_partworths", "fig12_overlap_by_scenario",
)
FIGSIZE = (13.33, 7.5)


def set_plot_style():
    import matplotlib.pyplot as plt

    plt.rcParams.update({"figure.figsize": FIGSIZE, "figure.dpi": 100, "savefig.dpi": 150,
                         "font.size": 14, "axes.spines.top": False, "axes.spines.right": False})


def save_figure(fig, name):
    if name not in FIGURE_NAMES:
        raise ValueError(f"{name!r} is not a §12.8 figure name")
    path = results_path(f"figures/{name}.png")
    fig.set_size_inches(*FIGSIZE)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return path


__all__ += ["FIGURE_NAMES", "FIGSIZE", "set_plot_style", "save_figure"]

# %% [markdown]
# ## OSRCT sampler [C1] (spec §6.1 to §6.4)
# `z()` standardizes on the complete cases with the sample SD (`ddof=1`), as in the pilot.
# `targeting_p` gives the true p per scenario. `osrct_keep` turns one child seed into a kept mask
# and a draw seed. `load_draw` returns the kept rows for a production draw from `osrct_draws.npz`
# (`'Cproxy'` uses C's mask and draw seed).

# %%
SCENARIOS = ("A", "B", "C")
ADJUSTMENT_SETS = {
    "A": FEATURES,
    "B": FEATURES,
    "C": [f for f in FEATURES if f not in ("mrm2", "dormant")],
    "Cproxy": [f for f in FEATURES if f != "mrm2"],
    "RCT": FEATURES,
}


def targeting_p(cc, scenario):
    """True targeting probability p(X) for scenario 'A', 'B' or 'C' (array of len(cc))."""
    raise NotImplementedError("[C1]")


def production_child(scenario, d):
    """Index into SeedSequence(SEED).spawn(160) for production draw d of 'A', 'B' or 'C'."""
    return {"A": 0, "B": 1, "C": 2}[scenario] * 50 + d


def osrct_keep(p, treatment, child_index):
    """(keep mask, draw_seed) for one child seed, per spec §6.4."""
    raise NotImplementedError("[C1]")


def load_draw(df, scenario, d):
    """(kept rows of with_features(complete_cases(df)), true p of the kept rows, draw_seed)."""
    raise NotImplementedError("[C1]")


__all__ += ["SCENARIOS", "ADJUSTMENT_SETS", "targeting_p", "production_child", "osrct_keep", "load_draw"]

# %% [markdown]
# ## Nuisance helpers [C2] (spec §6.6)

# %%
def make_splitter(draw_seed):
    """StratifiedKFold(5, shuffle=True, random_state=draw_seed). Always an object, never an index list."""
    raise NotImplementedError("[C2]")


class ClippedClassifier:
    """Wraps a classifier; predict_proba clips column 1 to [lo, hi] and sets column 0 = 1 - column 1.
    [C2] must make it a BaseEstimator + ClassifierMixin so sklearn.base.clone works."""

    def __init__(self, base, lo=0.01, hi=0.99):
        raise NotImplementedError("[C2]")


def shared_propensity(X, T, draw_seed):
    """Clipped cross-fitted LGBM propensity e_hat (spec §6.6), shape (n,)."""
    raise NotImplementedError("[C2]")


__all__ += ["make_splitter", "ClippedClassifier", "shared_propensity"]

# %% [markdown]
# ## Estimator interface (spec §6.5 to §6.7)
# Every estimator is a function `f(data, adj, draw_seed, *, p_true=None, e_hat=None)` registered
# under its ID with `@register("E1")`. `data` is the kept rows from `load_draw` (or the RCT complete
# cases with features), `adj` the scenario's adjustment set. It returns
# `dict(estimate_pp=..., ci_lo_pp=..., ci_hi_pp=..., se_pp=...)` in pp, with NaN where the method has
# no CI. Each function converts to numpy itself and builds `make_splitter(draw_seed)` itself.
# [C3] registers R0 to R2 and E1 to E4, [C4a] E5, E5d, E6, E7, [C4b] E8 to E10, [C5] E11 and E12.

# %%
ESTIMATOR_IDS = ("R0", "R1", "R2", "E1", "E2", "E3", "E4", "E5", "E5d", "E6", "E7",
                 "E8", "E9", "E10", "E11", "E12")
CANDIDATES = ("E1", "E8", "E9", "E10")
CPROXY_ESTIMATORS = CANDIDATES
ESTIMATORS = {}


def register(est_id):
    if est_id not in ESTIMATOR_IDS:
        raise ValueError(f"unknown estimator {est_id!r}")

    def wrap(fn):
        ESTIMATORS[est_id] = fn
        return fn

    return wrap


def ci_row(estimate_pp, ci_lo_pp=np.nan, ci_hi_pp=np.nan):
    """Standard return value; se_pp = CI width / (2 × 1.959964) when a CI exists (spec §12.8)."""
    se_pp = (ci_hi_pp - ci_lo_pp) / (2 * 1.959964)
    return dict(estimate_pp=float(estimate_pp), ci_lo_pp=float(ci_lo_pp), ci_hi_pp=float(ci_hi_pp), se_pp=float(se_pp))


__all__ += ["ESTIMATOR_IDS", "CANDIDATES", "CPROXY_ESTIMATORS", "ESTIMATORS", "register", "ci_row"]

# %% [markdown]
# ## Fitted-object helpers for refuters and sensitivity [C3, C4b] (spec §7)
# `fit_e1` returns DoWhy's `(model, estimand, estimate)` for E1; `econml_route` does the same for E8 or
# E9 through DoWhy's EconML route; `fit_e9` returns the fitted `LinearDML`.

# %%
def fit_e1(data, adj):
    raise NotImplementedError("[C3]")


def econml_route(est_id, data, adj, draw_seed):
    raise NotImplementedError("[C4b]")


def fit_e9(data, adj, draw_seed):
    raise NotImplementedError("[C4b]")


__all__ += ["fit_e1", "econml_route", "fit_e9"]

# %% [markdown]
# ## Draw-level diagnostics [C7d] (spec §6.10)

# %%
def draw_diagnostics(data, adj, e_hat, draw_seed):
    """dict(share_ps_outside, max_abs_smd_ipw, ps_auc_cv, brier_ratio_cv) for one draw."""
    raise NotImplementedError("[C7d]")


__all__ += ["draw_diagnostics"]

# %% [markdown]
# ## Metrics and the go-to rule [C10] (spec §6.8, §6.9)
# `metrics_table` has one row per (scenario, estimator) with mean_pp, bias_pp, sd_pp, rmse_pp,
# mcse_bias_pp, pct_bias_removed, coverage_pct, mcse_cov_pct, se_ratio, mcse_seratio, ci_width_pp,
# n_draws, pass_bias, pass_cov, pass_seratio, pass_all and borderline_bias/cov/seratio (pass_* per
# scenario; candidate-only columns NaN elsewhere). `goto` applies §6.9 and returns
# dict(primary, co, fallback, scores).

# %%
def metrics_table(draws, truth_pp=TRUTH_PP):
    raise NotImplementedError("[C10]")


def goto(metrics):
    raise NotImplementedError("[C10]")


__all__ += ["metrics_table", "goto"]

# %% [markdown]
# ## Interaction screen [A2] (spec §4.2) and power [A4] (spec §4.4)
# Shared with §8: `interaction_screen` returns the step-1 table (term, coef, HC2 p, Holm p) and the
# joint HC2 F-test p-value; `mde_pp` and `n_per_arm` are the hand power formulas.

# %%
def interaction_screen(cc):
    raise NotImplementedError("[A2]")


def mde_pp(p, n_per_arm, alpha=0.05, power=0.80):
    raise NotImplementedError("[A4]")


def n_per_arm(p, effect_pp, alpha=0.05, power=0.80):
    raise NotImplementedError("[A4]")


__all__ += ["interaction_screen", "mde_pp", "n_per_arm"]
