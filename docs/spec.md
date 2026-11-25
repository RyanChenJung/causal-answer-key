# Answer Key: Project Spec

**Grading causal methods against a fundraising experiment.**
Team 7, ADSP 32029 Causal Models in Data Science, Fall 2026.

| | |
|---|---|
| Status | Draft for team review. Objections close **Wed 2026-11-25 23:59 CST**, and silence by then counts as consent. An objection must be written and must propose a concrete alternative. The spec then locks as git tag `spec-v1`. |
| Supersedes | The team brief (rev 2, 2026-11-24). Where they differ, this spec wins. |
| Presentation | **Tue 2026-12-08**, on Zoom, 12 minutes **including Q&A**, all four members speak. |
| Submission | PPT + HTML of one notebook, on Canvas, **before** the talk. The deck freezes Mon 12-07 21:00 and is uploaded by 23:00 (§17). |

**How to read this.**
- Sections marked **[pre-registered]** define how results are judged. After `spec-v1` they change only through §18, and never after the production run.
- Numbers marked **pilot** come from exploratory runs and must never be reported as results.
- Course weeks are cited as `[W5]` so we can show where each method comes from.
- The letters A to D mean workstreams. Where a letter does something (shares the screen, reviews, uploads), it means that stream's lead in the §15 roster.
- Coding agents: before starting a ticket, read `AGENTS.md`, §12 to §15, the spec section named in the ticket, and Appendix B.

---

## 1. Goal and grading

The final-project guideline asks us to:
- assess a causal impact from experimental or observational data, using DoWhy, EconML and CausalML as we see fit;
- be comprehensive, validate the causal impacts, and, when we rely on confidence intervals, ask whether the method's assumptions are violated by our data;
- deliver a 12-minute presentation, and submit the PPT and the HTML of the Python notebook.

The guideline says the A grade goes to teams that "come to a conclusion about the methods you think would be your Go-To methods in real life Causal Effect estimation." This project is built around earning that conclusion with evidence.

**Hard constraints**
- 12 minutes include Q&A. We plan a 9:30 talk and leave 2:30 for questions.
- All code must be visible in the submitted notebook. The submitted notebook imports nothing from our repo.
- The syllabus requires that each submitted assignment list its AI tools by product name and version (§17).

---

## 2. Framing

**Headline question:** *Which causal methods can you trust when there is no randomization?*

We use a real randomized experiment as the answer key:
1. The experiment gives the true effect of a matching-grant offer on donating.
2. We hide the randomization by building observational-looking samples in which the match letters appear targeted at warm donors (§6). We know which assumption each sample breaks.
3. We run the course's estimators on those samples and grade them against the true effect.
4. The go-to conclusion is a workflow: identify with DoWhy, estimate with the go-to estimators, then check with diagnostics, refuters and sensitivity analysis.

**Estimand.** The average treatment effect (ATE) of receiving any match offer versus the standard letter on the probability of giving, in percentage points (pp). We lead with **extra donors per 1,000 letters** and give pp in parentheses. We use the ATE because the decision is whether to mail the match letter to the whole file, and the sampling scheme keeps the ATE unchanged (§6.1). Heterogeneity (§8) uses conditional effects.

---

## 3. Data

**Source.** Karlan, D. and List, J. A. (2007), "Does Price Matter in Charitable Giving?", *American Economic Review* 97(5). The data are on Harvard Dataverse, doi:10.7910/DVN/27853, under CC0 1.0. Our file is the unchanged copy mirrored in the public replication repository `embeddedlayers/replication-karlan-list-2007`.
- File: `data/karlan_list_2007.dta` (5.4 MB).
- SHA-256: `7d13b9c4394c567a663c9eed27e1212204b65fe284f64edc772d7f61bdb330b5`.
- A provenance ticket compares the mirror with the official Dataverse file.

**Validation.** Our copy reproduces Table 1's donor-history and state variables, and every cell of Table 2A (`scripts/validate_karlan_list.py`).

**Design.** 50,083 past donors of a US civil-liberties nonprofit were mailed in August 2005. 16,687 received the standard letter (control) and 33,396 a match offer (treated); treated outnumber control 2 to 1. The treated arms fully cross three factors, giving 36 cells of 925 to 929 people:

| Factor | Levels |
|---|---|
| Match ratio | 1:1, 2:1, 3:1 |
| Match cap | $25,000, $50,000, $100,000, unstated |
| Suggested amount | 1x, 1.25x, 1.5x the donor's highest previous gift |

**Variables used**

| Name | Meaning |
|---|---|
| `treatment` | 1 = any match offer |
| `gave` | 1 = donated (outcome; about 2%; 1,034 donors in total) |
| `amount` | Dollars given (used descriptively only) |
| `hpa` | Highest previous gift |
| `freq` | Number of prior gifts |
| `years` | Years since first gift |
| `mrm2` | Months since last gift |
| `dormant` | 1 = no gift yet in 2005 (the last gift was 8 or more months before the August mailing). Exactly `1{mrm2 >= 8}` (verified on the 50,082 rows with `mrm2`: 0 exceptions) |
| `female`, `couple` | Household |
| `red0` | Red state |
| `ratio`, `size`, `ask` | Treated-arm factors, loaded as numeric codes (§12.2) |

**Known issues**
- The zip-code census variables do not match the paper's Table 1, although they are balanced across arms. They are not used in the benchmark.
- `dormant` is a deterministic function of `mrm2`. In the DAG we treat the two as one "recency" node (§5).
- There are 30 exact duplicate rows. We keep them and note it; there is no ID column.
- 1,184 rows (2.36%) miss at least one of the 8 core covariates. This includes the one row with missing `mrm2`.

**Row rule**
- The 8 core covariates are `CORE_COVARIATES = ['hpa', 'freq', 'years', 'mrm2', 'dormant', 'female', 'couple', 'red0']`, on their raw scale.
- The headline difference in means (§4.1) uses all **50,083** rows.
- Every covariate-based analysis, including the benchmark truth, uses the **48,899 complete cases** on `CORE_COVARIATES`.

**Population statement** (data slide, following the course's three-step check [W1]):
1. The population is this organization's past donors (1991 to 2005), mailed in August 2005.
2. The randomness comes from random assignment, not random sampling. The estimand is the intent-to-treat effect of mailing a match letter; whether the letter was read is unobserved.
3. Results generalize to this population only, not to other charities or new donors.

**The answer key** (complete cases, difference in means) **[pre-registered]**:

| Quantity | Value |
|---|---|
| Truth (ATE on `gave`) | **0.4479 pp**, shown as 0.45 pp or 4.5 extra donors per 1,000 letters |
| Standard error (unpooled, Neyman) | 0.1318 pp |
| 95% CI | [0.190, 0.706] pp |
| Tie band ("one truth-SE") | **0.1318 pp**, shown as 0.13 pp |

- **Code constants.** `TRUTH_PP` and `TRUTH_SE_PP` are computed at run time and asserted to equal 0.4479 and 0.1318 within 5e-5. `TIE_BAND_PP = 0.1318` is a fixed constant; it is not recomputed.
- The two-proportion z-test (§4.1) uses the pooled SE, 0.137 pp. The CI above uses the unpooled SE.
- On all 50,083 rows the effect is 0.418 pp (SE 0.130), and the effect on dollars is $0.154 per letter (SE 0.080; descriptive only).

---

## 4. Part 1: The experimental answer key [W1 to W3, W8]

Owner: workstream A.

### 4.1 Headline effect
- Difference in means on all rows and on complete cases, with a two-proportion z-test [W2] (pooled SE; see §3).
- A standardized mean difference (SMD) balance table for `CORE_COVARIATES` by arm. One markdown line defines SMD. The slide title (slide 2, §11) uses the course wording "assess randomization across experiment and control" [W4].

### 4.2 Two-step ANCOVA [W3, W4] (core) [pre-registered]
Run on the complete cases, with HC2 standard errors (a 0/1 outcome is heteroskedastic by construction [W1]). `Xc` means the 8 `CORE_COVARIATES` on their raw scale, each centred at its complete-case mean. Interacting the treatment with centred covariates follows Lin (2013).

1. **Step 1, interaction screen.** `gave ~ T + Xc + T:Xc`.
   - Test each of the 8 interactions, Holm-adjusted, and report the joint F-test.
   - **STOP rule:** if any interaction survives Holm, we do not report a single covariate-adjusted ATE as the headline. We report effects within the strata of that covariate (a blocked analysis [W2]) and keep the interaction in the model.
   - Under randomization (SMD about 0) an interaction means heterogeneity, not confounding. We say this explicitly.
   - Pilot: only `T:red0` survives Holm (adjusted p = 0.013). The joint F p = 0.069 is not significant.
   - The covariate scale is fixed here because the result depends on it: with §6.2's log features the joint F p is 0.024. The log version is a notebook-only sensitivity row.
2. **Step 2, ANCOVA.** `gave ~ T + Xc`, plus `T:red0_c` if step 1 stops. With centred covariates, the `T` coefficient is the average effect (pilot 0.442 pp). It is used only for the orthogonality check and is not reported as the headline. If STOP fires, the reported result is the red-state and blue-state effects.
3. **Orthogonality check** [W3]: the step-2 `T` coefficient should be close to the difference in means (0.448 pp).

This interaction table is reused as the screen in §8 and appears on a backup slide.

### 4.3 Factorial ANOVA on the treated rows [W2, W3, W8]
- Model: `gave ~ C(ratio, Sum) * C(size, Sum) * C(ask, Sum)` on the 33,396 treated rows, with effects (sum) coding. The factors are loaded as numeric codes (§12.2), so the empty control level never enters the design.
- Tests: Type II with HC3 robust errors. In a balanced design Type I and Type II nearly agree; we say so in one line.
- The test family is the 3 main effects, Holm-adjusted. Interactions are exploratory: 2-way interactions are summarized on a backup slide, the 3-way only in the notebook.
- Presentation: a partworth and attribute-importance table in the course's conjoint format [W8], with CIs. The main effects are null, so the importances are mostly noise; we say so.
- Ratio contrasts: 2:1 minus 1:1 (pilot +0.188 pp) and 3:1 minus 1:1 (+0.198 pp), each with a 95% CI, compared with the design's minimum detectable effect (MDE).
- A logistic likelihood-ratio cross-check, in the notebook only.

### 4.4 Power [W2]
One documented function computes everything. It uses the course's hand formula, MDE = (1.96 + 0.84) × SE, and cross-checks it with `statsmodels` `NormalIndPower` (Cohen's h). `NormalIndPower` is expected to give about 0.03 pp more (0.57 pp; n ≈ 92,000), because the arcsine scale effectively uses the variance under the alternative. We report the hand formula.

| Quantity | Pilot value | Inputs |
|---|---|---|
| MDE per ratio arm | 0.54 pp | All treated rows, no covariates; n ≈ 11,132 per arm; 1:1 rate 2.075%; SE = sqrt(2·p(1−p)/n); α = 0.05 two-sided; power 0.80 |
| n per arm to detect 0.19 pp | ≈ 88,000 (7.9x the actual) | same |
| MDE of the red/blue interaction | 0.74 pp | Complete cases; SE = sqrt(Σ p_st(1−p_st)/n_st) over the four cells s ∈ {red, blue}, t ∈ {treated, control}, with the observed cell rates |

- No post-hoc ("observed") power.
- Next mailing (one backup line): mail 1:1 only, n from the formula above, block on `red0`; a D-optimal fraction is the next step, with its alias limits noted [W3].

### 4.5 Dollars and break-even
- Extra dollars per letter on all rows, with a CI (descriptive; heavy-tailed outcome, so robust SEs).
- One break-even line: the cost per letter at which the match offer stops paying for itself.

---

## 5. Part 2: Causal structure [W4, W5, W9, A3]

Owner: workstream B.

- **DAG.** Treatment, outcome, the covariates, and domain edges with one sentence of story each, in the course's format [W9] (for example `years -> freq -> hpa`, `recency -> gave`).
  - Nodes: `['treatment', 'gave', 'log_hpa', 'log_freq', 'years', 'recency', 'female', 'couple', 'red0']`, with `recency = log1p(mrm2)`.
  - `dormant` is a deterministic function of `mrm2`, which breaks faithfulness. It is merged into the recency node and left out of the `falsify_graph` and BIC data. One line explains this.
  - In the RCT the treatment has no parents. In the OSRCT samples it has edges from the targeting variables.
- **Identification** with DoWhy `identify_effect` on this DAG. The backdoor set is empty in the RCT and equals the targeting variables in the OSRCT samples. One markdown cell writes out the truncated-product derivation [W9] and the adjustment formula [W5]. This cell is markdown only; the computed hand adjustment formula is an optional item (§10).
- **Graph refutation** with DoWhy `falsify_graph` [W5]:
  - Run on the full RCT and on scenario A, draw 0.
  - `falsify_graph` has no seed argument; it uses numpy's global random state. So call `dowhy.gcm.util.general.set_random_seed(20261208)` right before `falsify_graph(G, data, independence_test=generalised_cov_based, conditional_independence_test=generalised_cov_based, n_permutations=100, n_jobs=1, allow_data_subset=False, plot_histogram=False)`.
  - The test is the generalised covariance measure (GCM), `dowhy.gcm.independence_test.generalised_cov_measure.generalised_cov_based`. One line says why not the HSIC kernel test used in class: the kernel test is O(n²) at our row counts.
  - GCM is documented for continuous variables, so the tests that involve the binary nodes (`treatment`, `gave`, `female`, `couple`, `red0`) are approximate. One line says so.
  - If a run takes more than 10 minutes, use a fixed-seed sample of 10,000 rows and say so.
  - Interpret in the course's terms ("better than X% of permuted DAGs", LMC violations), with a power caveat.
- **Scenario C, two graphs side by side.** The *true graph* has recency latent, so DoWhy reports that the effect is not identifiable by backdoor. The *convenient graph* pretends recency is observed. The name "true graph" avoids clashing with "honest" causal forests.
- **BIC comparison** of 2 to 3 hand-written alternative DAGs [A3, W9]:
  - Use per-node OLS/Logit BIC, the A3 version.
  - The alternatives must differ in skeleton or v-structures, because Markov-equivalent DAGs tie [W4].
- This DAG is used only in §5. The §6 benchmark builds its DoWhy models from the adjustment sets (§6.5).

---

## 6. Part 3: The method benchmark (centerpiece) [W3 to W7]

Owner: workstream C (critical path), except §6.10 (B, including `fig06_diagnostics_crosstab`; C computes the draw-level diagnostics in the production loop), and §6.13, the CI audit and the other §6 figures (D).

### 6.1 Hiding the randomization (OSRCT) [pre-registered]
We use observational sampling from an RCT (Gentzel, Pruthi and Jensen, 2021). The idea of judging observational methods against an experiment goes back to LaLonde (1986).

For each person with covariates X we define a targeting probability `p(X) = logistic(γ · score(X))`, with γ = 1 (§6.3). Then:
- a treated person is kept with probability `p(X) / 2`;
- a control person is kept with probability `1 - p(X)`.

Because treated outnumber control 2 to 1, `P(keep | X) = 1/3` for every X. The kept sample therefore has the same covariate mix, and the same true ATE, as the experiment, while `P(T = 1 | X, kept) = p(X)`. A naive comparison is confounded by X.

These identities are exact only when the treated share is exactly 2/3; our fixed population's share is 0.6663. So the unit tests (`tests/test_osrct.py`) compare each bin with its exact expectation on the fixed population:
- Bins are deciles of the true p, or the distinct p values when p has fewer than 10 of them (scenario B has 6).
- Write π_i for person i's keep probability (p_i/2 if treated, 1 − p_i if control). In each bin, the kept fraction is compared with mean(π_i), and the kept treated share with Σπ_i·T_i / Σπ_i.
- The tolerance is 4 times the binomial Monte Carlo SE.

### 6.2 Shared feature matrix [pre-registered]
Toolkit constants:
- `FEATURES = ['log_hpa', 'log_freq', 'years', 'mrm2', 'dormant', 'female', 'couple', 'red0']`, with `log_hpa = np.log1p(hpa)` and `log_freq = np.log1p(freq)`. Every §6 and §8 estimator uses these columns. There are no interactions.
- `CORE_COVARIATES` (§3), on the raw scale, is used for the complete-case filter, the §4.1 SMD table and the §4.2 ANCOVA.
- **Adjustment sets.** A and B use `FEATURES`. C uses `FEATURES` minus `mrm2` and `dormant`. C-proxy uses `FEATURES` minus `mrm2`.
- EconML and CausalML always receive numpy arrays.

### 6.3 Scenarios [pre-registered]
Here `z()` means standardizing on the 48,899 complete cases, and γ = 1 throughout. Each scenario breaks one assumption.

**Targeting scores and adjustment sets**

| | Business story | Targeting score | Score SD | Adjustment set |
|---|---|---|---|---|
| **A** | Mail by RFM score | `z(log1p(freq)) - z(mrm2) + z(log1p(hpa))` | 2.01 | full matrix |
| **B** | Analyst segment rules | `z(1.5*1{mrm2<=6 & freq>=5} - 1.0*1{dormant=1} + 0.8*1{hpa>50 & years>5})` | 1.00 | full matrix |
| **C** | Recency-driven mailing; recency missing from the warehouse extract | `-1.5 * z(log1p(mrm2))` | 1.50 | matrix **without** `mrm2` and `dormant` |
| C-proxy (contrast) | Same draws as C | as C | 1.50 | matrix without `mrm2` (`dormant` kept) |

**What each scenario stresses**

| | True p range; share outside [0.05, 0.95] | Assumption stressed | Course failure name [W6, W7] |
|---|---|---|---|
| **A** | [0.000, 1.000]; 14.7% | Overlap | Positivity; propensity score sensitivity |
| **B** | [0.29, 0.88]; 0% | Functional form | Model misspecification; realizability; "incorrect functional form" |
| **C** | [0.009, 0.976]; 2.1% | No unmeasured confounding | Unmeasured confounding; conditional exchangeability; "wrong set of variables" |
| C-proxy (contrast) | as C | A coarse proxy is observed | |

- **Why C uses `log1p(mrm2)`.** It keeps the overlap problem from the long right tail of `mrm2` (max 168 months) out of the hidden-confounding test. In the pilot, the raw-`mrm2` version put 7.7% of units outside [0.05, 0.95].
- **B is a mild misspecification test.** In the pilot, the misspecified-logit IPW and OLS both stayed inside the band (bias about −0.05 to −0.08 pp). B mainly catches learners that shrink the effect, such as the S-learner. We expect the parametric methods (OLS and the logistic PS methods) to stay near the band, and we say so on the slide.
- **Pilot biases (verification runs, Appendix A).** With recency fully hidden (C): OLS +0.64 pp, IPW about +0.7 pp. The expected naive estimate is 3 to 4.4 times the truth across scenarios.
- **C-proxy (pilot).** Keeping `dormant` removes about 60% of the hidden-recency bias but leaves about +0.3 pp, still outside the band. A coarse proxy helps but does not fix hidden confounding.
- **Overlap plots.** The notebook shows one histogram per scenario (A, B and C) of the true p and the shared estimated propensity (§6.6), on draw 0. The estimated propensity is recomputed with the toolkit function.
- **Display names.** Scenarios use the business stories on slides and the course failure names in the scoreboard annotations and in the CI-audit table.

### 6.4 Draws and seeds [pre-registered]
- There are 50 draws per scenario.
- **Seeds.** `children = np.random.SeedSequence(20261208).spawn(160)`.
  - The production child for (scenario s, draw d) is `children[{'A': 0, 'B': 1, 'C': 2}[s] * 50 + d]`.
  - Children 150 to 159 are for smoke tests and nuisance-quality checks.
- **Per child.** `u = np.random.default_rng(child).random(48_899)`. A treated person is kept if `u < p/2`, a control person if `u < 1 - p`. `draw_seed = int(child.generate_state(1)[0] % 2**31)` is every learner's `random_state` and the fold seed.
- Positions refer to the complete cases in file order: `df.dropna(subset=CORE_COVARIATES).reset_index(drop=True)`.
- **C-proxy** reuses C's masks and draw seeds and runs only the four candidates (E1, E8, E9, E10). Its naive estimate equals C's. It appears as one extra column in the full scoreboard (backup) and as one line on slide 9. It is not used in §6.9 or §6.10.
- The production run therefore has 200 (scenario, draw) units: 150 full units and 50 C-proxy units. A full unit (A, B or C) writes 16 rows: R0 to R2, E1 to E12 and E5d. A C-proxy unit writes 4 rows: E1, E8, E9 and E10.
- The kept masks and the true p for all draws are saved to `results/osrct_draws.npz` (§12.8) and committed.

### 6.5 Estimators [pre-registered]
There are 12 graded estimators, 3 grey reference rows and 1 sensitivity row. Display names follow the course's CarPricing table [W7]: Package-Learner-BaseLearner.

| ID | Display name | Library call | CI | Tier |
|---|---|---|---|---|
| R0 | Naive difference in means | numpy | (none) | reference |
| R1 | Oracle-p IPW (Hájek, true p) | numpy | (none) | reference |
| R2 | DoWhy default IPW | DoWhy `backdoor.propensity_score_weighting`, defaults | (none) | reference |
| E1 | DoWhy-OLS | DoWhy `backdoor.linear_regression` | HC2 (statsmodels, same design) | **candidate** |
| E2 | DoWhy-PS-Strat-LR | `backdoor.propensity_score_stratification`, 5 strata | (none) | exploration |
| E3 | DoWhy-PS-Match-LR | `backdoor.propensity_score_matching`, 1-NN with replacement | (none) | exploration |
| E4 | DoWhy-PS-IPW-LR | `backdoor.propensity_score_weighting`, Hájek weights | (none) | exploration |
| E5 | EconML-S-LGBM | `econml.metalearners.SLearner` | (none) | exploration |
| E5d | EconML-S-LGBM (defaults) | `SLearner(overall_model=LGBMRegressor(n_jobs=1, verbose=-1, random_state=draw_seed))` | (none) | sensitivity, not graded |
| E6 | EconML-T-LGBM | `econml.metalearners.TLearner` | (none) | exploration |
| E7 | EconML-X-LGBM | `econml.metalearners.XLearner` | (none) | exploration |
| E8 | EconML-DR-LGBM-L | `econml.dr.LinearDRLearner` | `ate_interval` | **candidate** |
| E9 | EconML-R-LGBM-L (LinearDML) | `econml.dml.LinearDML` | `ate_interval` | **candidate** |
| E10 | EconML-CF-LGBM (CausalForestDML) | `econml.dml.CausalForestDML` | `ate__inference()` | **candidate** |
| E11 | CausalML-X-LGBM | `causalml.inference.meta.BaseXRegressor` | (none) | exploration |
| E12 | CausalML-R-LGBM | `causalml.inference.meta.BaseRRegressor` | (none) | exploration |

- **Calls.** In the 50-draw loop the EconML and CausalML estimators are called directly. The DoWhy estimators (E1 to E4, R2) go through `CausalModel.estimate_effect`.
- **How DoWhy models are built.** In §6, every DoWhy model is `CausalModel(data=kept_df, treatment='treatment', outcome='gave', common_causes=<scenario adjustment set>)`, with no `graph=`. E1 to E4 and R2 call `estimate_effect(estimand, method_name=..., target_units='ate', effect_modifiers=[], method_params=...)`. Passing the §5 DAG would silently change the backdoor set.
- **DoWhy route.** The DoWhy route for EconML is demonstrated once, on the untargeted RCT (§6.11), and is used by the refuters (§7).
  - Every route call is `estimate_effect(..., method_name='backdoor.econml.<module>.<Class>', target_units='ate', effect_modifiers=<scenario adjustment set>)`, with the same `init_params`, seed and splitter as the direct call.
  - Assertion: `abs(route.value - direct.ate(X)) < 1e-9`.
  - Only `.value` is read from the route. Its `get_confidence_intervals()` is per unit and is never used; CIs come only from the direct calls (§6.7).
- **Cross-package agreement** is reported descriptively and is not part of the §6.9 rule:
  - E7 versus E11 (X-learners). They share the outcome and CATE learners but differ in the propensity: EconML fits it in-sample, CausalML gets the cross-fitted one (§6.6).
  - E9 versus E12 (R-learners).
- **E1 estimand.** OLS without treatment × covariate terms, like LinearDML without X, targets an overlap-weighted average of conditional effects. Our data have heterogeneity (`T:red0`), so part of E1's bias can be an estimand gap rather than confounding. The CI audit says so.

### 6.6 Nuisance contract [pre-registered]
- **Outcome-type models** (outcome, pseudo-outcome, CATE): `LGBMRegressor` everywhere, including on the 0/1 outcome, where it estimates `P(gave | X)`. EconML's S, T and X learners call `.predict()`, so a classifier would return 0/1 labels.
- **Propensity models:** `LGBMClassifier`.
- **Frozen LightGBM parameters** (`FROZEN`): `n_estimators=150, learning_rate=0.05, num_leaves=31, min_child_samples=100, subsample=1.0, colsample_bytree=1.0, verbose=-1, n_jobs=1, random_state=<draw seed>`. Never set `is_unbalance` or `scale_pos_weight`. There is no tuning per estimator or per scenario.
- **CausalForestDML:** `n_estimators=500, min_samples_leaf=50, max_samples=0.45, honest=True, n_jobs=1`.
- **Cross-fitting.** Pass a splitter object, never a precomputed index list: `cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=draw_seed)`, with `mc_iters=1`.
  - A precomputed list breaks DoWhy's `data_subset_refuter`, which refits on 80% of the rows.
  - The same seeded splitter is used for E8, E9, E10, the shared propensity and the DoWhy route, so all of them get identical folds, including inside the refuters.
  - CausalML's R-learner (E12) cannot take custom folds. It uses `n_fold=5, random_state=draw_seed`; this is a known deviation.
- **Shared propensity.** `e_hat = np.clip(cross_val_predict(LGBMClassifier(**FROZEN), X, T, cv=<draw splitter>, method='predict_proba')[:, 1], 0.01, 0.99)`.
  - It feeds E11 and E12 through `p=e_hat`, and the §6.10 diagnostics.
  - EconML cannot take precomputed scores. E7 fits its propensity in-sample, as EconML does. E8 to E10 fit theirs inside EconML, on the shared folds and with the same LightGBM parameters.
- **Propensity clipping:** clip, never trim, at [0.01, 0.99].
  - E8: `min_propensity=0.01`.
  - E4: `min_ps_score=0.01, max_ps_score=0.99`.
  - E11, E12: `e_hat` is clipped before it is passed as `p=`.
  - E7, E9, E10: the propensity model (`propensity_model` or `model_t`) is `ClippedClassifier(LGBMClassifier(**FROZEN), lo=0.01, hi=0.99)`. This toolkit class subclasses `BaseEstimator` and `ClassifierMixin`, so EconML can clone it. Its `predict_proba` clips column 1 and sets column 0 to 1 minus column 1.
  - E2, E3: no clipping (they use ranks or distances). E2 drops strata that have no treated or no control units (`clipping_threshold=1`), and we report how many.
  - R2 is exempt by design. It uses DoWhy's defaults: `LogisticRegression()`, `ips_weight`, and clipping at [0.05, 0.95].
- **DoWhy PS methods (E2 to E4):** `propensity_score_model=make_pipeline(StandardScaler(), LogisticRegression(C=np.inf, max_iter=2000))` on the scenario's adjustment set (§6.2). `C=np.inf` makes it unpenalized; `penalty=None` is deprecated in scikit-learn 1.8+ and prints a warning. This model is correctly specified in A and wrong in B by design.
- **Recorded checks:**
  - Nuisance quality (outcome Brier and log-loss, propensity AUC), computed once on smoke child 150.
  - E5d (§6.5) answers "did a bad setting cause the S-learner result?".

### 6.7 CI contract [pre-registered]
- **E1:** the point estimate comes from DoWhy. The official CI is statsmodels OLS on the identical design with `cov_type="HC2"`. DoWhy's default (non-robust) CI is shown beside it in the notebook.
- **E8, E9:** fit with X = the scenario's adjustment set, so the reported number is the ATE.
  - Without X, LinearDML estimates an overlap-weighted coefficient, not the ATE.
  - The ATE is the mean CATE over the kept sample, with the CI from `ate_interval(X, alpha=0.05)`.
- **E10:** `ate__inference()`; read `.point_estimate` and `.conf_int(alpha=0.05)`. Do not use `CausalForestDML.ate_interval(X)`: in the 2026-11-24 API check (Appendix B) it was about twice as wide.
- **Never** average per-unit `effect_interval` bounds.
- **No bootstrap CIs** are computed for any §6 estimator. (The §8 list contrast uses a bootstrap SE; it is a separate test.)
- CausalML's `estimate_ate` also returns bounds, which we ignore. In the API check the R-learner's interval was implausibly narrow (width 0.0003, against 0.019 for the X-learner). The cause: causalml 0.15.5 divides the R-learner's SE by n instead of √n (`rlearner.py`, `estimate_ate`). This is a CI-audit example.
- **How intervals are judged.**
  - Every draw reuses the same 48,899 people, so the spread across draws is usually smaller than the sampling error a reported SE describes. In a pilot check with 300 to 400 draws, the empirical SD was 0.7 to 0.9 times the mean reported SE in B and C. In A it was 0.86 to 1.2, depending on the method, because extreme weights widen the spread. A DR estimator with a clipped propensity had an SE ratio of about 0.97 to 1.09 in A, close to the 0.9 floor.
  - We do not shrink intervals with √(1 − n_kept/48,899). That correction assumes everyone has the same chance of being kept, but OSRCT keeps people with unequal probabilities (p/2 or 1 − p). In the pilot it pushed a bias-free DR interval's coverage in A down to about 90.6%.
  - Instead, §6.9 uses two plain checks: raw coverage of the reported 95% CI, and the SE ratio (mean reported SE divided by the empirical SD of the 50 estimates). The SE-ratio band [0.9, 1.6] allows for the gap above, and still catches intervals that are clearly too narrow or too wide.
- **CI audit table** (notebook, plus a backup slide): method, CI source, the assumption behind it, and whether our data violate it, in course terms. It includes the E1 estimand note (§6.5) and the CausalML R-learner bug.

### 6.8 Metrics [pre-registered]
For each (scenario, estimator) over the 50 draws:
- mean estimate, bias (mean minus truth), empirical SD, RMSE;
- the Monte Carlo (MC) SE of the bias (SD / √50);
- `% bias removed = 1 - |mean(est) - truth| / |mean(naive) - truth|`, computed from the 50-draw means within each scenario, not per draw [W3, W4].

For candidates only:
- raw coverage of the reported 95% CI;
- the SE ratio: mean reported SE / empirical SD;
- mean CI width;
- the MC SE of coverage, `sqrt(c(1-c)/50)`: 3.1 pp at 95% and 4.2 pp at the 90% threshold.

**Borderline labels.** Each bias, coverage and SE ratio is shown with its MC SE. The MC SE of the SE ratio is about 10% of its value at 50 draws (ratio / √98). A value within 2 MC SEs of its threshold is labelled "borderline". The reporting follows Morris, White and Crowther (2019).

We also test the course's claim that quintile stratification removes about 90% of the bias, by reading the `% bias removed` of E2 in A and B.

### 6.9 Go-to rule [pre-registered]
- **Eligibility.** Only candidates (E1, E8, E9, E10), meaning methods that report their own CI. Exploration-tier methods are ranked by bias and RMSE for information only.
- **Pass criteria.** A candidate passes if, in **both** scenario A and scenario B:
  1. |bias| ≤ `TIE_BAND_PP` (0.1318 pp, shown as 0.13);
  2. raw coverage ≥ 90%; and
  3. the SE ratio is between 0.9 and 1.6. This catches intervals that are too narrow and intervals that are too wide.

  Slide wording: "the interval covered the answer, and its width matched the real variation."
- **Choice.**
  - Each passer's score is (RMSE_A + RMSE_B) / 2, unrounded.
  - The band holds the passers whose score is within 0.1318 pp of the best passing score.
  - The primary go-to is the best-scoring E8, E9 or E10 in the band. If none of them is in the band, it is the best-scoring passer.
  - The co-go-to is the best-scoring remaining passer in the band, if there is one.
  - At most two methods are named, primary first.
- **Cross-package agreement** (§6.5) is descriptive only and does not enter this rule.
- **Fallback.** If no candidate passes, the "least bad" method is the candidate with the smallest max(|bias_A|, |bias_B|). Its coverage and SE ratio are shown beside it, and we state plainly that no method met the bar.
- **Role of C.** Scenario C is not used for selection. It shows that every method fails under hidden confounding, and it tests whether the diagnostics (§6.10) and the sensitivity analysis (§7) warn us.
- **Grading error.** All estimators target the same fixed 48,899-person population, so the truth's SE adds no grading error. The 0.1318 pp band is a materiality scale, not a significance test.
- **Verdict wording.** Name the method and the workflow: DoWhy identify → go-to estimator → diagnostics, refuters and sensitivity. Add one "do not use when" line per go-to method, tied to the Week 7 breakdown lists.

### 6.10 "Would our diagnostics have told us?" [pre-registered]
In real life there is no answer key. So for each candidate and scenario we record the checks that are available without one, and compare them with the true pass/fail.

| Diagnostic | Computed on | Flag rule |
|---|---|---|
| Share of units with estimated propensity outside [0.05, 0.95] | every draw | > 5% |
| Max \|SMD\| over the adjustment set after Hájek ATE weighting | every draw | ≥ 0.10 |
| Cross-validated propensity AUC | every draw | reported only (> 0.80 = strong targeting) |
| Cross-validated outcome Brier score / constant-model Brier | every draw | reported only (≥ 1.0 = no signal) |
| Refuters (§7) | draw 0; E1, E8 and E9 in A and C only | fails a §7 pass rule; other cells show n/a |

- **Models.** The propensity diagnostics use the shared cross-fitted, clipped LGBM propensity (§6.6). SMD is the weighted mean difference divided by the unweighted pooled SD. The Brier score comes from a cross-fitted `LGBMRegressor` on [X, T], with predictions clipped to [1e-6, 1 − 1e-6].
- **When a diagnostic fires.** A draw-level diagnostic fires for a scenario if it flags in more than 50% of the draws.
- **Who builds it.** C computes the draw-level diagnostics inside the production loop and writes `results/diagnostics_draws.csv`. B builds the cross-tab.
- **The cross-tab.** Its rows are the 12 candidate × scenario cells. Its columns are each diagnostic's fire rate and whether it fires, plus the truth: the full §6.9 pass/fail in that scenario (bias, coverage and SE ratio).
- **How we judge a diagnostic:** it is useful if it fires more often in failing cells than in passing cells.
- **Expected story:** no diagnostic flags C, which is why sensitivity analysis is mandatory.

### 6.11 RCT unit-test table
All 12 estimators, the reference rows and E5d are run once on the untargeted complete-case RCT. The run uses the `FEATURES` adjustment set and seed 20261208 for every learner and for the folds. Its rows are stored in `results/benchmark_draws.csv` with `scenario = RCT`, `draw = 0` and `draw_seed = 20261208`. The table uses the instructor's CarPricing format: Model | Library | Response | Treatment | Confounders | Subgroups | ATE | CI.
- Every ATE should be within `TIE_BAND_PP` of `TRUTH_PP` (0.45 pp). `tests/test_rct_smoke.py` checks this.
- This table also shows the DoWhy → EconML route for E8 and E9, with the §6.5 assertion.

### 6.12 Production run [pre-registered fallback]
- **Smoke test, by 12-01.** One unit per scenario, through the exact production code: smoke children 150, 151 and 152 for A, B and C. The C-proxy unit reuses child 152's mask and draw seed, as in production (§6.4). The smoke test records the time per estimator and checks every CI extraction path.
  - If an API path fails, log an amendment that proposes a replacement path, and exclude that estimator from the DoWhy refuters if needed.
- **Production run, night of 12-03, after the code freeze,** on one named Mac (named at the 12-01 checkpoint). The same Mac is the export machine (§12.5).
  - Joblib (loky) runs the (scenario, draw) units in parallel with `n_workers = os.cpu_count() - 1`.
  - Inside the workers every estimator is single-threaded: LightGBM `n_jobs=1` and `CausalForestDML(..., n_jobs=1)`.
  - In causalml 0.15.5, `BaseRRegressor` does not accept `cv_n_jobs` (only its parent class does). Set it after construction: `r = BaseRRegressor(learner=..., n_fold=5, random_state=draw_seed)`, then `r.cv_n_jobs = 1`.
  - Before it starts the workers, the production loop sets `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `VECLIB_MAXIMUM_THREADS` to `"1"` in `os.environ`. Each worker is a fresh process and inherits them.
  - Each worker returns its unit's rows to the parent. Only the parent appends to `results/benchmark_draws.csv`, with one write per finished unit, then a flush.
  - On resume, a unit counts as done only if all of its estimator rows are present. Partial units are dropped and recomputed.
  - Each run writes `results/run_log.json` (§12.8).
- **Budget.** At most 4 hours of wall time. The smoke test projects it as (150 × full-unit time + 50 × C-proxy-unit time) / `n_workers`.
  - If the projection is over budget, first cut CausalForestDML trees from 500 to 200, then the folds from 5 to 3, and log the amendment before the production run (§18).
  - The number of draws is never cut.
- **Fallback.** If fewer than 50 draws per scenario are done by **12-04 09:00 CST**, report the completed draws (minimum 20) with their MC SEs.

### 6.13 Scoreboard
- **Full table** (notebook and a backup slide): the CarPricing format (Model | Library | Response | Treatment | Confounders | Subgroups). Then, for A, B and C: the mean ATE, the mean 95% CI (candidates only), raw coverage, SE ratio and `% bias removed`. A C-proxy ATE column covers the candidates. A grey Truth row (0.45 pp) and the reference rows sit on top.
- **Go-to table** (notebook and the tie-rule backup slide): for each candidate in A and B, the bias ± MC SE, RMSE, raw coverage ± MC SE, SE ratio ± MC SE, pass/fail and the §6.9 score. Borderline values are labelled.
- **Slide 7** shows a compact version: Model | Library | ATE in A, B and C (with the CI for candidates) | pass/fail, next to the figure. The response, treatment and confounders go in the slide subtitle.
- **Figure:** a dot-and-whisker chart with methods as rows grouped by family, panels for A, B and C, and a shaded ±0.13 pp band around the truth. Pass and fail are shown in colour, and borderline cells are marked.
- **Annotations:** each failure is labelled with the Week 7 breakdown item it matches, written from the actual results.

---

## 7. Part 4: Refutation and sensitivity [W5; extension]

Owner: workstream B.

DoWhy's estimate refuters are an extension. The course taught graph refutation (`falsify_graph`), not estimate refuters. Each refuter gets one plain sentence of explanation.

**Refuters [pre-registered]**

| | Setting |
|---|---|
| Methods | E1 (OLS), E8 (DR), E9 (LinearDML). E8 and E9 run through DoWhy's EconML route (§6.5). |
| Data | Scenario A draw 0, scenario C draw 0. The full RCT is used for E1 only. |
| Refuters | `placebo_treatment_refuter` (`placebo_type="permute"`), `random_common_cause`, `data_subset_refuter` (`subset_fraction=0.8`) |
| Simulations | E1: 50. E8 and E9: 20. Never fewer than 20. Seed 20261208. |
| Pass rules | Placebo: \|mean placebo effect\| < max(`TIE_BAND_PP`, 2 · SD_sims / √n_sims). Random common cause and subset: \|mean refuted estimate − original estimate\| below the same threshold. DoWhy's refutation p-value is reported alongside. |

Why the noise term: with a fixed 0.13 pp band and only 10 simulations, a correct method would fail the placebo check by chance about 7 to 10% of the time. With the noise term and at least 20 simulations, this falls to about 2%.

None of these three refuters can detect a hidden confounder, so passing them in C is expected by design, not a finding. The notebook and slide 9 say so.

**Sensitivity [pre-registered]**
- **E1 in C draw 0:**
  - Run DoWhy `add_unobserved_common_cause` with `simulation_method="linear-partial-R2"` once per benchmark: `benchmark_common_causes=['log_freq']`, then `['log_hpa']`. Each call uses `effect_fraction_on_treatment=[1, 2, 3]` and `plot_estimate=False`, and we draw our own contour plot.
  - Never pass two benchmarks in one call: DoWhy 0.14 keeps only the last.
  - Partial R² is explained as a squared partial correlation [W1].
  - Mark the *actual* partial R² of the hidden recency in that draw. This is possible only because we hid it ourselves. Use the Cinelli and Hazlett (2020) definitions, with Z = {`mrm2`, `dormant`} jointly and OLS on the kept draw, where X is C's adjustment set:
    - R²(T ~ Z | X) = (R²(T ~ X + Z) − R²(T ~ X)) / (1 − R²(T ~ X));
    - R²(Y ~ Z | T, X) is the same, with T added to both models.
  - Report `stats["robustness_value"]` (for the point estimate) and `stats["robustness_value_alpha"]` (for the CI).
- **E9 in C draw 0:** EconML `LinearDML.robustness_value(alpha=0.05)`, which is CI-based, compared with E1's `robustness_value_alpha`. One line notes that EconML's robustness value (Chernozhukov et al., 2022) is for the partially linear coefficient θ, not for E9's mean-CATE ATE. We print θ beside it, from the same E9 fit on C draw 0: `est.sensitivity_interval(alpha=0.05, c_y=0, c_t=0, interval_type="theta")` returns (θ, θ).
- DoWhy's sensitivity analyzer calls `plt.show()`. Scripts must set `matplotlib.use("Agg")`, otherwise it hangs on macOS.
- **Expected story:** the refuters pass while the bias remains; only the sensitivity analysis reveals the fragility. Slide 9 is titled "Which checks caught C?".

---

## 8. Part 5: Heterogeneity and targeting (lean) [W2, W3, W6, W7]

Owner: workstream D. This part uses the full RCT complete cases, with no OSRCT sampling. The propensity is known to be 2/3, so the models here use `DummyClassifier(strategy="prior")` as the propensity. This is the one exception to §6.6.

Every model in §8 uses seed 20261208: `FROZEN` with `random_state=20261208`, `cv=StratifiedKFold(5, shuffle=True, random_state=20261208)`, and `random_state=20261208` on each EconML estimator. CausalForestDML uses the §6.6 forest settings.

1. **Screen.** Reuse the step-1 interaction table from §4.2. Only `red0` is expected to survive.
2. **Red versus blue** [W2 blocked analysis]:
   - The difference in means within each state colour is the answer.
   - Beside it, LinearDML and CausalForestDML give subgroup estimates with CIs. Both use `model_y=LGBMRegressor(**FROZEN)`, `model_t=DummyClassifier(strategy="prior")`, X = `red0` and W = the other 7 `FEATURES`. The subgroup CIs come from `effect_interval(np.array([[0], [1]]), alpha=0.05)`.
   - Pilot: red-state effect 0.93 pp, blue 0.13 pp.
3. **Power:** the interaction MDE is 0.74 pp, plus the n needed next time (§4.4).
4. **Model-free policy:** mailing only red-state donors uses 40.4% of the letters (19,760 complete cases) and earns 83.4% of the extra donors (pilot). The share is n_red·τ_red / (n_red·τ_red + n_blue·τ_blue). An ethics and PR caveat goes with it: this is targeting by political geography.
5. **ML contrast** (one test) **[pre-registered]**:
   - Scores: τ̂ from 5-fold out-of-fold fits of `DRLearner(model_propensity=DummyClassifier(strategy="prior"), model_regression=LGBMRegressor(**FROZEN), model_final=LGBMRegressor(**FROZEN), cv=StratifiedKFold(5, shuffle=True, random_state=20261208), random_state=20261208)`, with X = `FEATURES`. The outer out-of-fold split is the same `StratifiedKFold(5, shuffle=True, random_state=20261208)` on T.
   - Three mailing lists of n = 19,760 (the red-list size): the top n by τ̂, the red-state rule (`red0 = 1`), and a uniform random n (seed 20261208).
   - Each list's value is the difference in means inside the list, times 10, in extra donors per 1,000 letters, with a Neyman SE (about 0.20 pp).
   - The test: DR top minus the red-state rule. Its SE comes from 2,000 bootstrap resamples of the file (seed 20261208), rebuilding all three lists in each resample with τ̂ held fixed. The random list is a fresh uniform draw of n from each resample.
   - The same bootstrap also gives the SE of the red-state rule minus the random list, which is used only in §9.
   - One list "beats" another when the 95% CI of their difference (± 1.96 bootstrap SE) is above zero.
   - "The simple rule beats ML" is a reportable result.
   - Winner's curse: the red-state rule was picked by the §4.2 screen on these same data, so its advantage is optimistic. We say so.
6. **Wording.**
   - The conditional effect of a segment is a lower bound on the probability that the match is necessary and sufficient (PNS) [W6].
   - Parts 1 to 3 use the ATE, and Part 5 uses conditional effects [W6, W7: ATE versus ATT].

---

## 9. Recommendation and limitations

Owner: workstream A.

**For the fundraiser**
- Use a 1:1 match. There is no detectable gain from 2:1 or 3:1, but the experiment could only rule out effects larger than the MDE.
- Targeting depends on the §8 results ("beats" is defined in §8 item 5):
  - If the red-state rule beats the random list, recommend prioritizing red-state donors when the match pool is limited, with the ethics caveat.
  - Recommend ML targeting only if the DR list beats the red-state rule. Otherwise, say that ML targeting needs a properly powered test first.
  - The red-state rule was picked on these data, so its advantage is optimistic.
- Report the break-even cost per letter.

**For practitioners** (the go-to verdict, §6.9)
- The verdict is a workflow plus the go-to estimator(s), and it holds only for settings like ours: a rare binary outcome, about 16,000 rows, 8 covariates and the targeting rules we tested.

**Limitations, each with a data reason**
- One organization, in 2005, liberal-leaning, by direct mail. The outcome is rare: data sparsity [W7].
- IV and encouragement designs [W6, W8] do not apply: assignment is the treatment, there is no measured non-compliance, and no variable satisfies the exclusion restriction.
- Mediation and the front door [W5, W6] do not apply: no post-treatment mediator was measured.
- SEM [W8] does not apply: there is no latent construct to measure.
- The g-formula [W7] is not excluded. The point-treatment g-formula is the adjustment formula, which DoWhy regression and the S-learner already implement.
- Bayesian-network structure learning [W9] is replaced by a domain-first DAG (the course's step 1). A short pgmpy hill-climb is an optional extra (§10).
- The census variables do not match the paper, so they are unused.

---

## 10. Scope tiers

**Core** (never cut): §3 to §9 as written.

**Optional** (only if we are ahead at the 12-01 checkpoint). If time runs short they are cut in the order listed, so the first item goes first:
1. Caliper 1:1 PS matching (caliper 0.2 × SD of the logit) with a McNemar test, on A draw 0 [W3, W4].
2. A reference row using the PS as a covariate (PS method 4 [W3]).
3. Linear base-learner rows in the RCT unit test and in scenario B, to show a realizability failure [W7].
4. A hand-computed adjustment formula stratified by `dormant` on C-proxy draw 0 [W5, W6].
5. pgmpy `HillClimbSearch` with BIC: T should have no parent in the RCT and should gain one in a targeted draw [W9].
6. An OrthoForest row in the RCT unit test only [W7].
7. State-clustered SEs for `T:red0`, notebook only.

**Cut now** (one backup sentence each): the hidden-confounder strength sweep, and the computed fractional-factorial design.

---

## 11. Presentation

**Talk plan.** A 9:30 talk in four contiguous speaker blocks (three handoffs), then 2:30 of Q&A. There are 11 numbered content slides; the title and closing slides are not counted.

| # | Slide | Speaker and time |
|---|---|---|
| 1 | The question, and why an experiment is our answer key | 1 (0:00 to 2:00) |
| 2 | Data, population, randomization check (SMD; title "assess randomization across experiment and control") | 1 |
| 3 | The answer key: 4.5 extra donors per 1,000 letters; the ratios do not differ, but the test is underpowered (MDE) | 1 |
| 4 | OSRCT in one diagram ("we hid the randomization but kept the answer") | 2 (2:00 to 4:30) |
| 5 | Naive versus adjusted on A draw 0, with the overlap histogram | 2 |
| 6 | DAG and identification; C's true versus convenient graph | 2 |
| 7 | The scoreboard (compact table and chart) | 3 (4:30 to 7:30) |
| 8 | Failure mapping, and "Would our diagnostics have told us?" | 3 |
| 9 | "Which checks caught C?": refuters versus sensitivity, with the C-proxy line | 3 |
| 10 | Heterogeneity and targeting value | 4 (7:30 to 9:30) |
| 11 | Conclusion in two parts: the go-to verdict, and the fundraiser recommendation with break-even | 4 |
| | Q&A | all (9:30 to 12:00) |

**Deck rules**
- At most **11 content slides**, as above. About 8 backup slides cover:
  - the truth CI and the tie rule;
  - the full scoreboard (with coverage, SE ratio and the C-proxy column);
  - the CI audit;
  - the refuters in C;
  - the RCT unit-test table;
  - the ANCOVA STOP table;
  - the factorial partworths and 2-way interactions;
  - the census mismatch, why no IV/SEM/BN, and the tuning policy.
- The closing slide carries references and one AI-disclosure line.
- The deck is a PowerPoint file co-edited on UChicago OneDrive. Each slide footer carries its course-week tag.
- Speakers need not be the analysts. Names are fixed at the 12-01 checkpoint, and every speaker learns the adjacent block.
- **Timekeeper.** Speaker 1 keeps time after their block and signals at 4:30, at 7:30 (handoff due) and at 9:00 (30 seconds left).

**Zoom**
- D shares the screen and advances the slides for the whole talk; speakers say "next slide". B is the backup sharer and keeps the PPT and a PDF locally.
- Everyone joins 10 minutes early to test screen sharing.

**Rehearsals**
- Three timed rehearsals on Zoom: 12-05 evening; 12-06 (recorded, ending with a cut list); 12-07 before the 21:00 deck freeze (at least one run under 9:30, then a 10-minute mock Q&A).
- If a run is over time, cut slides; do not speak faster.

**Q&A preparation**
- A Q&A bank of 15+ questions by 12-05, each with an owner and a 30-second answer. For example:
  - Is grading reliable when the truth has an SE of 0.13 pp? (§6.9, "Grading error".)
  - Did you tune? (E5d.)
  - Why not IV?
  - Why did `red0` trigger STOP?
  - Why judge intervals by coverage and the SE ratio, rather than with a finite-population correction?

**Deck freeze.** Mon 12-07 21:00 CST. A uploads both files to Canvas by 23:00 and tags `submission`. No edits after the freeze: the submitted deck is the deck we present.

---

## 12. Notebook and repository architecture

### 12.0 Repository setup
- The repo is `RyanChenJung/causal-answer-key`. It is **public** from the first push, and teammates are invited as collaborators.
- Not committed: the Rossmann and flotation data, `docs/course-map.md` (it summarizes the course slides), the team brief and its build script, and all Chinese translations.
- `.gitignore`: `.DS_Store`, `.remember/`, `.venv/`, `__pycache__/`, `.ipynb_checkpoints/`, `.claude/settings.local.json`, `*.env`, `_private/`, `build/`, `results/dev/`, and `data/*` except `!data/karlan_list_2007.dta` and `!data/README.md`.
- Before the first commit, move the data file from `data/karlan_list/karlan_list_2007.dta` to `data/karlan_list_2007.dta`, and the pilot script from `scripts/check_osrct_feasibility.py` to `scripts/pilot/check_osrct_feasibility.py`, so the paths in §3 and §12.1 hold. Without the move, the `data/*` rule silently leaves the data file out of the repo.
- Before the first push, `git ls-files` is checked against an allowlist and shown to the PM.
- The README lists first names and GitHub logins only.

### 12.1 Repository layout
```
causal-answer-key/
├── README.md              overview, setup, team, contribution table, links
├── AGENTS.md              rules for coding agents (ticket workflow, conventions)
├── CLAUDE.md              imports AGENTS.md
├── AI_DISCLOSURE.md       full per-member disclosure (§17)
├── LICENSE                MIT, "Team 7 contributors"
├── pyproject.toml, uv.lock   Python 3.12, pinned; src/answerkey is an installable package
├── data/                  karlan_list_2007.dta + README.md (provenance, SHA-256, CC0)
├── docs/spec.md           this file
├── src/answerkey/toolkit.py   shared core in jupytext percent format
├── notebooks/             one owner per notebook; others contribute by PR
│   ├── 00_intro.ipynb             A
│   ├── 01_answer_key.ipynb        A
│   ├── 02_structure.ipynb         B
│   ├── 03_benchmark.ipynb         C
│   ├── 04_refute_sensitivity.ipynb B
│   ├── 05_heterogeneity.ipynb     D
│   └── 06_conclusion.ipynb        A (D reviews)
├── scripts/               assemble_notebook.py, check_env.py, validate_karlan_list.py, pilot/check_osrct_feasibility.py
├── tests/                 test_osrct.py, test_rct_smoke.py
├── results/               the §12.8 files and figures/ (results/dev/ is git-ignored)
├── build/                 assembled notebook and HTML (git-ignored)
└── .github/               workflows/ci.yml, ISSUE_TEMPLATE/task.md, pull_request_template.md
```

### 12.2 Shared toolkit
`src/answerkey/toolkit.py` holds only the code that several sections share:
- the constants: `CORE_COVARIATES`, `FEATURES`, `FROZEN`, `TRUTH_PP`, `TRUTH_SE_PP`, `TIE_BAND_PP` and the data path and SHA-256;
- `load_data()`, which reads `pd.read_stata(path, convert_categoricals=False)`, asserts the SHA-256 and prints it;
  - The factor codes are: `ratio` 0 = control, 1 to 3 = 1:1 to 3:1; `size` 0 = control, 1 = $25k, 2 = $50k, 3 = $100k, 4 = unstated; `ask` 0 = control, 1 = 1x, 2 = 1.25x, 3 = 1.5x.
  - With the default categoricals, the empty "Control" level makes the §4.3 design rank-deficient, and statsmodels only warns.
- the feature matrix;
- the OSRCT sampler;
- `ClippedClassifier` (§6.6);
- the estimator functions, including the reference rows and E5d;
- the scoring functions;
- the plotting style (owned by D).

It is written in jupytext percent format, with one function per cell and a markdown cell above each one that says what it does. It defines `__all__`.

**Import cell.** During development, each section notebook from `01_answer_key` to `06_conclusion` has exactly one cell tagged `toolkit-import`. `00_intro` uses no toolkit code and has no such cell.
- It holds `from answerkey.toolkit import *` and, in `02_structure` to `06_conclusion`, `df = load_data()`.
- Section notebooks call toolkit functions by bare name. Calls like `tk.f()` or `answerkey.toolkit.f()` are forbidden, because they break after assembly.
- Sections never modify `df` in place.
- CI greps every section notebook for `answerkey` outside the tagged cell.

All other analysis is written directly in the section notebooks.

### 12.3 Assembly into the submitted notebook
`scripts/assemble_notebook.py` builds the submitted notebook:
1. It starts with `00_intro`.
2. It converts `toolkit.py` into a **"Shared toolkit"** section.
3. It appends the section notebooks in order, deleting their `toolkit-import` cells.
4. It writes `build/Team7_AnswerKey.ipynb`.
   - With `--execute --html` (local, §12.7), it executes the notebook in a fresh kernel and writes `build/Team7_AnswerKey.html`.
   - With `--no-execute` (CI), it only builds. CI fails if any code cell matches `\b(import|from)\s+answerkey\b`.

**Final sections and their sources**

| Final section | Source |
|---|---|
| 0. Title, the question, contents, versions, AI-disclosure line | `00_intro` |
| 1. Shared toolkit | `toolkit.py` (inserted by the script) |
| 2. Data (loads the file, prints the SHA-256, population statement) | `01_answer_key`, first part |
| 3. Answer key | `01_answer_key` |
| 4. Causal structure | `02_structure` |
| 5. Benchmark | `03_benchmark` |
| 6. Refutation and sensitivity | `04_refute_sensitivity` |
| 7. Heterogeneity | `05_heterogeneity` |
| 8. Go-to verdict and recommendation (ends with an explicit Conclusions cell) | `06_conclusion` |
| 9. Limitations | `06_conclusion` |
| 10. References | `06_conclusion` |

The question comes before the toolkit, so the reader sees what we ask before the helper code. Section 0's contents list says that section 1 is a reference to come back to.

### 12.4 Readability rules
- Each code cell is about 40 lines or fewer and is preceded by a sentence saying what it does.
- Each section opens with the question it answers and ends with a one-sentence conclusion.
- No warnings or install output appear in the HTML.
  - Section 0 calls `warnings.filterwarnings("ignore", category=SyntaxWarning)` and `warnings.filterwarnings("ignore", category=FutureWarning)` before any other import.
  - EconML and CausalML always receive numpy arrays, which avoids LightGBM's feature-name warnings.
- Tables are rounded (§13). Figures are static matplotlib.
- Section headers carry course-week tags.
- Three short "bridge" cells connect the methods to the course:
  - FWL: the OLS treatment coefficient equals the residual-on-residual regression, and DML is the same idea with ML nuisance models and cross-fitting [W1 → W7].
  - Hand-computed DML: θ = Σ(Y−ĝ)(T−m̂) / Σ(T−m̂)² next to E9.
  - Hand-computed AIPW: the mean ± 1.96·SD/√n next to E8.
- One-line notes cover:
  - SMD;
  - why a regressor is used on a 0/1 outcome;
  - the recency merge;
  - GCM versus HSIC;
  - Type I ≈ Type II;
  - HC2;
  - the A3-style BIC.

### 12.5 The benchmark inside the notebook
- The 50-draw loop's code is fully shown in section 5.
- `RUN_MODE` is read from the environment variable of the same name and defaults to `"dev"`.
  - `"dev"` runs draws 0 to 2 of every scenario (A, B, C, C-proxy) and writes `results/dev/benchmark_draws_dev.csv`, which is git-ignored. It never writes the production cache.
  - `"full"` computes all 200 units and the §6.11 RCT unit, resuming from `results/benchmark_draws.csv`. The production run uses it.
  - `"cache"` loads `results/benchmark_draws.csv` and never adds units, even when the §6.12 fallback left the cache incomplete. Its only computation is the recheck of draws 0 to 2 below. The export uses it.
- The export run prints "loaded <k>/200 units generated by this code at commit <hash> on <date>, runtime <min>".
- It then recomputes draws 0 to 2 of scenario A and asserts `np.allclose(new, cached, rtol=0, atol=1e-9, equal_nan=True)` on `estimate_pp`, `ci_lo_pp` and `ci_hi_pp`. Blank CI cells are read as NaN, so `equal_nan=True` is needed.
- Bit-level agreement is expected only on the same machine, so the export runs on the production Mac.

### 12.6 Numbers flow to slides
- Every number on a slide comes from `results/key_numbers.csv`, and every figure is a fixed-name 16:9 PNG in `results/figures/` (§12.8).
- After the numbers freeze, a non-author checks every slide number against the CSV.

### 12.7 HTML export rules
- On the production Mac, use a clean `UV_COMPILE_BYTECODE=1 uv sync --frozen` environment, then run `RUN_MODE=cache uv run python scripts/assemble_notebook.py --execute --html`. Executing in a fresh kernel is the same as Restart & Run All.
- Precompiling the bytecode stops DoWhy's first import from printing SyntaxWarnings.
- The first code cell prints the Python and package versions. Section 2's `load_data()` prints the data SHA-256.
- Section 8 ends with an explicit Conclusions cell, and the notebook ends with References.

### 12.8 Results contract
All effects are stored in pp. This contract is how the sections talk to each other; renaming a file or column needs the owner of every section that reads it.

- `results/osrct_draws.npz` (`np.savez_compressed`):
  - `p_A`, `p_B`, `p_C`: float64, shape (48899,);
  - `keep_A`, `keep_B`, `keep_C`: bool, shape (50, 48899);
  - `draw_seed`: uint32, shape (3, 50).
  - Positions refer to the §6.4 row order.
- `results/benchmark_draws.csv`: one row per (scenario, draw, estimator).
  - Columns: `scenario` (A, B, C, Cproxy, RCT), `draw`, `draw_seed`, `estimator` (R0 to R2, E1 to E12, E5d), `estimate_pp`, `ci_lo_pp`, `ci_hi_pp`, `se_pp`, `n_kept`, `n_treated`, `runtime_s`, `git_hash`.
  - The CI and SE columns are blank for methods without a CI. For candidates, `se_pp = (ci_hi_pp - ci_lo_pp) / (2 × 1.959964)`.
- `results/diagnostics_draws.csv`: `scenario, draw, share_ps_outside, max_abs_smd_ipw, ps_auc_cv, brier_ratio_cv`.
- `results/refuters.csv`: `scenario, estimator, refuter, n_sims, estimate_pp, new_effect_pp, sd_sims_pp, threshold_pp, p_value, passed`.
- `results/sensitivity_C0.csv`: `estimator, benchmark, k, r2tu_w, r2yu_tw, adj_estimate_pp, rv, rv_alpha`.
- `results/run_log.json`: git hash, package versions, machine, `n_workers`, start, end, runtime.
- `results/key_numbers.csv`: columns `key, value, unit, source`.
  - The unit is one of `pp`, `per1000`, `usd`, `p`, `pct`, `n`, `ratio`, `id`. The `id` unit is used only by `goto_ids`, whose value lists the go-to estimator IDs, primary first.
  - Keys (snake_case): `truth_ate_pp`, `truth_se_pp`, `truth_ci_lo_pp`, `truth_ci_hi_pp`, `tie_band_pp`, `ate_all_rows_pp`, `ate_dollars_usd`, `break_even_usd`, `ancova_ate_pp`, `holm_p_t_red0`, `joint_f_p`, `contrast_2v1_pp`, `contrast_3v1_pp`, `mde_ratio_pp`, `n_needed_019pp`, `mde_interaction_pp`, `effect_red_pp`, `effect_blue_pp`, `red_letter_share_pct`, `red_donor_share_pct`, `naive_<scen>_pp`, `bias_<scen>_<id>_pp`, `rmse_<scen>_<id>_pp`, `cov_<scen>_<id>_pct`, `seratio_<scen>_<id>`, `goto_ids`, `rv_e1_c0`, `rv_alpha_e1_c0`, `rv_e9_c0`, `list_value_<dr|red|random>_per1000`.
  - New keys may be added by PR.
- **Figures** (`figsize=(13.33, 7.5)`, dpi 150, PNG, in `results/figures/`): `fig01_osrct_diagram`, `fig02_overlap_A0`, `fig03_dag_rct`, `fig04_dag_C_true_vs_convenient`, `fig05_scoreboard`, `fig06_diagnostics_crosstab`, `fig07_sensitivity_C0`, `fig08_red_blue`, `fig09_policy_lists`, `fig10_balance_smd`, `fig11_ratio_partworths`, `fig12_overlap_by_scenario`. New figures may be added by PR; renaming one needs D's OK.

---

## 13. Engineering conventions

- **Environment.** Python 3.12 with `uv` and a committed `uv.lock`, pinning `dowhy==0.14`, `econml==0.17.1` and `causalml==0.15.5` (Appendix B explains why). Everyone is on a Mac. Colab pinned to 3.12 is the fallback. Use `UV_COMPILE_BYTECODE=1` for clean installs. Scripts set `matplotlib.use("Agg")`.
- **Seeds.** §6.4. All other randomness uses fixed seeds that are documented where used.
- **Rounding.** Effects in pp to 2 decimals, donors per 1,000 to 1 decimal, p-values to 3 decimals, dollars to 2 decimals. Pre-registered constants (§3) are stored and used at full precision; only their display follows these rules.
- **Git**
  - Branches are named `<issue#>-<slug>`. The PR body says `Closes #N`. Use squash merge.
  - `main` is protected: changes arrive only through a PR, CI must pass, and force pushes are blocked. No approval is required.
- **Review policy**
  - Review is optional, and authors may merge their own PRs once CI passes.
  - Tag your review partner (B↔C, A↔D) when a PR touches `toolkit.py`, frozen settings, or anything that feeds the final numbers. If there is no response in 12 hours, merge.
  - Exception: any amendment to this spec needs approval from two teammates (§18).
- **CI** (GitHub Actions, set up by the PM in M0):
  - `uv sync --locked`;
  - a check that no notebook outputs are committed (nbstripout);
  - `pytest tests/` (the OSRCT sampler invariants, and the RCT smoke table with every estimator within `TIE_BAND_PP` of `TRUTH_PP`);
  - a grep of every section notebook for `answerkey` outside the `toolkit-import` cell;
  - `assemble_notebook.py --no-execute`, then the check for no `answerkey` import (§12.3).
- **Pre-commit:** `nbstripout`. Each member sets their git email to their GitHub noreply address.
- **Definition of done**
  1. Merged.
  2. The section runs from a clean `uv sync --frozen`.
  3. Numbers and figures are written to `results/` under the §12.8 names.
  4. The section opens with its question and ends with a conclusion.
  5. The matching slide draft is updated, or an Issue is opened.
  6. AI use is noted in the PR body.

---

## 14. Ticket workflow (GitHub Issues only)

We do not use a Project board. Issues are the single source of truth, and coding agents read them with `gh`. The full agent rules are in `AGENTS.md`, which is written during repo setup.

- **Everyone** upgrades `gh` to 2.94 or later (`brew upgrade gh`; 2.105 at the time of writing). This version adds `--blocked-by`, `--parent` and the JSON fields `blockedBy`, `parent`.
- **Initial tickets.** The PM drafts the first ~25 tickets with hour estimates and dependencies.
- **Dependencies** use native "blocked by" links. **Sub-issues** split parent tickets.
- **Estimates** use exactly one label per leaf ticket: `est:1h`, `est:2h`, `est:3h`, `est:5h` or `est:8h`.
  - Anything over 8 hours is split.
  - Parents carry no estimate.
  - Each ticket has one assignee.
- **Labels:** `ws:A`, `ws:B`, `ws:C`, `ws:D`, `infra`, `deck`, `admin`.
- **Milestones:** see §16.
- **Commands an agent uses:**
  - To find its next ticket: `gh issue list --assignee @me --search "is:open -is:blocked"`.
  - To claim one: assign itself first, re-check the assignees, then comment its plan.
  - To start work: `gh issue develop N --checkout`.
- **Hours per person.** Whoever has the fewest open hours takes the next unassigned ticket. This command lists open hours per person:

```bash
gh issue list --state open --limit 500 --json assignees,labels --jq '[.[] | {who: (.assignees[0].login // "unassigned"), h: ([.labels[].name | select(startswith("est:")) | ltrimstr("est:") | rtrimstr("h") | tonumber] | add // 0)}] | group_by(.who) | map({who: .[0].who, open_hours: (map(.h) | add)}) | sort_by(.open_hours)'
```

---

## 15. Workstreams and roles

| Stream | Scope |
|---|---|
| **A** Answer key and integration | §4; §9; the `00_intro` and `06_conclusion` notebooks; the shared toolkit `toolkit.py` (D owns its plotting functions); the assembly script; `key_numbers.csv`; the final notebook; the submission checklist and the Canvas upload |
| **B** Structure and checks | §5; §7; the diagnostics cross-tab (§6.10). Pairs with C on the DoWhy code (E1 to E4, R2, the refuters). |
| **C** Benchmark (critical path) | §6.1 to §6.9, §6.11, §6.12: the sampler, the estimators, the draw-level diagnostics and the production run. C does not build figures or the deck. |
| **D** Heterogeneity and deck | §8; the scoreboard table and figure (§6.13); the other §6 figures (`fig01_osrct_diagram`, `fig02_overlap_A0`, `fig12_overlap_by_scenario`), built from C's saved results; the CI audit table; the plot style (the toolkit's plotting functions); deck lead; screen sharer |

**Roster.** Stream leads, review partners and Zoom roles are filled when tickets are assigned, before `spec-v1`. Speaker blocks are filled at the 12-01 checkpoint (§11).

| Member | GitHub login | Stream lead | Review partner | Speaker block | Zoom role |
|---|---|---|---|---|---|
| Ryan | `RyanChenJung` | | | | |
| Adi | `asingh49-cmd` | | | | |
| Hoon | `jhoonyum` | | | | |
| Yuta | `yutakoba120` | | | | |

- **Stream leads.** A stream lead owns that stream's notebooks and decides inside the stream. Individual tickets can go to any member, by open hours (§14).
- **Roles.** Ryan is PM: he runs the Issues and the cadence, and breaks ties on cross-stream questions after 24 hours without consensus.
- **Backups.** The integrator's backup is C, who is free after the 12-04 numbers freeze. The deck's backup is B. Both backups do one assembly dry run by 12-05, on the production Mac or with `--no-execute`.
- **Balance.** Tickets are assigned by estimated hours, so that totals are balanced. Ryan's share is slightly lighter, because the pilot, the validation, this spec and the repo setup are already done.

---

## 16. Schedule and milestones (CST)

| Date | Event |
|---|---|
| Tue 11-24 | Spec drafted |
| **Wed 11-25** | Repo created; tickets drafted and assigned; **objections close 23:59; spec lock, tag `spec-v1`** |
| Thu 11-26 to Sun 11-29 | Thanksgiving. The only hard task, by **Sun 11-29 20:00**: accept the repo invite, clone, run `UV_COMPILE_BYTECODE=1 uv sync --frozen`, run `scripts/check_env.py`, and post its output on the onboarding issue. Critical-path tickets go to whoever is available. |
| Mon 11-30 | 30-minute Zoom kickoff; environment troubleshooting |
| **Tue 12-01** | **Checkpoint.** Every section notebook runs end to end with `RUN_MODE="dev"`; smoke-test timings are in; the slide outline and speakers are fixed; the production Mac is named (it is also the export machine, §12.5); decide on the optional items |
| **Thu 12-03** | **Code freeze**; the production run starts that night; 30-minute sync |
| **Fri 12-04** | **Numbers freeze** (tag `results-v1`) from the cache; `key_numbers.csv` written. Unmerged optional work is dropped. An unmerged core item blocks the numbers freeze and goes to the PM. |
| Sat 12-05 | Assembled notebook re-executed from the cache and exported to HTML; backups' assembly dry run; full deck draft; Q&A bank; AI-disclosure paragraphs; rehearsal 1 in the evening |
| Sun 12-06 | Rehearsal 2 (recorded) |
| Mon 12-07 | Rehearsal 3 and mock Q&A before 21:00; **deck freeze 21:00**; **Canvas upload by 23:00** |
| **Tue 12-08** | **Presentation** |

**GitHub milestones**
- M0 Setup (due 11-29)
- M1 Skeleton (12-01)
- M2 Code freeze (12-03)
- M3 Numbers freeze (12-04)
- M4 Deliver (12-07)

**Cadence**
- A daily async check-in in the group chat: done / next / blocked.
- Reply within 12 hours; a blocker that @-mentions someone gets a reply within 6 hours.
- Flag an expected slip at least 24 hours ahead. No blame.

**Slip rules**
- An in-progress ticket with 48 hours of silence gets a PM check-in.
- A core stream without a running skeleton at 12-01 gets a paired teammate.
- Cut order: the optional items (§10) in the order listed, caliper matching first. Core is never cut.

---

## 17. Submission and AI disclosure

**Files:** `Team7_AnswerKey.html` and `Team7_AnswerKey.pptx`. After the 21:00 deck freeze on Mon 12-07, A uploads both to Canvas by 23:00 CST, tags the source commit `submission`, and posts a screenshot of the upload in the chat.

**AI disclosure** (the syllabus requires it within each submitted assignment):
- `AI_DISCLOSURE.md` in the repo holds each member's paragraph: tools and versions, what they were used for, and how the output was verified ("all numbers reproduced by running the code ourselves"). Each member adds theirs by PR by 12-05.
- The notebook (one cell in section 0) and the closing slide each carry one line listing the tools by product name and version, with a link to `AI_DISCLOSURE.md`.

**Final checklist** (run by A, checked by the PM)
1. On the production Mac: clean environment; assemble with `--execute --html` (§12.7). If A does not own that Mac, its owner runs this step with A.
2. HTML opened offline in a second browser: figures, disclosure and data source present.
3. File names correct.
4. Upload by 23:00; tag `submission`; screenshot.

**References** go at the end of the notebook and on the closing slide (§19).

---

## 18. Amendments

After `spec-v1`, any change to this spec needs:
- a dated reason, approval from two teammates, and a PR that edits this section;
- to land **before** the production run on 12-03.

After the run, **[pre-registered]** items never change. Any departure is reported as a deviation in the notebook, never as a rule edit.

Slide wording: *"Go-to rule pre-registered 2026-11-25 (tag `spec-v1`), written after a 10-draw pilot, verification runs of 20 to 400 draws and an API check, and before the 50-draw run."*

**Pre-lock revisions.** These were changed after the pilot and checks, before `spec-v1`. We list them for transparency:
- Scenario C targets `log1p(mrm2)` instead of raw `mrm2`, so that overlap problems do not mix into the hidden-confounding test. C hides both `mrm2` and `dormant`, because `dormant` is a proxy for recency.
- The ANCOVA uses the complete cases and the raw covariates.
- The package pins changed to the combination in Appendix B.
- The power numbers were recomputed: MDE 0.54 pp, n ≈ 88,000, interaction MDE 0.74 pp.
- Coverage: the √(1 − f) finite-population correction was replaced by raw coverage plus an SE-ratio band, because OSRCT keeps people with unequal probabilities.
- The tie rule, the least-bad fallback, the refuter pass rules and the diagnostic thresholds were written out explicitly.

**Amendments after the lock**

| Date | Change | Reason | Approved by |
|---|---|---|---|
| | | | |

---

## 19. References

- Karlan, D. and List, J. A. (2007). Does Price Matter in Charitable Giving? Evidence from a Large-Scale Natural Field Experiment. *American Economic Review*, 97(5), 1774 to 1793. Data: Harvard Dataverse, doi:10.7910/DVN/27853 (CC0 1.0).
- Gentzel, A. M., Pruthi, P. and Jensen, D. (2021). How and Why to Use Experimental Data to Evaluate Methods for Observational Causal Inference. *ICML 2021*, PMLR 139, 3660 to 3671.
- LaLonde, R. J. (1986). Evaluating the Econometric Evaluations of Training Programs with Experimental Data. *American Economic Review*, 76(4), 604 to 620.
- Lin, W. (2013). Agnostic Notes on Regression Adjustments to Experimental Data. *Annals of Applied Statistics*, 7(1), 295 to 318.
- Cinelli, C. and Hazlett, C. (2020). Making Sense of Sensitivity: Extending Omitted Variable Bias. *JRSS-B*, 82(1), 39 to 67.
- Chernozhukov, V., Cinelli, C., Newey, W., Sharma, A. and Syrgkanis, V. (2022). Long Story Short: Omitted Variable Bias in Causal Machine Learning. NBER Working Paper 30302.
- Morris, T. P., White, I. R. and Crowther, M. J. (2019). Using Simulation Studies to Evaluate Statistical Methods. *Statistics in Medicine*, 38(11), 2074 to 2102.
- Software: DoWhy, EconML, CausalML, LightGBM, statsmodels and scikit-learn, at the versions in Appendix B.
- Course: ADSP 32029 lecture notes, Weeks 1 to 9 (cited as [W#]; lists are paraphrased with attribution).

---

## Appendix A. Pilot results (pilot; never report as results)

| Pilot | Result |
|---|---|
| 10 draws, hand-written scikit-learn estimators, older scenario definitions (`scripts/pilot/check_osrct_feasibility.py`) | The naive estimate was 3 to 4 times the truth. DR, DML, T and X had the smallest bias when the confounders were observed. IPW broke under extreme propensities. The S-learner lost about half the effect under nonlinear targeting. |
| Verification runs (20 to 400 draws, fast estimators only; the naive ratios are exact expectations) | Under the current definitions the naive estimate is 3 to 4.4 times the truth. With recency fully hidden (C), the bias is +0.64 pp (OLS) and about +0.7 pp (IPW). With `dormant` kept (C-proxy), about 60% of that bias is removed and about +0.3 pp remains; an earlier figure of +0.14 to +0.18 pp came from the older raw-`mrm2` targeting. In B, the misspecified-logit IPW and OLS had a bias of about −0.05 to −0.08 pp. Under scenario A, OLS on raw features had +0.36 pp bias, against +0.03 pp on log features. |
| Coverage check (300 to 400 draws of OLS, oracle IPW, DR and partially linear estimators; 160 draws of a cross-fitted LightGBM DR in A) | A LightGBM DR estimator like E8 was nearly unbiased in A, with raw coverage 96.3%. With the √(1 − f) correction its coverage fell to 90.6%. The empirical SD was 0.7 to 0.9 times the mean reported SE in B and C, and 0.86 to 1.2 in A, depending on the method. |
| ANCOVA (complete cases) | Only `T:red0` survives Holm (adjusted p = 0.013). The joint F p is 0.069 on raw covariates and 0.024 on log features. The step-2 `T` coefficient is 0.442 pp. |

## Appendix B. Package API facts (verified 2026-11-24 and 2026-11-25)

These were checked on synthetic data and on our file in a clean Python 3.12.13 environment on Apple silicon. Re-verify any path that the smoke test (§6.12) exercises differently.

**Pinned versions**

| Package | Version |
|---|---|
| dowhy | 0.14 |
| econml | 0.17.1 |
| causalml | 0.15.5 |
| lightgbm | 4.7.0 |
| scikit-learn | 1.9.1 |
| numpy | 2.4.6 |
| pandas | 3.1.1 |
| scipy | 1.15.3 |
| statsmodels | 0.15.0 |
| pgmpy | 1.1.2 |

**Why this combination**
- `dowhy>=0.14` requires `scipy<=1.15.3` on Python 3.12, while `causalml>=0.16` requires `scipy>=1.16`, so the two are incompatible.
- The alternative, `dowhy==0.12` with `causalml==0.18.0`, installs but fails at `identify_effect` with current networkx (`networkx.algorithms.d_separated` was removed).
- `causalml==0.15.5` depends on `pydotplus`, which ships only a pure-Python source package. uv builds it automatically; no compiler is needed.
- On Python 3.13, causalml has no wheels at all.

**Call paths that worked**

DoWhy:
- Model construction for §6: `CausalModel(data=..., treatment=..., outcome=..., common_causes=[...])`, with no `graph=` (§6.5).
- Linear regression: `CausalModel.estimate_effect(estimand, method_name="backdoor.linear_regression", confidence_intervals=True)`. `.get_confidence_intervals()` gives the non-robust CI.
- Propensity-score methods, all with `target_units="ate"` and `method_params={"propensity_score_model": <sklearn estimator>, ...}`:
  - weighting: `weighting_scheme="ips_normalized_weight", min_ps_score=0.01, max_ps_score=0.99`;
  - stratification: `num_strata=5, clipping_threshold=1` (the default threshold is 10);
  - matching: defaults.
  - The defaults, used only by R2, are `LogisticRegression()`, `weighting_scheme="ips_weight"` and clipping at [0.05, 0.95].
- DoWhy route to EconML: `method_name="backdoor.econml.dml.LinearDML"` or `"backdoor.econml.dr.LinearDRLearner"`, with `effect_modifiers=<adjustment set>` and `method_params={"init_params": {...}, "fit_params": {}}`. Without `effect_modifiers`, X is None and LinearDML returns the overlap-weighted coefficient, not the ATE.
- Refuters, each with `num_simulations=` and `random_seed=`: `placebo_treatment_refuter` (`placebo_type="permute"`), `random_common_cause`, `data_subset_refuter` (`subset_fraction=0.8`).
- Sensitivity: `refute_estimate(..., method_name="add_unobserved_common_cause", simulation_method="linear-partial-R2", benchmark_common_causes=[<one column>], effect_fraction_on_treatment=[1, 2, 3], plot_estimate=False)`.
  - Pass one benchmark per call. DoWhy 0.14 loops over the benchmarks but overwrites its bounds on each pass, so only the last survives.
  - It returns a `LinearSensitivityAnalyzer`. The `.stats` keys are `estimate`, `standard_error`, `degree of freedom`, `t_statistic`, `r2yt_w`, `partial_f2`, `robustness_value` and `robustness_value_alpha`.
  - It calls `plt.show()`, so use the Agg backend.
- Graph refutation: `dowhy.gcm.falsify.falsify_graph(causal_graph, data, suggestions=False, independence_test=..., conditional_independence_test=..., significance_level=0.05, n_permutations=..., n_jobs=..., plot_histogram=False, allow_data_subset=True)`.
  - There is no seed argument; call `dowhy.gcm.util.general.set_random_seed(seed)` first.
  - `allow_data_subset` means "graph nodes without a data column are allowed", not row subsampling. We set it to `False`.
  - The GCM test is `dowhy.gcm.independence_test.generalised_cov_measure.generalised_cov_based`. The default test is the kernel test.
- The first `import dowhy` in a fresh environment prints SyntaxWarnings unless the bytecode was precompiled (`UV_COMPILE_BYTECODE=1`).

EconML:
- Every `cv=` gets a splitter object: `cv=StratifiedKFold(5, shuffle=True, random_state=seed)`.
- `LinearDML(model_y=..., model_t=..., discrete_treatment=True, cv=..., random_state=...)`: `.ate(X)`, `.ate_interval(X, alpha=0.05)`, `.robustness_value(alpha=0.05)`.
- `LinearDRLearner(model_propensity=..., model_regression=..., min_propensity=0.01, cv=...)`: `.ate(X, T0=0, T1=1)`, `.ate_interval(X, T0=0, T1=1, alpha=0.05)`. The default `min_propensity` is 1e-06.
- `CausalForestDML(..., discrete_treatment=True, n_estimators=..., min_samples_leaf=..., max_samples=..., honest=True, cv=..., n_jobs=1)`: `.ate__inference()` gives `.point_estimate`, `.stderr` and `.conf_int(alpha)`. `drate=True` is the default. The default `n_jobs` is −1 (all cores). `.ate_interval(X)` also runs, but its interval was about twice as wide as the `ate__inference()` interval, so we do not use it (§6.7).
- `SLearner(overall_model=...)`, `TLearner(models=...)`, `XLearner(models=..., propensity_model=..., cate_models=...)`: `.fit(Y, T, X=X).ate(X)`. `XLearner.fit(Y, T, *, X, inference=None)` has no argument for a precomputed propensity; it clones `propensity_model` and fits it in-sample.
- `econml.validate.DRTester` exists, but we do not use it.

CausalML:
- `BaseXRegressor(learner=LGBMRegressor(...)).estimate_ate(X, T, y, p=e_hat)`.
- `r = BaseRRegressor(learner=..., n_fold=5, random_state=seed)`, then `r.cv_n_jobs = 1`, then `r.estimate_ate(X, T, y, p=e_hat)`. The constructor rejects `cv_n_jobs` (TypeError); the attribute defaults to −1 (all cores).
- Both return `(ate, lower, upper)`. Use the first element only. In 0.15.5 the R-learner's SE is divided by n instead of √n, so its bounds are far too narrow.

scikit-learn and pandas:
- Unpenalized logistic regression is `LogisticRegression(C=np.inf)`. `penalty=None` prints a FutureWarning in scikit-learn 1.9.1.
- `pd.read_stata(path, convert_categoricals=False)` keeps `ratio`, `size` and `ask` as numeric codes (§12.2).
