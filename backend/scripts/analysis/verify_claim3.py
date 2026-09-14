import csv, json, os, re, sys, difflib, importlib.util
sys.path.insert(0, os.path.abspath("."))
def load(n, r):
    s = importlib.util.spec_from_file_location(n, r)
    m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
inject = load("inject_defects", "scripts/inject_defects.py")

AUDIT = "out_study/audit"
key = json.load(open(f"{AUDIT}/key.json", encoding="utf-8"))["key"]
bank = json.load(open("out_study/defect_bank.json", encoding="utf-8"))
dump_of = {e["defect_id"]: e["dump_dir"] for e in bank.get("entries", [])}
dumps = {os.path.basename(d): d for d in inject.base_dirs("out_study")}
def dump_for(i):
    s = key[i]["source"]
    return dump_of.get(s) if key[i]["tier"] == "tier1" else dumps.get(s.split(":")[0])
def read(p): return {r["item_id"].strip(): r["rating"].strip().upper()
                     for r in csv.DictReader(open(p, encoding="utf-8", newline=""))}
A, B = read(f"{AUDIT}/rating_a.csv"), read(f"{AUDIT}/rating_b.csv")

STOP = set("a an the and or of to in for on with is are be been being that this those these "
           "at by from as it its their there here we you they i not no more most very can could "
           "should would may might will shall do does did have has had".split())
def toks(s): return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2}
def jac(a, b):
    ta, tb = toks(a), toks(b)
    return len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0

sheet = open(f"{AUDIT}/rating_sheet.md", encoding="utf-8").read()
blocks = re.split(r"\n## (I\d\d)\n", sheet)[1:]
claims = {i: (re.findall(r"```\n(.*?)\n```", b, re.S) or ["", "", ""])[0]
          for i, b in zip(blocks[0::2], blocks[1::2])}

print(f"THRESHOLD = 0.35 (difflib SequenceMatcher, character-level)\n")
print(f"{'item':5} {'class':26} {'lex':>5} {'tokens':>6}  A B   flagged issue -> best upstream match")
print("-" * 118)
for iid in sorted(claims):
    lab = key[iid]["label"]
    if "untraceable" not in lab and lab != "O5":
        continue
    state = inject.state_from_dump(dump_for(iid))
    reasoning = state.get("reasoning_output") or {}
    cands = ([rc.get("cause", "") for rc in reasoning.get("root_causes") or []]
             + [rc.get("pattern", "") for rc in reasoning.get("root_causes") or []]
             + [p.get("description", "") for p in reasoning.get("patterns") or []])
    cands = [c for c in cands if c]
    issues = re.findall(r"^\s+- (.+)$", claims[iid], re.M)
    for issue in issues:
        lex, best = max(((difflib.SequenceMatcher(None, issue, c).ratio(), c) for c in cands),
                        default=(0.0, ""))
        jbest, jc = max(((jac(issue, c), c) for c in cands), default=(0.0, ""))
        print(f"{iid:5} {lab:26} {lex:>5.2f} {jbest:>6.2f}  {A[iid]} {B[iid]}   "
              f"{issue[:44]!r}")
        print(f"{'':41}          -> {jc[:70]!r}")
