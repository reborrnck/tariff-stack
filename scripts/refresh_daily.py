#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TariffStack — 多源关税数据刷新管线 (refresh_daily.py)
======================================================
用户 2026-09-02 钉死的四项要求：
  1. 多源多维采集：不单信 USITC 单一官方。叠加 Federal Register(政府公报 API，最权威实时)
     + Google News RSS(抓"已经更新但我们不知道"的最新新闻) + 官方机构(USTR/Commerce/CBP)。
     USITC 基础表新修订改从官方交互式 HTS 的 reststop API(hts.usitc.gov/reststop，
     结构化 JSON，未被 Cloudflare 拦截)探测 currentRelease；命中新 Rev 即触发重建。
  2. 正确数据判定：Federal Register / USITC 官方 = HIGH(可写回)；官方机构新闻 = MEDIUM；
     单一新闻源 = LOW(仅标记不写回)。分歧时按"权威性+时效性+交叉印证"判正确值。
  3. 24h 自动迭代：本脚本由每日自动化调用；用户手动喊"更新最新数据"也直接跑。
  4. 本地 + 线上同步：高置信度变更写回 policy_overlay.json + 重新生成 tariff_full.json；
     若 git remote 已配且有实质变更，commit+push 触发 CF Pages 线上更新。

用法：
  python refresh_daily.py            # 跑一次（需联网，走 HTTPS_PROXY/127.0.0.1:7890）
网络：优先 env HTTPS_PROXY/HTTP_PROXY；缺失试 127.0.0.1:7890；再试直连。
"""

import json
import hashlib
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM_DIR = os.environ.get("PLATFORM_DIR", r"D:\projects\tariff-platform")  # CI 中由 workflow 注入仓库根；本地默认 D: 路径
OVERLAY_PATH = os.path.join(PLATFORM_DIR, "src", "data", "policy_overlay.json")
FULL_DATA_PATH = os.path.join(PLATFORM_DIR, "public", "data", "tariff_full.json")
PREPROCESS_PATH = os.path.join(PLATFORM_DIR, "preprocess_full.py")
REPORT_DIR = os.environ.get("REPORT_DIR") or os.path.abspath(os.path.join(HERE, "..", "kw-research", "outputs"))  # CI 注入 runner.temp；本地走 Claw/kw-research

USITC_REST_BASE = "https://hts.usitc.gov/reststop"  # 官方交互式 HTS 的 reststop API（hts.usitc.gov，未被 Cloudflare 拦截，结构化 JSON）
# 针对性政策词（抓宏观 232/301 公告，而非个案 AD/CVD 噪声）
FR_TERMS = ["Section 232", "Section 301", "de minimis",
            "Harmonized Tariff Schedule", "reciprocal tariff", "forced labor"]
FR_API = ("https://www.federalregister.gov/api/v1/articles.json"
          "?conditions[term]={term}&per_page=15&order=newest")
NEWS_RSS = ("https://news.google.com/rss/search?q="
            "US%20tariff%20Section%20232%20OR%20Section%20301%20OR%20HTS%20OR%20import%20duty%20OR%20de%20minimis"
            "&hl=en-US&gl=US&ceid=US:en")

# 已知叠加层关键事实（交叉比对基准）
KNOWN = {
    "sec232_pharma_eff": "2026-09-29",
    "sec232_drones_eff": "2026-09-03",
    "sec232_polysilicon_eff": "2026-12-04",
    "sec232_steel_alum_copper": 0.50,
    "sec232_autos": 0.25,
    "sec232_lumber": 0.10,
    "forced_labor_CN": 0.125,
    "forced_labor_OTHER": 0.10,
    "eu_deal_cap": 0.10,
    "uk_deal_cap": 0.10,
}

# 关键词 -> (关联字段, 提取正则, 类型)
# type: date=生效日, pct=税率
WATCH = [
    (r"pharmaceutical|drug", "sec232_pharma_eff", r"(\d{4}-\d{2}-\d{2})", "date"),
    (r"unmanned aircraft|drone", "sec232_drones_eff", r"(\d{4}-\d{2}-\d{2})", "date"),
    (r"polysilicon", "sec232_polysilicon_eff", r"(\d{4}-\d{2}-\d{2})", "date"),
    (r"steel|aluminum|aluminium|copper", "sec232_steel_alum_copper", r"(\d{1,3})\s*%", "pct"),
    (r"automobile|motor vehicle|auto part", "sec232_autos", r"(\d{1,3})\s*%", "pct"),
    (r"lumber|timber", "sec232_lumber", r"(\d{1,3})\s*%", "pct"),
    (r"forced labor|forced labour", "forced_labor_CN", r"(\d{1,3}(?:\.\d+)?)\s*%", "pct"),
    (r"european union|us-eu", "eu_deal_cap", r"(\d{1,3}(?:\.\d+)?)\s*%", "pct"),
    (r"united kingdom|britain|economic prosperity deal", "uk_deal_cap", r"(\d{1,3}(?:\.\d+)?)\s*%", "pct"),
    (r"harmonized tariff schedule", "_hts_revision", r"revision\s+(\d+)", "rev"),
    (r"de minimis", "_deminimis", r"(\d{4}-\d{2}-\d{2})", "date"),
]

# 字段 → policy_overlay.json 真实嵌套路径 + 类型（修复 WATCH 字段名与实际结构错位）
# type: pct=税率(存为 0.x 浮点) / date=生效日(存为字符串) / rev=修订号(int)
# 生效日类字段写入独立的 overlay["effective_dates"] 字典，避免破坏现有 sec232 标志键结构。
# 人工维护字段（不进 FIELD_MAP/WATCH，自动刷新绝不覆盖）：eu_members、uk_code、usmca_free、
#   us_fta_free、notes、source —— 均为静态参考(ISO 代码/成员国/FTA 成员)或人工撰写的政策说明，
#   无可靠自动源，误刷会覆盖正确值。变更时需人工核对官方公告后手动更新。
FIELD_MAP = {
    "sec232_steel_alum_copper": (("sec232", "steel_alum_copper"), "pct"),
    "sec232_autos":              (("sec232", "autos_parts"), "pct"),
    "sec232_lumber":             (("sec232", "lumber"), "pct"),
    "forced_labor_CN":           (("forced_labor", "CN"), "pct"),
    "sec232_pharma_eff":         (("effective_dates", "sec232_pharma"), "date"),
    "sec232_drones_eff":         (("effective_dates", "sec232_drones"), "date"),
    "sec232_polysilicon_eff":    (("effective_dates", "sec232_polysilicon"), "date"),
    "_deminimis":                (("effective_dates", "deminimis"), "date"),
    "base_hts_revision":         (("base_hts_revision",), "rev"),
    "eu_deal_cap":               (("eu_deal_cap",), "pct"),
    "uk_deal_cap":               (("uk_deal_cap",), "pct"),
}

# 政策解读型常量（非简单 API 字段）：Federal Register 监控到信号仅 FLAG_REVIEW 标记人工核对，
# 不直接 APPLY 写回——避免把"EU 对美报复关税"等噪声误写成 US 对 EU 的 301 上限（守全真数据铁律）。
REVIEW_ONLY_FIELDS = {"eu_deal_cap", "uk_deal_cap"}


def get_overlay_val(overlay, field):
    """读取 overlay 中某字段当前真值（按 FIELD_MAP 路径），缺失返回 None。"""
    m = FIELD_MAP.get(field)
    if not m:
        return None
    path, _ = m
    cur = overlay
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def set_overlay_val(overlay, field, value):
    """按 FIELD_MAP 路径写入 overlay 真值，中间节点自动建字典。成功返回 True。"""
    m = FIELD_MAP.get(field)
    if not m:
        return False
    path, _ = m
    cur = overlay
    for k in path[:-1]:
        cur = cur.setdefault(k, {})
    cur[path[-1]] = value
    return True


def coerce_val(raw, vtype):
    """把提取到的原始字符串转成类型化值；转换失败返回 None。"""
    if not raw:
        return None
    try:
        if vtype == "pct":
            return round(float(raw.replace("%", "").strip()) / 100.0, 4)
        if vtype == "date":
            return raw.strip()
        if vtype == "rev":
            return int(raw)
    except Exception:  # noqa
        return None
    return None


# 页头滚动播报的"真实政策"条目（i18n key 驱动，10 语翻译由前端负责）。
# 每日刷新时重写 generated_at=今日；政策实质变化时更新此列表并随 commit 同步线上。
NEWS_FEED_ITEMS = [
    {"key": "news_usitc",         "tag": "US", "date": "2026-08-24"},
    {"key": "news_sec232_steel",  "tag": "US", "date": "2026"},
    {"key": "news_sec232_autos",  "tag": "US", "date": "2026"},
    {"key": "news_sec232_pharma", "tag": "US", "date": KNOWN["sec232_pharma_eff"]},
    {"key": "news_sec232_drones", "tag": "US", "date": KNOWN["sec232_drones_eff"]},
    {"key": "news_eu_cap",         "tag": "EU", "date": "2026"},
    {"key": "news_uk_cap",         "tag": "UK", "date": "2026"},
    {"key": "news_uflpa",          "tag": "US", "date": "2026-07-24"},
]


# ---------- 网络 ----------
def _build_opener():
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if not proxy:
        proxy = "http://127.0.0.1:7890"
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    )


_OPENER = None


def http_get(url, timeout=25, extra_headers=None):
    global _OPENER
    if _OPENER is None:
        _OPENER = _build_opener()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra_headers:
        headers.update(extra_headers)
    tries = [_OPENER, urllib.request.build_opener()]  # 代理 -> 直连兜底
    last = None
    for op in tries:
        try:
            req = urllib.request.Request(url, headers=headers)
            with op.open(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace"), None
        except Exception as e:  # noqa
            last = e
    return None, str(last)


# ---------- 采集 ----------
def _norm_us_date(s):
    """把 USITC releaseList 的 MM/DD/YYYY 归一成 YYYY-MM-DD（非该格式原样返回）。"""
    if not s or not isinstance(s, str):
        return s
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s.strip())
    return f"{m.group(3)}-{m.group(1)}-{m.group(2)}" if m else s


def check_usitc():
    """探测当前 USITC HTS 修订号+生效日期。
    改用官方交互式 HTS 的 reststop API（hts.usitc.gov，未被 Cloudflare 拦），
    比旧 www.usitc.gov 文案正则更稳、结构化。currentRelease 给修订号，
    releaseList 当前条目给日期（优先生效日期 target/releaseStartDate，回退创建日期 date）。
    """
    txt, err = http_get(USITC_REST_BASE + "/currentRelease",
                        extra_headers={"Accept": "application/json"})
    if not txt:
        return None, None, f"FAIL:currentRelease:{err}"
    try:
        cur = json.loads(txt)
    except Exception as e:  # noqa
        return None, None, f"JSON_FAIL:currentRelease:{e}"
    name = cur.get("name", "") or cur.get("description", "") or ""
    m = re.search(r"HTSRev(\d+)", name) or re.search(r"Revision\s+(\d+)", name)
    if not m:
        return None, None, "PARSE_FAIL:rev"
    rev = int(m.group(1))
    # 取日期：releaseList 中 status=current 或 name 命中的条目
    date = ""
    ltxt, lerr = http_get(USITC_REST_BASE + "/releaseList",
                          extra_headers={"Accept": "application/json"})
    if ltxt:
        try:
            for it in json.loads(ltxt):
                if it.get("status") == "current" or it.get("name") == name:
                    date = (it.get("target") or it.get("releaseStartDate")
                            or it.get("date") or "")
                    date = _norm_us_date(date)
                    break
        except Exception:  # noqa
            pass
    return rev, date, "OK"


def fetch_fed_register():
    out = []
    seen = set()
    fails = []
    for term in FR_TERMS:
        url = FR_API.format(term=term.replace(" ", "%20"))
        txt, err = http_get(url)
        if not txt:
            fails.append(f"{term}:{err}")
            continue
        try:
            data = json.loads(txt)
        except Exception as e:  # noqa
            fails.append(f"{term}:JSON_FAIL:{e}")
            continue
        for d in data.get("results", []):
            dn = d.get("document_number", "")
            if dn in seen:
                continue
            seen.add(dn)
            dates = d.get("dates", {}) or {}
            ags = [a.get("name", "") for a in d.get("agencies", [])]
            out.append({
                "title": d.get("title", ""),
                "pub": d.get("publication_date", ""),
                "eff": dates.get("effective_date") or "",
                "doc": dn,
                "type": d.get("type", ""),
                "agencies": ags,
                "json_url": d.get("json_url", ""),
                "abstract": (d.get("abstract", "") or "")[:400],
            })
    st = "OK" if not fails else "PARTIAL:" + ";".join(fails[:3])
    return out, st


def _parse_pubdate(s):
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except Exception:  # noqa
            continue
    return None


def fetch_news():
    xml, err = http_get(NEWS_RSS)
    if not xml:
        return [], f"FAIL:{err}"
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    seen = set()
    raw = []
    for block in re.findall(r"<item>(.*?)</item>", xml, re.S):
        t = re.search(r"<title>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))</title>", block, re.S)
        p = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
        l = re.search(r"<link>(.*?)</link>", block, re.S)
        title = (t.group(1) or t.group(2) or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        pub = _parse_pubdate(p.group(1) or "") if p else None
        # 仅保留近 30 天，且去重；老文章不计入（避免历史 evergreen 噪声）
        if pub and pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        if pub and pub < cutoff:
            continue
        raw.append({"title": title, "pub": (p.group(1) or "").strip(),
                    "link": (l.group(1) or "").strip()})
    return raw[:20], "OK"


# ---------- 正确数据判定 ----------
def reconcile(usitc_rev, usitc_date, fr_docs, news_items, overlay, provisioned_rev=None):
    findings = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # 当前已记录的基础表修订号：优先读专属字段 base_hts_revision（首次探测后写入），
    # 旧部署可能把版本号藏在 as_of 文案里，做一次兼容回退。
    asof_rev = None
    br = overlay.get("base_hts_revision")
    if isinstance(br, int):
        asof_rev = br
    elif isinstance(br, str) and br.isdigit():
        asof_rev = int(br)
    else:
        m = re.search(r"Revision (\d+)", overlay.get("as_of", ""))
        if m:
            asof_rev = int(m.group(1))

    # 1) USITC 基础表修订（rev 来自 reststop/currentRelease，结构化 JSON）
    #    served_rev = 当前线上已服务(base)数据的 rev（来自 overlay 记录）。
    #    关键守全真数据：版本号前进到的 rev 必须等于 preprocess 实际重建出的底层数据 rev，
    #    绝不"页面显示新版本、底层却是旧税率"。判定：
    #      - provisioned_rev(可抓到的最新 rev) > served_rev → 重建到 provisioned_rev，版本号前进到它；
    #        若 provisioned_rev < usitc_rev(announced)，说明 announced 更高但 JSON 暂未可抓取，
    #        数据先前进到可抓到的最新 rev，并标注 announced rev 待跟进。
    #      - announced 更新但可抓到的最新 rev 不比已服务新（JSON 暂未可抓取/网络异常）→ FLAG_REVIEW，
    #        版本号不幻进，数据维持 served_rev，待官方 JSON 上线后次日自动重建。
    served_rev = asof_rev
    if usitc_rev is None:
        pass  # 取数失败不误报，靠 FR/News 兜底
    elif served_rev is None:
        # 首次：以实际已构建的 rev 记录基准（有 provisioned 用它，否则用 announced），不触发重建
        base = provisioned_rev if provisioned_rev is not None else usitc_rev
        findings.append({"field": "base_hts_revision", "confidence": "HIGH",
                         "source": "USITC", "found": f"Rev{usitc_rev} ({usitc_date})",
                         "current": "(未记录)", "action": "APPLY", "new_value": base,
                         "diff": True,
                         "note": f"首次探测，记录基准 HTS 修订 Rev{base}（{usitc_date}）"})
    elif provisioned_rev is not None and provisioned_rev > served_rev:
        # 可抓到比当前已服务更新的 rev → 重建到该 rev，版本号前进到 provisioned_rev
        caught_up = (provisioned_rev == usitc_rev)
        findings.append({"field": "base_hts_revision", "confidence": "HIGH",
                         "source": "USITC", "found": f"Rev{usitc_rev} ({usitc_date})",
                         "current": f"Rev{served_rev}", "action": "REBUILD_FULL",
                         "new_value": provisioned_rev,
                         "diff": True,
                         "note": ("USITC 发布新修订，已抓取官方 JSON，重建到 Rev%s" % provisioned_rev)
                                 + ("" if caught_up else f"；announced Rev{usitc_rev} 的 JSON 暂未可抓取，待其上线后次日继续前进")})
    elif usitc_rev > served_rev:
        # announced 更新但可抓到的最新 rev 不比已服务新（JSON 暂未可抓取/网络异常）→ 不幻进版本号
        findings.append({"field": "base_hts_revision", "confidence": "HIGH",
                         "source": "USITC", "found": f"Rev{usitc_rev} ({usitc_date}) 已宣布",
                         "current": f"Rev{served_rev}", "action": "FLAG_REVIEW",
                         "diff": False,
                         "note": f"USITC 已宣布 Rev{usitc_rev}，但可抓到的最新 rev(provisioned={provisioned_rev}) 不比已服务 Rev{served_rev} 新；"
                                 f"数据维持 Rev{served_rev}，待官方 JSON 上线后次日自动重建，版本号暂不前进"})
    else:
        findings.append({"field": "base_hts_revision", "confidence": "HIGH",
                         "source": "USITC", "found": f"Rev{usitc_rev} ({usitc_date}) 已最新",
                         "current": f"Rev{served_rev}", "action": "NONE",
                         "diff": False, "note": "基础税率表无更新"})

    # 2) Federal Register 公文 —— 监控+标记待人工复核（FR 噪声大、生效日常缺结构字段，
    #    故不作为自动写回，而是按政策层 surfacing 候选供助理核对权威源后应用正确值）。
    TARIFF_CTX = re.compile(r"tariff|duty|section 232|section 301|de minimis|hts|harmonized")
    # 各层必须出现的语境词（降噪：FDA 药品批准/个案 AD-CVD 不含这些词则跳过）
    FIELD_CTX = {
        "sec232_steel_alum_copper": r"section 232",
        "sec232_autos": r"section 232",
        "sec232_lumber": r"section 232",
        "sec232_drones_eff": r"section 232",
        "sec232_pharma_eff": r"section 232",
        "sec232_polysilicon_eff": r"section 232",
        "forced_labor_CN": r"section 301.{0,40}forced labor|forced labor.{0,40}section 301",
        "_deminimis": r"de minimis",
        "_hts_revision": r"harmonized tariff schedule",
        "eu_deal_cap": r"section 301.{0,40}(european union|\beu\b)|(european union|\beu\b).{0,40}section 301|us-eu",
        "uk_deal_cap": r"section 301.{0,40}(united kingdom|britain)|(united kingdom|britain).{0,40}section 301|economic prosperity deal",
    }
    for doc in fr_docs:
        blob = (doc["title"] + " " + doc["abstract"]).lower()
        matched = None
        for kw, field, pat, kind in WATCH:
            if re.search(kw, blob):
                matched = (field, kind, pat)
                break
        if not matched:
            continue
        field, kind, pat = matched
        if not TARIFF_CTX.search(blob):
            continue
        ctx = FIELD_CTX.get(field)
        if ctx and not re.search(ctx, blob):
            continue
        if field == "_hts_revision":
            mm = re.search(pat, blob)
            val = mm.group(1) if mm else ""
            # 仅当真提取到“更新且更大”的修订号才触发重建，否则仅标记
            if val.isdigit() and (asof_rev is None or int(val) > asof_rev):
                findings.append({"field": "base_hts_revision", "confidence": "MEDIUM",
                                 "source": "Federal Register",
                                 "found": f"检测到新 HTS Rev{val} ({doc['title'][:50]})",
                                 "current": overlay.get("as_of", "?"),
                                 "action": "REVIEW_REBUILD", "diff": True,
                                 "note": f"doc#{doc['doc']} {doc['pub']} 链接 {doc.get('json_url','')[:70]} — 需人工确认并重建全量"})
            else:
                findings.append({"field": "base_hts_revision", "confidence": "MEDIUM",
                                 "source": "Federal Register",
                                 "found": f"HTS 修订信号(无新版本号): {doc['title'][:50]}",
                                 "current": overlay.get("as_of", "?"),
                                 "action": "FLAG_REVIEW", "diff": False,
                                 "note": f"doc#{doc['doc']} {doc['pub']} — 提及 HTS 但非新修订，待核"})
            continue
        # 尝试提取可判读的生效日/税率；提取不到也照常标记（留给人工）
        cval = None
        raw = ""
        if kind == "date" and doc["eff"]:
            raw = doc["eff"]
            cval = coerce_val(raw, "date")
        else:
            mm = re.search(pat, blob)
            raw = mm.group(1) if mm else ""
            if kind == "pct":
                cval = coerce_val(raw, "pct")
            elif kind == "date":
                cval = coerce_val(raw, "date")
        cur = get_overlay_val(overlay, field)
        diff = (cval is not None) and (cur is None or cval != cur)
        # 完全托管：Federal Register 为官方权威源(MEDIUM)，提取到值且确有差异 → 直接写回(APPLY)；
        # 仅当提取不到值(待核)才 FLAG_REVIEW 留痕。新闻 LOW 不在此分支，仅标记不写回。
        # 政策解读型常量(eu/uk cap)仅标记人工核对，不直接写回（避免误刷覆盖正确 cap）
        if field in REVIEW_ONLY_FIELDS:
            action = "FLAG_REVIEW"
        else:
            action = "APPLY" if (cval is not None and diff) else "FLAG_REVIEW"
        findings.append({"field": field, "confidence": "MEDIUM", "source": "Federal Register",
                        "found": f"{doc['title'][:70]} => {raw or '(待核)'}" + (f" (eff {doc['eff']})" if doc['eff'] else ""),
                        "current": str(cur) if cur is not None else "(无)",
                        "new_value": cval, "action": action, "diff": diff,
                        "note": "doc#%s %s ag %s 链接 %s" % (
                            doc['doc'], doc['pub'], ','.join(doc['agencies'])[:30],
                            doc.get('json_url', '')[:70])})

    # 3) 新闻：in-flight 标记，不写回
    seen = set()
    for it in news_items:
        low = it["title"].lower()
        if not re.search(r"tariff|section 232|section 301|hts|duty|de minimis", low):
            continue
        if it["title"] in seen:
            continue
        seen.add(it["title"])
        findings.append({"field": "_news", "confidence": "LOW", "source": "Google News",
                        "found": it["title"], "current": "", "action": "FLAG", "diff": False,
                        "note": f"pub {it['pub']} | {it['link'][:60]}"})
    return findings, today


# ---------- 写回 ----------
def write_overlay_atomic(overlay):
    """原子写回；Windows 下若被 dev server 锁住，尝试先删旧文件再 rename 兜底，
    仍失败才落到 .pending.json 并标记 PENDING。"""
    tmp = OVERLAY_PATH + ".tmp"
    for attempt in range(5):
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(overlay, f, ensure_ascii=False, indent=2)
            os.replace(tmp, OVERLAY_PATH)
            return True
        except Exception:  # noqa
            # Windows 文件锁兜底：被锁的旧文件先删掉，再试一次 rename
            try:
                os.remove(OVERLAY_PATH)
                os.replace(tmp, OVERLAY_PATH)
                return True
            except Exception:  # noqa
                pass
            time.sleep(0.4)
    # 锁兜底：写 pending，等 dev server 关闭或人工 apply
    try:
        with open(OVERLAY_PATH + ".pending.json", "w", encoding="utf-8") as f:
            json.dump(overlay, f, ensure_ascii=False, indent=2)
        return "PENDING"
    except Exception:
        return False


def write_news_feed(today):
    """每日重写页头滚动播报数据源（generated_at=今日）。翻译由前端 i18n 负责，
    故此处只写 i18n key 引用，UI 模板无需改动即可随每日刷新更新。"""
    path = os.path.join(PLATFORM_DIR, "src", "data", "news_feed.json")
    payload = {"generated_at": today, "items": NEWS_FEED_ITEMS}
    tmp = path + ".tmp"
    for attempt in range(5):
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
            return "OK"
        except Exception:  # noqa
            time.sleep(0.4)
    return "FAIL(locked)"


def _tariff_data_dir():
    """输入源目录：CI 由 TARIFF_DATA_DIR 注入（脚本内 temp）；本地回退旧 C 盘路径。"""
    return os.environ.get("TARIFF_DATA_DIR") or r"C:/Users/Administrator/WorkBuddy/Claw/tariff-data"


def _provisioned_rev():
    """读 fetch_sources 写出的落地 rev 清单：我们实际已抓取到、可用来重建全量数据的 HTS rev。"""
    p = os.path.join(_tariff_data_dir(), "hts_provisioned_rev.txt")
    if os.path.exists(p):
        try:
            v = open(p, encoding="utf-8").read().strip()
            return int(v) if v else None
        except Exception:  # noqa
            return None
    return None


def maybe_rebuild_full():
    if not os.path.exists(PREPROCESS_PATH):
        return "SKIP(no preprocess)"
    try:
        # 把 PLATFORM_DIR + TARIFF_DATA_DIR 注入子进程环境，便于 preprocess 解析输入/输出路径
        env = dict(os.environ)
        env["PLATFORM_DIR"] = PLATFORM_DIR
        env["TARIFF_DATA_DIR"] = _tariff_data_dir()
        r = subprocess.run([sys.executable, PREPROCESS_PATH], cwd=PLATFORM_DIR,
                           timeout=600, capture_output=True, env=env)
        if r.returncode == 2:
            return "SKIP(no inputs)"
        res = "OK" if r.returncode == 0 else f"FAIL:{r.stderr[:120]}"
        # CN 全量重建：仅本地存在 _cn_src 时触发（CI 无 _cn_src → 跳过，CN 维持已入库静态基表）。
        cn_res = maybe_rebuild_cn(env)
        return f"{res} | CN:{cn_res}"
    except Exception as e:  # noqa
        return f"FAIL:{e}"


def maybe_rebuild_cn(env):
    """本地有官方 CN 税则 PDF(_cn_src) 时，按其 sha256 变化判定是否重建 tariff_full_cn.json。
    CI 不入库 70MB PDF（本机 git-lfs 不可用）→ 此分支在 CI 恒为 SKIP，CN 全量维持静态基表。
    哈希守卫：PDF 未变则不重复重建，避免每日白跑 pdfplumber 解析大文件。"""
    cn_script = os.path.join(PLATFORM_DIR, "scripts", "build_cn_tariff.py")
    full_pdf = os.path.join(PLATFORM_DIR, "_cn_src", "cn_2026_full_tariff.pdf")
    hash_path = os.path.join(PLATFORM_DIR, "src", "data", "cn_src_hash.txt")
    if not os.path.exists(cn_script) or not os.path.exists(full_pdf):
        return "SKIP(no _cn_src)"
    h = hashlib.sha256()
    with open(full_pdf, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    digest = h.hexdigest()
    old = ""
    if os.path.exists(hash_path):
        with open(hash_path, encoding="utf-8") as f:
            old = f.read().strip()
    if old == digest:
        return "SKIP(unchanged)"
    r = subprocess.run([sys.executable, cn_script], cwd=PLATFORM_DIR,
                       timeout=600, capture_output=True, env=env)
    if r.returncode != 0:
        return f"FAIL:{r.stderr[:120]}"
    with open(hash_path, "w", encoding="utf-8") as f:
        f.write(digest)
    return f"OK(sha256={digest[:12]})"


def maybe_deploy(dirty):
    if not dirty:
        return "SKIP(no data change)"
    try:
        if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                          cwd=PLATFORM_DIR, capture_output=True).returncode != 0:
            return "SKIP(not a git repo)"
        if not subprocess.run(["git", "remote"], cwd=PLATFORM_DIR, capture_output=True).stdout.strip():
            return "SKIP(no remote)"
        # 仅提交本管线触及的数据文件，避免把无关本地改动卷进自动提交。
        # CN 全量(tariff_full_cn.json) 与 _cn_src 哈希仅在本地重建时存在，CI 下按存在性决定是否纳入。
        add_list = ["src/data/policy_overlay.json", "src/data/tariff_full.json",
                    "public/data/tariff_full.json", "src/data/news_feed.json"]
        for extra in ["src/data/tariff_full_cn.json", "public/data/tariff_full_cn.json",
                      "src/data/cn_src_hash.txt"]:
            if os.path.exists(os.path.join(PLATFORM_DIR, extra)):
                add_list.append(extra)
        for p in add_list:
            subprocess.run(["git", "add", p], cwd=PLATFORM_DIR, capture_output=True)
        msg = f"data refresh {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        subprocess.run(["git", "commit", "-m", msg], cwd=PLATFORM_DIR, capture_output=True)
        last_err = ""
        for _ in range(3):
            # 先拉取远端最新（防非快进），再推送；瞬时失败重试，避免当天数据 stale
            subprocess.run(["git", "pull", "--rebase", "origin", "main"],
                           cwd=PLATFORM_DIR, capture_output=True)
            p = subprocess.run(["git", "push", "origin", "HEAD:refs/heads/main"],
                               cwd=PLATFORM_DIR, capture_output=True, text=True)
            if p.returncode == 0:
                return "OK"
            last_err = (p.stderr or "")[:120]
            time.sleep(2)
        return f"PUSH_FAIL:{last_err}"
    except Exception as e:  # noqa
        return f"FAIL:{e}"


def write_report(usitc_rev, usitc_date, fr_docs, news_items, findings, deploy_res, today):
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, f"FRESHNESS_REPORT_{today}.md")
    L = [f"# TariffStack 数据新鲜度报告 — {today}", "",
         "> 多源采集：USITC HTS 档案(best-effort) + Federal Register API + Google News RSS。",
         "> 判定：Federal Register/USITC 官方=HIGH；官方机构新闻=MEDIUM；单新闻源=LOW(仅标记)。", "",
         "## 采集状态"]
    L.append(f"- USITC 最新修订探测(reststop API)：rev={usitc_rev} date={usitc_date}（OK=结构化 JSON 命中；FAIL/JSON_FAIL/PARSE_FAIL=取数异常，靠 FR/News 兜底）")
    L.append(f"- Federal Register 近期公文：{len(fr_docs)} 条")
    L.append(f"- Google News 近期关税新闻：{len(news_items)} 条")
    L.append(f"- 线上同步(commit/push)：{deploy_res}")
    L.append("")
    L.append("## 发现 / 交叉验证")
    actionable = [f for f in findings if f["confidence"] in ("HIGH", "MEDIUM")]
    news = [f for f in findings if f["confidence"] == "LOW"]
    if not findings:
        L.append("- 无新发现。")
    if actionable:
        L.append(f"### 需关注（权威源，{len(actionable)} 条）")
        for f in actionable:
            L.append(f"- **[{f['confidence']}]** `{f['field']}` | 源:{f['source']} | 动作:{f['action']} | 差异:{f['diff']}")
            L.append(f"  - 发现：{f['found']}")
            L.append(f"  - 当前值：{f['current']}")
            if f.get("action") == "APPLY":
                L.append(f"  - ✅ 已自动写回真值（旧 {f['current']} → 新 {f['new_value']}）")
            L.append(f"  - {f['note']}")
    if news:
        L.append(f"### 近期新闻监测（近30天，{len(news)} 条，仅标记不写回）")
        for f in news:
            L.append(f"- {f['pub'][:16]} · {f['found'][:90]}")
    L.append("")
    L.append("## 正确数据判定摘要")
    L.append("完全托管模式：USITC(HIGH) 与 Federal Register(MEDIUM) 官方源变更 → 直接写回 policy_overlay.json 真值（APPLY，无需人工确认）。")
    L.append("Google News(LOW) 仅作 in-flight 标记，不自动写回（非官方源）。")
    L.append("本报告为非阻塞审查/审计层：每次运行记录所有『旧值→新值+来源链接』，便于回溯与人工复核异常，但不阻断自动写回。")
    body = "\n".join(L)
    tmp = path + ".tmp"
    for attempt in range(5):
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(body)
            os.replace(tmp, path)
            return path
        except Exception:  # noqa
            time.sleep(0.4)
    # 锁兜底：写带时间戳的副本
    alt = os.path.join(REPORT_DIR, f"FRESHNESS_REPORT_{today}_{int(time.time())}.md")
    with open(alt, "w", encoding="utf-8") as fh:
        fh.write(body)
    return alt


def main():
    print(f"[refresh] {datetime.now(timezone.utc).isoformat()} 开始多源刷新")
    usitc_rev, usitc_date, usitc_st = check_usitc()
    print(f"[refresh] USITC: rev={usitc_rev} date={usitc_date} ({usitc_st})")
    fr_docs, fr_st = fetch_fed_register()
    print(f"[refresh] Federal Register: {len(fr_docs)} 条 ({fr_st})")
    news_items, news_st = fetch_news()
    print(f"[refresh] Google News: {len(news_items)} 条 ({news_st})")

    overlay = {}
    if os.path.exists(OVERLAY_PATH):
        with open(OVERLAY_PATH, encoding="utf-8") as f:
            overlay = json.load(f)

    provisioned_rev = _provisioned_rev()
    findings, today = reconcile(usitc_rev, usitc_date, fr_docs, news_items, overlay, provisioned_rev)

    # 完全托管：官方源(USITC HIGH / Federal Register MEDIUM)变更直接写回真值，无需人工确认。
    # base_hts_revision 在 action==REBUILD_FULL 时不在本循环写回——版本号须等全量重建成功后才前进，
    # 避免「页面显示新版本、底层却是旧税率」的错位（USITC 宣布新 rev 但官方 JSON 暂未可抓取时尤其关键）。
    applied = []
    for f in findings:
        act = f.get("action")
        if f["field"] == "base_hts_revision" and act == "REBUILD_FULL":
            continue  # 延后到重建成功后写回
        # 完全托管：官方源(USITC HIGH / Federal Register MEDIUM)的结构化真值直接写回。
        if f.get("diff") and f.get("new_value") is not None and act in ("APPLY", "REBUILD_FULL"):
            if set_overlay_val(overlay, f["field"], f["new_value"]):
                if f["field"] == "base_hts_revision" and usitc_date:
                    overlay["base_hts_date"] = usitc_date
                applied.append(f)
    print(f"[refresh] auto-applied 官方源变更: {len(applied)} 条")

    overlay["last_checked"] = today
    dirty = any(f["diff"] for f in findings)
    if dirty:
        overlay["as_of"] = today
        overlay["source"] = (f"多源实时自动应用({today})：USITC HTS Rev{usitc_rev}({usitc_date}) + "
                             f"Federal Register + Google News。refresh_daily.py 完全托管直接写回官方真值。")
    ok = write_overlay_atomic(overlay)
    print(f"[refresh] write overlay: {ok if isinstance(ok, str) else ('OK' if ok else 'FAIL(locked)')}")

    nf = write_news_feed(today)
    print(f"[refresh] write news_feed: {nf}")

    rebuild = "SKIP(no new rev)"
    for f in findings:
        if f["field"] == "base_hts_revision" and f["action"] in ("REBUILD_FULL", "REVIEW_REBUILD"):
            rebuild = maybe_rebuild_full()
            break
    print(f"[refresh] rebuild full: {rebuild}")

    # 全量重建成功后才把页面版本号前进到新 rev；重建未成功(FAIL/SKIP)则维持旧版本，标记待排查——
    # 守全真数据：绝不出现「版本号=新 rev 而底层数据=旧 rev」的错位。
    for f in findings:
        if f["field"] == "base_hts_revision" and f["action"] == "REBUILD_FULL":
            if rebuild.startswith("OK"):
                set_overlay_val(overlay, "base_hts_revision", f["new_value"])
                if usitc_date:
                    overlay["base_hts_date"] = usitc_date
                overlay["last_checked"] = today
                write_overlay_atomic(overlay)
                print(f"[refresh] base_hts_revision advanced -> Rev{f['new_value']}")
            else:
                f["action"] = "FLAG_REVIEW"
                f["note"] = (f.get("note") or "") + f" | 重建未成功({rebuild})，版本号不前进，待排查"
                print(f"[refresh] WARN: rebuild 未成功({rebuild})，版本号不前进")

    # 每日 push：last_checked / news_feed.generated_at 每次运行都会更新为今日，
    # 故即使无税率变更也 commit+push，保证 CF Pages 重建后线上“页面更新日期”每日刷新。
    # （无 git remote 时 maybe_deploy 自动 SKIP，本地文件仍会更新。）
    deploy = maybe_deploy(True)
    print(f"[refresh] deploy: {deploy}")

    report = write_report(usitc_rev, usitc_date, fr_docs, news_items, findings, deploy, today)
    print(f"[refresh] report: {report}")
    print(f"[refresh] 完成。发现 {len(findings)} 条，实质变更 {dirty}。")

    # 暴露失败给 CI：push 失败 -> run 变红，避免「假绿」让人误以为刷新成功
    if deploy.startswith("PUSH_FAIL") or deploy.startswith("FAIL"):
        print(f"[refresh] FAILED: deploy={deploy}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
