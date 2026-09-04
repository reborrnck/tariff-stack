#!/usr/bin/env python3
"""Build tariff_full_cn.json from official 2026 China tariff PDFs (NO token needed).

Sources (official, open, legally effective 2026-01-01):
  - 进出口税则(2026) full PDF  -> all HS-8 lines: 最惠国税率(MFN) + 普通税率(general/col3)
  - 附1 进口商品暂定税率表 PDF  -> provisional rates (暂定税率, often < MFN, actually applied)

Output: src/data/tariff_full_cn.json  (+ copied to public/data for runtime fetch)
  { meta:{source,as_of,n_lines}, by_hs8:{ "<hs8>": {ex,name,mfn,general,prov?,raw_mfn,raw_general} } }
"""
import pdfplumber, re, json, os, sys, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(ROOT, "_cn_src", "cn_2026_full_tariff.pdf")
PROV = os.path.join(ROOT, "_cn_src", "cn_2026_provisional.pdf")
OUT_SRC = os.path.join(ROOT, "src", "data", "tariff_full_cn.json")
OUT_PUB = os.path.join(ROOT, "public", "data", "tariff_full_cn.json")

hs_dotted = re.compile(r'^(ex)?(\d{4})\.(\d{4})$')
hs_plain = re.compile(r'^(ex)?(\d{8})$')
hs_dotted10 = re.compile(r'^(ex)?(\d{4})\.(\d{4})\.(\d{2})$')   # 10-digit HS (China lists many lines at 10-digit)
hs_plain10 = re.compile(r'^(ex)?(\d{10})$')

def norm_hs(cell):
    if not cell:
        return None
    c = cell.strip().replace(' ', '').replace('\n', '').replace('\u00a0', '')
    m = hs_dotted.match(c)
    if m:
        return (m.group(1) is not None, m.group(2) + m.group(3))
    m = hs_dotted10.match(c)
    if m:
        return (m.group(1) is not None, m.group(2) + m.group(3))   # key by first 8 digits
    m = hs_plain.match(c)
    if m:
        return (m.group(1) is not None, m.group(2))
    m = hs_plain10.match(c)
    if m:
        return (m.group(1) is not None, m.group(2)[:8])            # key by first 8 digits
    return None

def parse_rate(cell):
    if not cell:
        return None
    c = cell.strip()
    m = re.match(r'^(\d+(?:\.\d+)?)', c)
    if m:
        return float(m.group(1))
    if c in ('Free', 'free', '免'):
        return 0.0
    if c in ('—', '-', ''):
        return None  # not applicable / no general rate
    return None


def build_gen_map(raw):
    """Fallback: map HS-8 -> trailing number on its line (= 普通税率, last rate column)."""
    out = {}
    for line in raw.splitlines():
        dm = re.search(r'(ex)?(\d{4})\.(\d{4})(?:\.\d{2})?\b', line)
        if dm:
            hs = (dm.group(2) + dm.group(3))
        else:
            pm = re.search(r'(ex)?(\d{10})\b', line)
            if pm:
                hs = pm.group(2)[:8]
            else:
                pm2 = re.search(r'(ex)?(\d{8})\b', line)
                if not pm2:
                    continue
                hs = pm2.group(2)
        nums = re.findall(r'\d+(?:\.\d+)?', line)
        if len(nums) >= 4:  # 序号 + hs + >=2 rates
            out[hs] = float(nums[-1])
    return out

def detect_header(row):
    # returns column map {hs,name,mfn,general} if this is a header row
    joined = ' '.join(str(x or '') for x in row)
    if '税则号列' in joined and ('最惠国税率' in joined or '最惠国' in joined):
        # map by finding indices of known headers
        hmap = {}
        for i, x in enumerate(row):
            if x is None:
                continue
            s = str(x)
            if '税则号列' in s:
                hmap['hs'] = i
            elif '品名称' in s:  # covers 货品名称 (full tariff) and 商品名称 (附1)
                hmap['name'] = i
            elif '最惠国税率' in s or s.strip() == '最惠国税率(%)':
                hmap['mfn'] = i
            elif '普通税率' in s:
                hmap['general'] = i
        if 'hs' in hmap and 'mfn' in hmap:
            return hmap
    return None

def process_pdf(path, page_slice, out_map):
    n_pages = 0
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        lo, hi = page_slice
        if lo is None:
            lo = 0
        if hi is None:
            hi = total
        cmap = None
        for idx in range(lo, min(hi, total)):
            if (idx - lo) % 100 == 0:
                print(f"[progress] {path.split('/')[-1]} page {idx}/{min(hi, total)} lines={len(out_map)}", flush=True)
            page = pdf.pages[idx]
            raw = page.extract_text() or ''
            gen_map = build_gen_map(raw)
            tbls = page.extract_tables()
            if not tbls:
                continue
            for tbl in tbls:
                for row in tbl:
                    if not row:
                        continue
                    h = detect_header(row)
                    if h:
                        cmap = h
                        continue
                    if cmap is None:
                        continue
                    # data row
                    hs_cell = row[cmap['hs']] if cmap['hs'] < len(row) else None
                    nh = norm_hs(hs_cell)
                    if not nh:
                        continue
                    ex, hs = nh
                    name = row[cmap['name']] if cmap['name'] < len(row) else None
                    name = (name or '').strip().replace('\n', ' ')
                    mfn = parse_rate(row[cmap['mfn']] if cmap['mfn'] < len(row) else None)
                    general = parse_rate(row[cmap['general']] if cmap['general'] < len(row) else None)
                    if general is None and hs in gen_map:
                        general = gen_map[hs]
                    # skip pure continuation rows (already have this hs? keep first)
                    if hs in out_map and not ex:
                        # prefer non-ex row with richer data; only overwrite if current has name
                        if not out_map[hs].get('name') and name:
                            out_map[hs]['name'] = name
                        continue
                    out_map[hs] = {
                        'ex': ex,
                        'name': name,
                        'mfn': mfn,
                        'general': general,
                    }
            n_pages += 1
    return n_pages

def process_provisional(out_map):
    with pdfplumber.open(PROV) as pdf:
        cmap = None
        for page in pdf.pages:
            tbls = page.extract_tables()
            if not tbls:
                continue
            for tbl in tbls:
                for row in tbl:
                    if not row:
                        continue
                    h = detect_header(row)
                    if h:
                        cmap = h
                        continue
                    if cmap is None:
                        continue
                    hs_cell = row[cmap['hs']] if cmap['hs'] < len(row) else None
                    nh = norm_hs(hs_cell)
                    if not nh:
                        continue
                    ex, hs = nh
                    mfn = parse_rate(row[cmap['mfn']] if cmap['mfn'] < len(row) else None)
                    # find provisional: it's the LAST rate column in 附1 (暂定税率)
                    # 附1 layout: 序号,EX,税则号列,商品名称,最惠国税率,暂定税率
                    prov = None
                    # search row cells after mfn for a numeric not equal to header
                    name_i = cmap['name']
                    mfn_i = cmap['mfn']
                    # provisional = first numeric cell after mfn that isn't a header
                    for c in row[mfn_i+1:]:
                        if c is None:
                            continue
                        r = parse_rate(c)
                        if r is not None and str(c).strip() not in ('最惠国税率(%)', '暂定税率'):
                            prov = r
                            break
                    entry = out_map.setdefault(hs, {'ex': ex, 'name': '', 'mfn': mfn, 'general': None})
                    entry['prov'] = prov
                    entry['mfn'] = entry['mfn'] if entry['mfn'] is not None else mfn
                    if not entry.get('name') and len(row) > name_i and row[name_i]:
                        entry['name'] = str(row[name_i]).strip().replace('\n', ' ')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=None)
    ap.add_argument('--end', type=int, default=None)
    ap.add_argument('--test', action='store_true', help='only process a few pages, print stats, no write')
    args = ap.parse_args()

    out_map = {}
    n = process_pdf(FULL, (args.start, args.end), out_map)
    print(f"[full] processed pages, lines so far: {len(out_map)}")
    process_provisional(out_map)
    print(f"[provisional] merged, total lines: {len(out_map)}")

    # HS-6 fallback keys: for each unique HS-6 prefix not directly present, attach the
    # first HS-8 line under it (real rate from the schedule, used only when no HS-8 match).
    hs6_added = 0
    for hs8 in list(out_map.keys()):
        hs6 = hs8[:6]
        if hs6 not in out_map:
            out_map[hs6] = out_map[hs8]
            hs6_added += 1
    print(f"[hs6-fallback] added {hs6_added} HS-6 keys")

    if args.test:
        sample = {k: out_map[k] for k in list(out_map)[:5]}
        print("SAMPLE:", json.dumps(sample, ensure_ascii=False, indent=2))
        # spot-check a known code
        for code in ('03035910', '03036300'):
            print(code, out_map.get(code))
        return

    # stats
    with_prov = sum(1 for v in out_map.values() if v.get('prov') is not None)
    no_mfn = sum(1 for v in out_map.values() if v.get('mfn') is None)
    meta = {
        'source': 'Official PRC 2026 Import & Export Tariff (国务院关税税则委员会, effective 2026-01-01)',
        'as_of': '2026-01-01',
        'n_lines': len(out_map),
        'with_provisional': with_prov,
        'missing_mfn': no_mfn,
    }
    result = {'meta': meta, 'by_hs8': out_map}
    os.makedirs(os.path.dirname(OUT_SRC), exist_ok=True)
    with open(OUT_SRC, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, separators=(',', ':'))
    os.makedirs(os.path.dirname(OUT_PUB), exist_ok=True)
    with open(OUT_PUB, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, separators=(',', ':'))
    size = os.path.getsize(OUT_SRC)
    print(f"[write] {OUT_SRC} ({size/1024/1024:.2f} MB), lines={len(out_map)}, prov={with_prov}, no_mfn={no_mfn}")

if __name__ == '__main__':
    main()
