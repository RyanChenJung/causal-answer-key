"""Check the notebook rules from docs/spec.md §12.2, §12.3 and §13. CI runs this on every push.

Section notebooks (notebooks/*.ipynb):
- no committed outputs or execution counts;
- 00_intro has no `toolkit-import` cell; every other notebook has exactly one;
- `answerkey` appears only inside the `toolkit-import` cell.

Assembled notebook (pass its path with --assembled): no code cell imports `answerkey`.

Usage: uv run python scripts/check_notebooks.py [--assembled build/Team7_AnswerKey.ipynb]
"""
import argparse
import re
import sys
from pathlib import Path

import nbformat

TAG = "toolkit-import"
IMPORT_RE = re.compile(r"\b(import|from)\s+answerkey\b")


def check_section(path):
    errors = []
    nb = nbformat.read(path, as_version=4)
    tagged = [c for c in nb.cells if TAG in c.get("metadata", {}).get("tags", [])]
    want = 0 if path.name.startswith("00_") else 1
    if len(tagged) != want:
        errors.append(f"has {len(tagged)} '{TAG}' cells, expected {want}")
    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        if cell.get("outputs") or cell.get("execution_count"):
            errors.append(f"cell {i} has committed outputs (run nbstripout)")
        if "answerkey" in cell.source and TAG not in cell.get("metadata", {}).get("tags", []):
            errors.append(f"cell {i} mentions 'answerkey' outside the '{TAG}' cell")
    return errors


def check_assembled(path):
    nb = nbformat.read(path, as_version=4)
    return [f"cell {i} imports answerkey" for i, c in enumerate(nb.cells)
            if c.cell_type == "code" and IMPORT_RE.search(c.source)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembled", type=Path)
    args = parser.parse_args()
    failed = False
    for path in sorted(Path("notebooks").glob("*.ipynb")):
        for err in check_section(path):
            print(f"{path}: {err}")
            failed = True
    if args.assembled:
        for err in check_assembled(args.assembled):
            print(f"{args.assembled}: {err}")
            failed = True
    print("notebook checks failed" if failed else "notebook checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
