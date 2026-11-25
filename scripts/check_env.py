"""Check that this machine can run the project. Post the full output on the onboarding issue.

Usage (from the repo root): uv run python scripts/check_env.py
"""
import os
import platform
import sys
import time
import warnings

os.environ.setdefault("MPLBACKEND", "Agg")
for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

from importlib.metadata import version  # noqa: E402

PINS = {
    "dowhy": "0.14",
    "econml": "0.17.1",
    "causalml": "0.15.5",
    "lightgbm": "4.7.0",
    "scikit-learn": "1.9.1",
    "numpy": "2.4.6",
    "pandas": "3.1.1",
    "scipy": "1.15.3",
    "statsmodels": "0.15.0",
    "pgmpy": "1.1.2",
}

problems = []
print(f"python {platform.python_version()} on {platform.system()} {platform.machine()} "
      f"(macOS {platform.mac_ver()[0] or 'n/a'})")
if sys.version_info[:2] != (3, 12):
    problems.append("Python must be 3.12")
for name, pin in PINS.items():
    got = version(name)
    flag = "" if got == pin else f"  <-- expected {pin}"
    print(f"{name:13s} {got}{flag}")
    if flag:
        problems.append(f"{name} {got} != {pin}")

start = time.time()
import numpy as np  # noqa: E402
from causalml.inference.meta import BaseRRegressor, BaseXRegressor  # noqa: E402,F401
from dowhy import CausalModel  # noqa: E402,F401
from econml.dml import CausalForestDML, LinearDML  # noqa: E402,F401
from lightgbm import LGBMClassifier, LGBMRegressor  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

from answerkey.toolkit import FROZEN, complete_cases, difference_in_means_pp, load_data  # noqa: E402

print(f"imports OK ({time.time() - start:.1f}s)")

cc = complete_cases(load_data())
truth, se = difference_in_means_pp(cc.gave, cc.treatment)
print(f"answer key: {truth:.4f} pp (SE {se:.4f}) on {len(cc):,} complete cases")
if abs(truth - 0.4479) > 5e-5:
    problems.append("answer key does not match the spec")

rng = np.random.default_rng(0)
X = rng.normal(size=(3000, 5))
T = rng.binomial(1, 1 / (1 + np.exp(-X[:, 0])))
Y = (rng.random(3000) < 0.05 + 0.02 * T).astype(float)
start = time.time()
est = LinearDML(model_y=LGBMRegressor(**FROZEN, random_state=0), model_t=LGBMClassifier(**FROZEN, random_state=0),
                discrete_treatment=True, cv=StratifiedKFold(5, shuffle=True, random_state=0), random_state=0)
est.fit(Y, T, X=X)
print(f"LinearDML smoke fit OK: ATE {est.ate(X):.4f} ({time.time() - start:.1f}s)")

print("ENV OK" if not problems else "ENV PROBLEMS: " + "; ".join(problems))
sys.exit(1 if problems else 0)
