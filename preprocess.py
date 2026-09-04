import json, re, os
from pypdf import PdfReader

JSON_PATH = "C:/Users/Administrator/WorkBuddy/Claw/tariff-data/hts_2026_rev17.json"
PDF_PATH  = "C:/Users/Administrator/WorkBuddy/Claw/tariff-data/china_tariffs_2026.html"
OUT = "C:/Users/Administrator/WorkBuddy/Claw/tariff-platform/src/data/tariff_sample.json"

def parse_rate(s):
    s = (s or "").strip()
    if s == "" or s.lower() == "free":
        return 0.0
    m = re.search(r"plus\s+(\d+(?:\.\d+)?)\s*%", s)
    if m: return float(m.group(1)) / 100.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
    if m: return float(m.group(1)) / 100.0
    return None

data = json.load(open(JSON_PATH, encoding="utf-8"))
by = {r["htsno"]: r for r in data}

# 官方 China Tariffs 映射（8位HTS -> Chapter99 子目）
reader = PdfReader(PDF_PATH)
text = "\n".join(p.extract_text() or "" for p in reader.pages)
mapping = {}
for ln in text.split("\n"):
    m = re.match(r"\s*(\d{4}\.\d{2}\.\d{2})\s+(\d{4}\.\d{2}\.\d{2})\s*$", ln.strip())
    if m:
        mapping[m.group(1)] = m.group(2)

# 代表 HTS（热门 + 覆盖不同税率档，用于原型演示）
seeds = ["6109.10.00","6203.42.40","6404.11.00","9503.00.00","8471.30.00",
         "6108.22.00","6205.20.20","4202.92.90","6110.30.30","9403.60.80",
         "6109.90.00","6211.43.00","6403.99.90","8528.72.00"]

out = {}
for h in seeds:  # h = 8位
    key = next((k for k in by if k.startswith(h)), None)
    if not key:
        print("MISSING seed:", h); continue
    r = by[key]
    base = parse_rate(r.get("general")) or 0.0
    ch99 = mapping.get(h)
    ch99_rate = parse_rate(by[ch99]["general"]) if (ch99 and ch99 in by) else 0.0
    out[h] = {
        "desc": (r.get("description") or "")[:90],
        "base": base,
        "ch99": ch99,
        "ch99_rate": ch99_rate,
    }

result = {
    "revision": "2026 HTS Revision 17 (2026-08-24)",
    "last_updated": "2026-08-24",
    "source": "USITC HTS JSON + official China Tariffs mapping",
    "fixed": {
        "forced_labor_cn": 0.125,   # 9903.05.31, eff 2026-07-24, 中国等46国
        "mpf": 0.003464,            # MPF 0.3464%
        "hmf": 0.00125,             # HMF 0.125%
        "sec122_expired": "2026-07-24"  # Section 122 已过期
    },
    "rates": out,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("WROTE", OUT, "| entries:", len(out))
print("sample:", json.dumps(out.get("6109.10.00"), ensure_ascii=False))
