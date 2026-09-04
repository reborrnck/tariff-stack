# 全量关税数据预处理：官方 USITC HTS Rev17 JSON + 官方 China Tariffs 映射表(PDF)
# -> 生成 tariff_full.json（所有 HTS 的 base + Section301 List4A 叠加层），供生产计算器自由查询。
import json, re, shutil
from pypdf import PdfReader

PATH_JSON = "C:/Users/Administrator/WorkBuddy/Claw/tariff-data/hts_2026_rev17.json"
PATH_PDF  = "C:/Users/Administrator/WorkBuddy/Claw/tariff-data/china_tariffs_2026.html"
OUT       = "C:/Users/Administrator/WorkBuddy/Claw/tariff-platform/src/data/tariff_full.json"
PUB       = "C:/Users/Administrator/WorkBuddy/Claw/tariff-platform/public/data/tariff_full.json"

def parse_rate(s):
    s = (s or "").strip()
    if s == "" or s.lower() == "free":
        return 0.0
    m = re.search(r"plus\s+(\d+(?:\.\d+)?)\s*%", s)
    if m: return float(m.group(1)) / 100.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
    if m: return float(m.group(1)) / 100.0
    return None

print("load schedule...")
data = json.load(open(PATH_JSON, encoding="utf-8"))
by = {r["htsno"]: r for r in data}
print("schedule records:", len(data), "| sample key:", data[0]["htsno"])

print("parse China Tariffs PDF mapping...")
reader = PdfReader(PATH_PDF)
text = "\n".join(p.extract_text() or "" for p in reader.pages)
mapping = {}
for ln in text.split("\n"):
    m = re.match(r"\s*(\d{4}\.\d{2}\.\d{2})\s+(\d{4}\.\d{2}\.\d{2})\s*$", ln.strip())
    if m:
        mapping[m.group(1)] = m.group(2)
print("china mapping entries:", len(mapping))

def ch99_for(h):
    # PDF 映射键为 8 位；HTS 可能是 8 或 10 位
    h8 = h[:8] if len(h) >= 8 else h
    return mapping.get(h) or mapping.get(h8) or None

out = {}
hit = 0
for r in data:
    h = r["htsno"]
    if not h or h.startswith("99"):   # 跳过 Chapter 99 容器子目
        continue
    base = parse_rate(r.get("general"))
    if base is None:
        continue
    ch99 = ch99_for(h)
    ch99_rate = 0.0
    if ch99 and ch99 in by:
        ch99_rate = parse_rate(by[ch99].get("general")) or 0.0
        hit += 1
    out[h] = {
        "desc": (r.get("description") or "").strip()[:140],
        "base": round(base, 5),
        "ch99": ch99,
        "ch99_rate": round(ch99_rate, 5),
    }

json.dump(out, open(OUT, "w"), ensure_ascii=False)
print(f"WROTE {OUT}: {len(out)} HTS records, {hit} with China Section 301 overlay")
# 同时写入 public/data（客户端运行时从此拉取），保持两份一致
shutil.copyfile(OUT, PUB)
print(f"COPIED -> {PUB}")
