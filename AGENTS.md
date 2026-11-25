# AGENTS.md

Team 7's causal-inference project. `docs/spec.md` is the source of truth: read its §12 to §15 and Appendix B once, and for every ticket read the spec section the ticket names. When the spec and a ticket disagree, the spec wins; say so in the ticket.

This repo is **public**. Commit code, docs and results only; keep emails, tokens and anything personal out of commits, issues and PRs.

## Ticket loop

Work one ticket at a time, in this order. Each step ends when its *done* condition holds.

1. **Find.** `gh issue list --assignee @me --search "is:open -is:blocked"`. If that is empty, run the hours command below; the member with the fewest open hours takes the next unassigned unblocked ticket. Propose it to your human before claiming. *Done: one ticket chosen.*
2. **Claim.** `gh issue edit N --add-assignee @me`, then `gh issue view N --json assignees` to confirm you are the only assignee, then comment a 3 to 5 line plan. *Done: sole assignee and plan posted.*
3. **Branch.** `gh issue develop N --checkout --name N-<slug>`. *Done: on branch `N-<slug>`.*
4. **Build.** Implement what the ticket and its spec section say, following the conventions below. *Done: every box under the ticket's "Done when" is true and the spec §13 definition of done holds.*
5. **Verify.** `uv run pytest -q` and `uv run python scripts/check_notebooks.py` pass, and any notebook you touched runs top to bottom with `RUN_MODE=dev`. *Done: all green, outputs stripped.*
6. **PR.** `gh pr create --fill`, fill the template, `Closes #N`. Tag the review partner (spec §13) when the PR touches `toolkit.py`, frozen settings or anything that feeds the final numbers. Squash-merge once CI passes; a tagged partner gets 12 hours. *Done: merged, issue closed.*

**Blocked?** Comment on the issue with what you need and @-mention the person, then move to another ticket.

## Conventions

- **Toolkit import.** In `notebooks/01_*` to `06_*`, exactly one cell is tagged `toolkit-import` and holds `from answerkey.toolkit import *` (plus `df = load_data()` in `02_*` to `06_*`). Call toolkit functions by bare name. Anything shared by two or more sections goes in `src/answerkey/toolkit.py`, added to `__all__`, one function per cell with a markdown line above it (spec §12.2).
- **Results contract.** Write only the files, columns, keys and figure names in spec §12.8; effects are in pp. Every number on a slide comes from `results/key_numbers.csv`.
- **Seeds.** Take every seed from spec §6.4 (or the section's stated seed). Every random call gets an explicit seed.
- **Frozen settings.** `FROZEN` and the estimator settings in spec §6.5 to §6.7 are pre-registered. Use them exactly; tuning is out of scope.
- **Package gotchas.** Before calling a DoWhy, EconML or CausalML API, check spec Appendix B: several defaults there silently give wrong answers.
- **Headless runs.** Set `MPLBACKEND=Agg` (DoWhy's sensitivity analysis hangs on macOS otherwise) and keep `n_jobs=1` in estimators.
- **Notebooks.** The pre-commit hook strips outputs; commit notebooks without outputs.
- **Data.** Read data only through `load_data()`; the only committed data file is `data/karlan_list_2007.dta`.
- **Spec changes.** Any edit to `docs/spec.md` is an amendment: a PR that also adds a row to the §18 table, approved by two teammates, merged before the production run.

## Hours command

Open hours per person, from the `est:Nh` labels (spec §14):

```bash
gh issue list --state open --limit 500 --json assignees,labels --jq '[.[] | {who: (.assignees[0].login // "unassigned"), h: ([.labels[].name | select(startswith("est:")) | ltrimstr("est:") | rtrimstr("h") | tonumber] | add // 0)}] | group_by(.who) | map({who: .[0].who, open_hours: (map(.h) | add)}) | sort_by(.open_hours)'
```

## Dependencies

Tickets use GitHub's native "blocked by" links and sub-issues. `gh` 2.94+ shows them (`gh issue view N --json blockedBy,parent`); upgrade with `brew upgrade gh`. To add a link with any `gh` version:

```bash
gh api -X POST repos/RyanChenJung/causal-answer-key/issues/N/dependencies/blocked_by -F issue_id=$(gh api repos/RyanChenJung/causal-answer-key/issues/M --jq .id)
```

This records "N is blocked by M".
