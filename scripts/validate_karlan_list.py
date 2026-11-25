"""Validate the Karlan & List (2007) data copy against the published paper."""
import sys

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

path = sys.argv[1]
reader = pd.io.stata.StataReader(path)
value_labels = reader.value_labels()
df = pd.read_stata(path, convert_categoricals=False)

print("== value labels")
for k, v in value_labels.items():
    print(k, v)

print("\n== coding of design variables (control vs treatment)")
for c in ["ratio", "size", "ask"]:
    print(pd.crosstab(df[c], df.treatment))

# ---------- Table 1: balance ----------
paper_t1 = {  # variable: (treatment mean, control mean)
    "mrm2": (13.012, 12.998), "hpa": (59.597, 58.960), "freq": (8.035, 8.047),
    "years": (6.078, 6.136), "dormant": (0.523, 0.524), "female": (0.275, 0.283),
    "couple": (0.091, 0.093), "pwhite": (0.831, 0.830), "pblack": (0.061, 0.062),
    "page18_39": (0.297, 0.298), "ave_hh_sz": (1.999, 1.986), "red0": (0.407, 0.399),
    "redcty": (0.512, 0.507), "nonlit": (2.485, 2.453), "cases": (1.499, 1.502),
}
print("\n== Table 1 replication (ours vs paper) + Welch t-test p-value")
rows = []
for v, (pt, pc) in paper_t1.items():
    t = df.loc[df.treatment == 1, v].dropna()
    c = df.loc[df.treatment == 0, v].dropna()
    p = stats.ttest_ind(t, c, equal_var=False).pvalue
    rows.append((v, round(t.mean(), 3), pt, round(c.mean(), 3), pc, round(p, 3)))
t1 = pd.DataFrame(rows, columns=["var", "treat_ours", "treat_paper", "ctrl_ours", "ctrl_paper", "p"])
t1["match"] = (abs(t1.treat_ours - t1.treat_paper) <= 0.0015) & (abs(t1.ctrl_ours - t1.ctrl_paper) <= 0.0015)
print(t1.to_string(index=False))
print("N treat / control:", int(df.treatment.sum()), int((df.treatment == 0).sum()), "(paper 33,396 / 16,687)")

# joint balance test: can covariates predict treatment?
cov = ["mrm2", "hpa", "freq", "years", "dormant", "female", "couple", "red0"]
jb = smf.logit("treatment ~ " + " + ".join(cov), data=df.dropna(subset=cov)).fit(disp=0)
print(f"joint balance logit LR test p = {jb.llr_pvalue:.3f}")

# ---------- Table 2A ----------
def panel(d, name):
    groups = {"control": d[d.treatment == 0], "treatment": d[d.treatment == 1]}
    for r in (1, 2, 3):
        groups[f"{r}:1"] = d[(d.treatment == 1) & (d.ratio == r)]
    out = {}
    for g, x in groups.items():
        givers = x[x.gave == 1]
        out[g] = [round(x.gave.mean(), 3), round(x.amount.mean(), 3), round(givers.amount.mean(), 3), len(x)]
    res = pd.DataFrame(out, index=["response", "dollars_uncond", "dollars_cond", "N"])
    print(f"\n== Table 2A {name} (ours)")
    print(res.to_string())

panel(df, "Panel A: all")
panel(df[df.blue0 == 1], "Panel B: blue states")
panel(df[df.red0 == 1], "Panel C: red states")

print("\n== totals raised (paper: all 45,860; control 13,566; treatment 32,294; 1:1 10,431; 2:1 11,423; 3:1 10,439)")
print("all", round(df.amount.sum()), "control", round(df.loc[df.treatment == 0, "amount"].sum()),
      "treatment", round(df.loc[df.treatment == 1, "amount"].sum()),
      {r: round(df.loc[(df.treatment == 1) & (df.ratio == r), "amount"].sum()) for r in (1, 2, 3)})

# ---------- factorial design ----------
tr = df[df.treatment == 1]
cells = tr.groupby(["ratio", "size", "ask"]).size()
print(f"\n== factorial cells among treated: {len(cells)} (expected 3 x 4 x 3 = 36)")
print("cell size min / max / mean:", cells.min(), cells.max(), round(cells.mean(), 1))
print("chi-square independence ratio x size:", round(stats.chi2_contingency(pd.crosstab(tr.ratio, tr["size"]))[1], 3),
      "| ratio x ask:", round(stats.chi2_contingency(pd.crosstab(tr.ratio, tr.ask))[1], 3),
      "| size x ask:", round(stats.chi2_contingency(pd.crosstab(tr["size"], tr.ask))[1], 3))

# ---------- headline effects ----------
print("\n== headline effects (OLS, robust SE)")
m1 = smf.ols("gave ~ treatment", data=df).fit(cov_type="HC1")
print(f"gave ~ treatment: {m1.params.treatment:.4f} (se {m1.bse.treatment:.4f}, p {m1.pvalues.treatment:.4f})")
m2 = smf.ols("amount ~ treatment", data=df).fit(cov_type="HC1")
print(f"amount ~ treatment: {m2.params.treatment:.3f} (se {m2.bse.treatment:.3f}, p {m2.pvalues.treatment:.3f})")
m3 = smf.ols("gave ~ ratio2 + ratio3", data=tr).fit(cov_type="HC1")
print("treated only, gave ~ ratio2 + ratio3 (vs 1:1):", m3.params.round(4).to_dict(), "p:", m3.pvalues.round(3).to_dict())
m4 = smf.ols("gave ~ treatment * red0", data=df).fit(cov_type="HC1")
print("gave ~ treatment * red0:", m4.params.round(4).to_dict(), "p(interaction):", round(m4.pvalues["treatment:red0"], 3))

# ---------- data quality / project fit ----------
print("\n== data quality")
print("exact duplicate rows:", df.duplicated().sum(),
      "| of which missing zip-level demographics:", df[df.duplicated(keep=False)].pwhite.isna().sum())
print("givers total:", int(df.gave.sum()), "| control:", int(df.loc[df.treatment == 0, "gave"].sum()),
      "| treatment:", int(tr.gave.sum()))
print("amount among givers: describe\n", df.loc[df.gave == 1, "amount"].describe().round(1))
print("rows with any missing covariate (of", len(df), "):", df[cov + ["pwhite", "median_hhincome"]].isna().any(axis=1).sum())
