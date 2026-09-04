# 全量关税数据预处理：官方 USITC HTS Rev17 JSON + 官方 China Tariffs 映射表(PDF)
# -> 生成 tariff_full.json（所有 HTS 的 base + Section301 List4A 叠加层），供生产计算器自由查询。
import json, re, shutil, os, sys
from pypdf import PdfReader

# 路径全部基于本文件位置推算，避免硬编码旧磁盘路径在 CI(Linux) / 搬盘后失效。
HERE = os.path.dirname(os.path.abspath(__file__))   # 仓库根（preprocess_full.py 位于根目录）
ROOT = HERE
# 输入源目录：CI 用 TARIFF_DATA_DIR 挂载；本地回退旧 C 盘 tariff-data 路径
TARIFF_DATA_DIR = os.environ.get("TARIFF_DATA_DIR") or r"C:/Users/Administrator/WorkBuddy/Claw/tariff-data"
PATH_JSON = os.path.join(TARIFF_DATA_DIR, "hts_2026_rev17.json")
PATH_PDF  = os.path.join(TARIFF_DATA_DIR, "china_tariffs_2026.html")
# 输出：构建期 SSR 用 src/data，运行时客户端用 public/data，两份须一致
OUT = os.path.join(ROOT, "src", "data", "tariff_full.json")
PUB = os.path.join(ROOT, "public", "data", "tariff_full.json")

def parse_rate(s):
    s = (s or "").strip()
    if s == "" or s.lower() == "free":
        return 0.0
    m = re.search(r"plus\s+(\d+(?:\.\d+)?)\s*%", s)
    if m: return float(m.group(1)) / 100.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
    if m: return float(m.group(1)) / 100.0
    return None

if not (os.path.exists(PATH_JSON) and os.path.exists(PATH_PDF)):
    # CI 未挂载输入源时明确 SKIP（exit 2），让调用方记录「SKIP(no inputs)」而非静默失败
    print(f"[preprocess] SKIP: 输入文件缺失 -> 设置 TARIFF_DATA_DIR 指向含 hts_2026_rev17.json / china_tariffs_2026.html 的目录\n  JSON={PATH_JSON}\n  PDF={PATH_PDF}")
    sys.exit(2)

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
