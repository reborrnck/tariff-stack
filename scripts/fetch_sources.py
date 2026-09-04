#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TariffStack — CI 输入源自动拉取 (fetch_sources.py)
==================================================
在每日 CI 中把 US HTS 基础表 + China-301 映射 PDF 自动准备好，
彻底消灭「基表升版时需人工跑 preprocess + commit」的手动步骤（用户全自动铁律）。

输入源：
  1) US HTS RevN JSON —— USITC 官方直链
       https://www.usitc.gov/sites/default/files/tata/hts/hts_2026_revision_{N}_json.json
     N 取自 reststop/currentRelease（结构化 JSON，未被 Cloudflare 拦截）。
     鲁棒性：优先下载 announced rev；失败则向下回退到 rev-1 … DEFAULT_REV，仍失败则复用已缓存文件。
     落地清单：把「实际成功落盘、可被 preprocess 用来重建的 rev」写入 hts_provisioned_rev.txt，
     供 refresh_daily 决策版本号是否前进（守全真数据：绝不「页面显示新 rev、底层却是旧税率」）。
  2) China-301 映射 PDF（实为 PDF，仓库内以 china_tariffs_2026.html 命名，~396KB）
     —— 随仓库入库于 data-src/，此处从 <repo>/data-src 拷贝到 TARIFF_DATA_DIR。

网络：优先 env HTTPS_PROXY/HTTP_PROXY；缺失试 127.0.0.1:7890；再试直连（与 refresh_daily 一致）。
"""
import json
import os
import re
import shutil
import sys
import glob
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))           # scripts/
ROOT = os.path.dirname(HERE)                                 # 仓库根
REPO_DATA_SRC = os.path.join(ROOT, "data-src")               # 随源码入库的小输入源
TARIFF_DATA_DIR = os.environ.get("TARIFF_DATA_DIR") or os.path.join(ROOT, "tariff-data")
USITC_REST_BASE = "https://hts.usitc.gov/reststop"
USITC_JSON_TPL = "https://www.usitc.gov/sites/default/files/tata/hts/hts_2026_revision_{rev}_json.json"
CHINA_SRC_NAME = "china_tariffs_2026.html"
DEFAULT_REV = 17   # 网络取数失败且本地无新版时的兜底修订号
MANIFEST = "hts_provisioned_rev.txt"


def _build_opener():
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if not proxy:
        proxy = "http://127.0.0.1:7890"
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    )


_OPENER = None


def http_get(url, timeout=180, extra_headers=None):
    global _OPENER
    if _OPENER is None:
        _OPENER = _build_opener()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra_headers:
        headers.update(extra_headers)
    last = None
    for op in (_OPENER, urllib.request.build_opener()):   # 代理 -> 直连兜底
        try:
            req = urllib.request.Request(url, headers=headers)
            with op.open(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace"), None
        except Exception as e:  # noqa
            last = e
    return None, str(last)


def check_usitc():
    """探测当前 USITC HTS 修订号（复用 refresh_daily 的 reststop 逻辑，仅取 rev）。"""
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
    return int(m.group(1)), (cur.get("releaseDate") or ""), "OK"


def _max_cached_rev():
    best = -1
    for p in glob.glob(os.path.join(TARIFF_DATA_DIR, "hts_2026_rev*.json")):
        m = re.search(r"hts_2026_rev(\d+)\.json$", os.path.basename(p))
        if m:
            best = max(best, int(m.group(1)))
    return best if best >= 0 else None


def _provision_hts(announced_rev):
    """下载 announced_rev 的 JSON；失败则向下回退到 announced_rev-1 … DEFAULT_REV，
    仍失败则复用 TARIFF_DATA_DIR 中已缓存的最大 rev 文件。返回实际落盘的 rev（无则 None）。"""
    # 优先复用已缓存的最大 rev（免重复下载）
    cached = _max_cached_rev()
    if cached is not None and cached >= announced_rev:
        target = os.path.join(TARIFF_DATA_DIR, f"hts_2026_rev{cached}.json")
        print(f"[fetch] HTS Rev{cached} 已缓存 -> {target} ({os.path.getsize(target)} B) skip")
        return cached
    # 从 announced 向下回退到 DEFAULT_REV，逐个尝试下载
    for rv in range(announced_rev, DEFAULT_REV - 1, -1):
        target = os.path.join(TARIFF_DATA_DIR, f"hts_2026_rev{rv}.json")
        if os.path.exists(target):
            print(f"[fetch] HTS Rev{rv} 已缓存 -> {target} ({os.path.getsize(target)} B) skip")
            return rv
        url = USITC_JSON_TPL.format(rev=rv)
        print(f"[fetch] downloading HTS Rev{rv} from {url}")
        data, err = http_get(url, timeout=180)
        if data:
            with open(target, "w", encoding="utf-8") as f:
                f.write(data)
            print(f"[fetch] HTS Rev{rv} saved -> {target} ({len(data)} B)")
            return rv
        print(f"[fetch] Rev{rv} 下载失败({err})，尝试更低 rev")
    if cached is not None:
        print(f"[fetch] 在线获取全部失败，复用缓存 Rev{cached}")
        return cached
    print("[fetch] FAIL: 无任何 HTS JSON 可用 -> 全量重建将 SKIP(no inputs)")
    return None


def main():
    os.makedirs(TARIFF_DATA_DIR, exist_ok=True)

    # 1) China-301 映射 PDF：随仓库入库于 data-src/，拷贝到 TARIFF_DATA_DIR
    src = os.path.join(REPO_DATA_SRC, CHINA_SRC_NAME)
    dst = os.path.join(TARIFF_DATA_DIR, CHINA_SRC_NAME)
    if os.path.exists(src):
        shutil.copyfile(src, dst)
        print(f"[fetch] China-301 mapping copied -> {dst} ({os.path.getsize(dst)} B)")
    elif os.path.exists(dst):
        print("[fetch] China-301 mapping already present in TARIFF_DATA_DIR (skip copy)")
    else:
        print("[fetch] WARN: China-301 source missing (no data-src/ and no local copy)")

    # 2) US HTS 基础表：取最新 announced rev，尽力下载（含向下回退），落地实际可用 rev
    rev, _date, st = check_usitc()
    if rev is None:
        rev = DEFAULT_REV
        print(f"[fetch] USITC 探测失败({st})，回退默认 rev={rev}")
    else:
        print(f"[fetch] USITC 最新修订(announced) rev={rev} ({st})")
    provisioned = _provision_hts(rev)
    with open(os.path.join(TARIFF_DATA_DIR, MANIFEST), "w", encoding="utf-8") as f:
        f.write(str(provisioned) if provisioned else "")
    print(f"[fetch] provisioned HTS rev={provisioned} -> manifest {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
