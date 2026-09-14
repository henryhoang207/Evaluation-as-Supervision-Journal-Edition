"""Verify the D13 raters' factual claims against the dumps.

The raters' central discriminator was corruption-of-a-real-id vs fabrication.
That is mechanically checkable: compute the edit distance from each flagged id
to every real review id the stage was actually given.
"""
import csv, json, os, re, sys, importlib.util

sys.path.insert(0, os.path.abspath("."))

def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, rel)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m

inject = load("inject_defects", "scripts/inject_defects.py")

def lev(a, b):
    if a == b: return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

AUDIT = "out_study/audit"
key = json.load(open(f"{AUDIT}/key.json", encoding="utf-8"))["key"]
bank = json.load(open("out_study/defect_bank.json", encoding="utf-8"))
dump_of_defect = {e["defect_id"]: e["dump_dir"] for e in bank.get("entries", [])}
dumps = {os.path.basename(d): d for d in inject.base_dirs("out_study")}

def dump_for(item_id):
    src = key[item_id]["source"]
    if key[item_id]["tier"] == "tier1":
        return dump_of_defect.get(src)
    return dumps.get(src.split(":")[0])

# --- pull each item's fact block straight out of the sheet the raters read ---
sheet = open(f"{AUDIT}/rating_sheet.md", encoding="utf-8").read()
blocks = re.split(r"\n## (I\d\d)\n", sheet)[1:]
facts = {}
for iid, body in zip(blocks[0::2], blocks[1::2]):
    fenced = re.findall(r"```\n(.*?)\n```", body, re.S)
    facts[iid] = fenced[2] if len(fenced) == 3 else ""

def read(p):
    return {r["item_id"].strip(): (r["rating"].strip().upper(), r["note"].strip())
            for r in csv.DictReader(open(p, encoding="utf-8", newline=""))}
A, B = read(f"{AUDIT}/rating_a.csv"), read(f"{AUDIT}/rating_b.csv")

ID_RE = re.compile(r"^\s+- ([A-Za-z0-9_\-]{15,30})\s*$", re.M)
REVIEW_RE = re.compile(r"^\s+- review ([A-Za-z0-9_\-]{15,30}) mentions:", re.M)

print("=" * 100)
print("CLAIM 1 — corruption vs fabrication, checked against the real corpus")
print("=" * 100)
print(f"{'item':5} {'tier':6} {'op/class':26} {'flagged id':26} {'len':>3} {'dist':>4} "
      f"{'mechanism':12} {'A':2} {'B':2}")
print("-" * 100)

rows = []
for iid in sorted(facts):
    cls = key[iid]["label"]
    if "missing_evidence" not in cls and key[iid]["label"] not in ("O1", "O2"):
        continue
    d = dump_for(iid)
    if not d: continue
    state = inject.state_from_dump(d)
    corpus = sorted({a.get("review_id") for a in (state.get("analysis_results") or []) if a.get("review_id")})
    for bad in ID_RE.findall(facts[iid]):
        dist, near = min(((lev(bad, r), r) for r in corpus), default=(None, None))
        mech = "CORRUPTION" if dist is not None and dist <= 2 else "FABRICATION"
        rows.append((iid, key[iid]["tier"], cls, bad, len(bad), dist, mech, near,
                     A[iid][0], B[iid][0]))
        print(f"{iid:5} {key[iid]['tier']:6} {cls:26} {bad:26} {len(bad):>3} "
              f"{dist if dist is not None else '-':>4} {mech:12} {A[iid][0]:2} {B[iid][0]:2}")
        if mech == "CORRUPTION":
            print(f"{'':5} {'':6} {'':26} nearest real id -> {near}")
json.dump([{"item": r[0], "tier": r[1], "class": r[2], "flagged": r[3], "len": r[4],
            "min_edit_distance": r[5], "mechanism": r[6], "nearest_real_id": r[7],
            "rater_a": r[8], "rater_b": r[9]} for r in rows],
          open("out_study/audit/claim_check.json", "w", encoding="utf-8"), indent=2)

print()
print("=" * 100)
print("CLAIM 2 — 'one stray citation in N', the misaligned-aspect items")
print("=" * 100)
for iid in sorted(facts):
    if "misaligned" not in key[iid]["label"] and key[iid]["label"] != "O3":
        continue
    d = dump_for(iid)
    if not d: continue
    state = inject.state_from_dump(d)
    patterns = (state.get("reasoning_output") or {}).get("patterns") or []
    offenders = REVIEW_RE.findall(facts[iid])
    total = sum(len(p.get("evidence_review_ids") or []) for p in patterns
                if any(o in (p.get("evidence_review_ids") or []) for o in offenders))
    print(f"  {iid}  {key[iid]['label']:26} offending cites: {len(offenders):>2} "
          f"of {total:>2} in the flagged pattern(s)   A={A[iid][0]} B={B[iid][0]}")
