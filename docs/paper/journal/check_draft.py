"""Pre-submission checks for the JSS draft. Read-only; no dependencies.

Run from docs/paper/journal/ with any Python 3:

    python check_draft.py

Reports:
  * abstract length against JSS's 250-word limit (any \\CSEVEN placeholder is
    excluded from the count; none remain since 2026-10-13);
  * highlights against JSS's limits (3-5 bullets, <= 85 characters each);
  * placeholders still open (\\CSEVEN for the second-model run, \\TODO for
    author decisions), per file;
  * \\cite keys missing from references.bib, and \\ref targets with no \\label.

Exit status is 0 whatever it finds: this is a report, not a gate. A draft is
submittable only when the placeholder counts are zero.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SECTIONS = sorted((HERE / "sections").glob("*.tex"))
FIGURES = sorted((HERE / "figures").glob("*.tex"))
TEX_FILES = [HERE / "main.tex", HERE / "macros.tex", *SECTIONS, *FIGURES]

ABSTRACT_LIMIT = 250
HIGHLIGHT_MAX_CHARS = 85
HIGHLIGHT_RANGE = (3, 5)


def strip_comments(text: str) -> str:
    """Drop LaTeX comments (an unescaped % to end of line)."""
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in text.splitlines())


def drop_macro_calls(text: str, name: str) -> str:
    """Remove every \\name{...} call, honouring nested braces."""
    out, i, token = [], 0, "\\" + name + "{"
    while True:
        j = text.find(token, i)
        if j < 0:
            out.append(text[i:])
            return "".join(out)
        out.append(text[i:j])
        depth, k = 1, j + len(token)
        while k < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        i = k


def abstract_words() -> int:
    text = strip_comments((HERE / "sections" / "00-abstract.tex").read_text(encoding="utf-8"))
    text = drop_macro_calls(text, "CSEVEN")
    text = re.sub(r"\$[^$]*\$", " X ", text)          # inline maths counts as one word
    text = re.sub(r"\\[A-Za-z]+", " ", text)           # control words
    text = text.replace("\\%", "%")
    return len(re.findall(r"[A-Za-z0-9][\w.,%+'-]*", text))


def highlights() -> list[str]:
    path = HERE / "highlights.txt"
    if not path.exists():
        return []
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()]
    return [l[1:].strip() if l.startswith(("-", "*", "\u2022")) else l
            for l in lines if l and not l.startswith("#")]


def main() -> int:
    n = abstract_words()
    print(f"Abstract: {n} words (limit {ABSTRACT_LIMIT}; {ABSTRACT_LIMIT - n} to spare)")

    hl = highlights()
    lo, hi = HIGHLIGHT_RANGE
    print(f"Highlights: {len(hl)} bullets (JSS: {lo}-{hi})")
    for h in hl:
        flag = "OK " if len(h) <= HIGHLIGHT_MAX_CHARS else "TOO LONG"
        print(f"  [{flag}] {len(h):3d}  {h}")

    print("Open placeholders (\\CSEVEN / \\TODO):")
    total_c7 = total_todo = 0
    for f in TEX_FILES:
        body = strip_comments(f.read_text(encoding="utf-8"))
        c7 = body.count("\\CSEVEN{") + body.count("\\CSEVENNUM")
        todo = body.count("\\TODO{")
        if f.name == "macros.tex":
            continue  # definitions, not uses
        if c7 or todo:
            print(f"  {f.relative_to(HERE)}: C7 {c7}, TODO {todo}")
        total_c7 += c7
        total_todo += todo
    print(f"  total: C7 {total_c7}, TODO {total_todo}")

    bib = (HERE / "references.bib").read_text(encoding="utf-8")
    keys = set(re.findall(r"@\w+\{([^,\s]+),", bib))
    body = "\n".join(strip_comments(f.read_text(encoding="utf-8")) for f in TEX_FILES)
    cited = set()
    for group in re.findall(r"\\cite[tp]?\*?(?:\[[^\]]*\])*\{([^}]+)\}", body):
        cited.update(k.strip() for k in group.split(","))
    labels = set(re.findall(r"\\label\{([^}]+)\}", body))
    refs = set(re.findall(r"\\(?:ref|eqref|pageref)\{([^}]+)\}", body))
    print("Missing citations:", sorted(cited - keys) or "none")
    print("Dangling references:", sorted(refs - labels) or "none")
    print(f"Cited {len(cited)} of {len(keys)} bibliography entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
