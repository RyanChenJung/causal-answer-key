# Data

`karlan_list_2007.dta` is the replication data for:

> Karlan, D. and List, J. A. (2007). Does Price Matter in Charitable Giving? Evidence from a Large-Scale Natural Field Experiment. *American Economic Review*, 97(5), 1774–1793.

| | |
|---|---|
| Official source | Harvard Dataverse, doi:[10.7910/DVN/27853](https://doi.org/10.7910/DVN/27853) |
| License | CC0 1.0 (public domain dedication) |
| Our copy | The unchanged file mirrored in the public replication repository `embeddedlayers/replication-karlan-list-2007` |
| Size | 5,367,918 bytes |
| SHA-256 | `7d13b9c4394c567a663c9eed27e1212204b65fe284f64edc772d7f61bdb330b5` |

- `load_data()` in `src/answerkey/toolkit.py` checks the SHA-256 every time it reads the file.
- `scripts/validate_karlan_list.py` reproduces the paper's Table 1 donor-history and state variables and every cell of Table 2A: `uv run python scripts/validate_karlan_list.py data/karlan_list_2007.dta`.
- A provenance ticket compares this mirror with the official Dataverse file.
- Variables, known issues and the row rule are in `docs/spec.md` §3.

No other data are committed; `.gitignore` ignores everything else in this folder.
