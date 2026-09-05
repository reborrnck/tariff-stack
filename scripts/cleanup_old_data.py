#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TariffStack — 旧数据 / 审计垃圾定时清理 (cleanup_old_data.py)
============================================================
用户 2026-09-05 要求「定时清理旧数据」，防止项目长期运行后审计日志与临时锁文件
无限累积、挤占仓库与磁盘。

安全铁律（绝不误删真数据）：
  - 只删除「明确模式」的临时 / 审计文件：
      * FRESHNESS_REPORT_*.md              超过 RETENTION_DAYS 天的旧审计报告
      * FRESHNESS_REPORT_*_<unix>.md       write_report 锁兜底产生的带时间戳副本
      * *.tmp                              原子写入替换的临时文件残留（>1h 旧才删，防误删正在写的）
      * *.pending.json                     write_overlay_atomic 文件锁兜底残留（>1h 旧才删）
  - 真实税率数据受 PROTECTED 保护，任何情况下不删：
      tariff_full.json / tariff_full_cn.json / policy_overlay.json /
      news_feed.json / origins.json / tariff_sample.json
  - 删除前打印摘要；--dry-run 仅预览不删。

扫描目录（--dir 可重复追加；默认覆盖 CI 与本地常见落点）：
  - 环境变量 REPORT_DIR（CI 注入 runner.temp/reports）
  - <PLATFORM_DIR>/kw-research/outputs      本地刷新脚本默认报告落点
  - C:/Users/Administrator/WorkBuddy/Claw/kw-research/outputs   实际本地落点
  - <PLATFORM_DIR>/.refresh_reports         仓库内（若存在）
  - <PLATFORM_DIR>/src/data                 仅清理其中的 *.tmp / *.pending.json 锁残留

用法：
  python cleanup_old_data.py                 # 实际清理并报告
  python cleanup_old_data.py --dry-run       # 只预览要删什么
  python cleanup_old_data.py --retention 14  # 保留最近 14 天报告（默认 30）
"""

import os
import sys
import time
import argparse
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM_DIR = os.environ.get("PLATFORM_DIR", os.path.dirname(HERE))

RETENTION_DAYS = 30          # FRESHNESS_REPORT 保留天数（命令行可覆盖）
STALE_LOCK_HOURS = 1         # *.tmp / *.pending.json 超过该时长才判定为残留

# 受保护的真实数据文件（绝不删除）
PROTECTED = {
    "tariff_full.json", "tariff_full_cn.json", "policy_overlay.json",
    "news_feed.json", "origins.json", "tariff_sample.json",
}

DEFAULT_DIRS = [
    os.environ.get("REPORT_DIR"),
    os.path.join(PLATFORM_DIR, "kw-research", "outputs"),
    r"C:/Users/Administrator/WorkBuddy/Claw/kw-research/outputs",
    os.path.join(PLATFORM_DIR, ".refresh_reports"),
    os.path.join(PLATFORM_DIR, "src", "data"),
]


def _parse_report_date(name):
    """从 FRESHNESS_REPORT_YYYY-MM-DD(.md|_<unix>.md) 解析日期；失败返回 None。"""
    stem = name
    for suf in (".md", ".tmp"):
        if stem.endswith(suf):
            stem = stem[: -len(suf)]
    # 去掉末尾 _<unix> 时间戳
    if "_" in stem:
        cand = stem.rsplit("_", 1)
        if len(cand) == 2 and cand[1].isdigit():
            stem = cand[0]
    if stem.startswith("FRESHNESS_REPORT_"):
        d = stem[len("FRESHNESS_REPORT_"):]
        try:
            return datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _should_prune(path, now, retention, dry_run, removed, protected_skip):
    name = os.path.basename(path)
    if name in PROTECTED:
        protected_skip.append(name)
        return False
    if name.startswith("FRESHNESS_REPORT_"):
        rd = _parse_report_date(name)
        if rd is None:
            # 解析不出日期的报告（异常命名），超过保留期按旧文件处理
            mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
            if (now - mtime).days > retention:
                return True
            return False
        age_days = (now - rd).days
        if age_days > retention:
            return True
        return False
    if name.endswith(".tmp") or name.endswith(".pending.json"):
        mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
        if (now - mtime).total_seconds() > STALE_LOCK_HOURS * 3600:
            return True
        return False
    return False


def main():
    ap = argparse.ArgumentParser(description="TariffStack 旧数据/审计垃圾安全清理")
    ap.add_argument("--dir", action="append", default=[],
                    help="额外扫描目录（可重复）；默认扫描 CI 与本地常见落点")
    ap.add_argument("--retention", type=int, default=RETENTION_DAYS,
                    help="FRESHNESS_REPORT 保留天数（默认 30）")
    ap.add_argument("--dry-run", action="store_true",
                    help="仅预览要删除的文件，不实际删除")
    args = ap.parse_args()

    dirs = [d for d in (DEFAULT_DIRS + args.dir) if d]
    now = datetime.now(timezone.utc)
    removed, protected_skip, scanned = [], [], 0

    print(f"[cleanup] {now.isoformat()} 开始；保留期={args.retention}天；"
          f"{'预览模式' if args.dry_run else '实际删除'}")
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            full = os.path.join(d, fn)
            if not os.path.isfile(full):
                continue
            scanned += 1
            if _should_prune(full, now, args.retention, args.dry_run, removed, protected_skip):
                if args.dry_run:
                    print(f"  [预览] 将删除: {full}")
                    removed.append(full)
                else:
                    try:
                        os.remove(full)
                        print(f"  [删除] {full}")
                        removed.append(full)
                    except Exception as e:  # noqa
                        print(f"  [失败] {full} -> {e}")

    print(f"[cleanup] 扫描文件={scanned}，保护跳过={len(set(protected_skip))}项，"
          f"删除={len(removed)}个")
    print(f"[cleanup] 完成。{'（预览模式，未实际删除）' if args.dry_run else '已清理旧数据。'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
