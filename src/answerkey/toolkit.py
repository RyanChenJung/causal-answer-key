# %% [markdown]
# # Shared toolkit
#
# This section holds the code that several later sections share: constants, data loading and a few
# small helpers. Later sections call these functions by name. Read it as a reference and come back
# to it when a section uses one of the names below. The project spec is `docs/spec.md`.

# %%
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

__all__ = [
    "DATA_FILE",
    "DATA_SHA256",
    "CORE_COVARIATES",
    "FEATURES",
    "SEED",
    "FROZEN",
    "TRUTH_PP_EXPECTED",
    "TRUTH_SE_PP_EXPECTED",
    "TIE_BAND_PP",
    "find_data_file",
    "load_data",
    "complete_cases",
    "with_features",
    "difference_in_means_pp",
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

# Pre-registered answer key (spec §3). The truth is recomputed at run time and checked against these.
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
def load_data(path=None):
    path = Path(path) if path is not None else find_data_file()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != DATA_SHA256:
        raise ValueError(f"SHA-256 mismatch for {path.name}: {digest}")
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
