import csv, json, os, re, sys, importlib.util
sys.path.insert(0, os.path.abspath("."))
def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, rel)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m
inject = load("inject_defects", "scripts/inject_defects.py")

AUDIT = "out_study/audit"
key = json.load(open(f"{AUDIT}/key.json", encoding="utf-8"))["key"]
bank = json.load(open("out_study/defect_bank.json", encoding="utf-8"))
dump_of = {e["defect_id"]: e["dump_dir"] for e in bank.get("entries", [])}
dumps = {os.path.basename(d): d for d in inject.base_dirs("out_study")}
def dump_for(i):
    s = key[i]["source"]
    return dump_of.get(s) if key[i]["tier"] == "tier1" else dumps.get(s.split(":")[0])

sheet = open(f"{AUDIT}/rating_sheet.md", encoding="utf-8").read()
blocks = re.split(r"\n## (I\d\d)\n", sheet)[1:]
facts = {i: (re.findall(r"```\n(.*?)\n```", b, re.S) or ["","",""])[2]
         for i, b in zip(blocks[0::2], blocks[1::2])}
def read(p): return {r["item_id"].strip(): r["rating"].strip().upper()
                     for r in csv.DictReader(open(p, encoding="utf-8", newline=""))}
A, B = read(f"{AUDIT}/rating_a.csv"), read(f"{AUDIT}/rating_b.csv")
REVIEW_RE = re.compile(r"^\s+- review ([A-Za-z0-9_\-]{15,30}) mentions:", re.M)

print(f"{'item':5} {'class':20} {'pattern aspect':16} {'stray':>5} {'cites in that pattern':>22}  A B")
print("-" * 82)
for iid in sorted(facts):
    lab = key[iid]["label"]
    if "misaligned" not in lab and lab != "O3":
        continue
    state = inject.state_from_dump(dump_for(iid))
    patterns = (state.get("reasoning_output") or {}).get("patterns") or []
    offenders = set(REVIEW_RE.findall(facts[iid]))
    for p in patterns:
        cites = p.get("evidence_review_ids") or []
        hit = offenders & set(cites)
        if not hit:
            continue
        print(f"{iid:5} {lab:20} {str(p.get('aspect')):16} {len(hit):>5} {len(cites):>22}  "
              f"{A[iid]} {B[iid]}")
