# Answer Key

**Grading causal methods against a fundraising experiment.**
Team 7 final project for ADSP 32029 Causal Models in Data Science (University of Chicago, Fall 2026).

Karlan and List (2007) randomized a matching-grant offer across 50,083 past donors, so we know the true effect of the offer. We hide the randomization by sampling observational-looking data from the experiment (OSRCT), run the course's DoWhy, EconML and CausalML estimators on it, and grade each one against the true effect. The result is our pre-registered answer to "which methods would be our go-to methods for causal effect estimation in real life?".

- **Spec:** [`docs/spec.md`](docs/spec.md) is the source of truth for scope, methods, rules and schedule.
- **Working on a ticket:** [`AGENTS.md`](AGENTS.md).
- **Deliverables:** a 12-minute talk on Zoom on Tue 2026-12-08, plus the PPT and the HTML of one notebook on Canvas.

## Team

| Member | GitHub | Stream |
|---|---|---|
| Ryan (PM) | [@RyanChenJung](https://github.com/RyanChenJung) | TBD |
| Adi | [@asingh49-cmd](https://github.com/asingh49-cmd) | TBD |
| Hoon | [@jhoonyum](https://github.com/jhoonyum) | TBD |
| Yuta | [@yutakoba120](https://github.com/yutakoba120) | TBD |

## Setup (macOS, Apple silicon)

1. Install [uv](https://docs.astral.sh/uv/) (`brew install uv`) and the GitHub CLI 2.94 or later (`brew install gh` or `brew upgrade gh`).
2. Clone and install the locked environment:
   ```bash
   gh repo clone RyanChenJung/causal-answer-key
   cd causal-answer-key
   UV_COMPILE_BYTECODE=1 uv sync --frozen
   ```
3. Check your machine and post the full output on the onboarding issue:
   ```bash
   uv run python scripts/check_env.py
   ```
4. Install the pre-commit hook (it strips notebook outputs) and use your GitHub noreply email for commits in this repo:
   ```bash
   uv run pre-commit install
   git config user.email "<id>+<login>@users.noreply.github.com"
   ```
   Your noreply address is under GitHub Settings → Emails.

Python 3.12 is required; uv installs it. EconML 0.17.1 has no prebuilt wheel for Intel Macs, so an Intel Mac needs the Colab fallback (spec §13).

## Layout

See spec §12.1. In short: `src/answerkey/toolkit.py` holds the shared code, `notebooks/` holds one notebook per section, `scripts/assemble_notebook.py` builds the single submitted notebook, and `results/` holds the cached benchmark draws, key numbers and figures.

## Contributions

Filled in before submission from the closed issues and merged PRs.

| Member | Main contributions |
|---|---|
| Ryan | |
| Adi | |
| Hoon | |
| Yuta | |

## AI use

See [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md).

## License and data

Code: MIT (see [`LICENSE`](LICENSE)). Data: CC0 1.0, from Harvard Dataverse (see [`data/README.md`](data/README.md)).
