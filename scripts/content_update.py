#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
content_update.py — TariffStack "全托管" 内容更新入口。

把 About / 指南 / 页脚 / 广告与 SEO 相关静态内容的改动 stage + commit + push 到 main。
GitHub Actions 的 daily-refresh.yml 在下次 cron（北京时间 03:00）会自动
`npm run build` + `wrangler deploy`，把改动上线——所以"改完 About 跑一下本脚本"
就等于把更新交给了自动化管线，无需手工登录 Cloudflare 重新发布。

用法:
  python scripts/content_update.py "更新 About 页文案"
不传 message 时使用默认提交信息。

注意: 本脚本只动"内容/UI"路径（见下方 PATHS），不碰密钥、不动数据刷新管线。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 纳入"内容/UI 全托管"的路径（不碰 .env / wrangler 密钥 / data 管线以外东西）
PATHS = [
    "src/pages/about.astro",
    "src/pages/guides/index.astro",
    "src/pages/guides/hs-codes-explained.astro",
    "src/pages/index.astro",
    "src/lib/i18n.ts",
    "public/ads.txt",
    "public/sitemap.xml",
    "public/robots.txt",
    "astro.config.mjs",
]


def run(cmd):
    print("> " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.stderr.strip():
        print(r.stderr.strip())
    return r.returncode


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else \
        "content: add About page + tariff guides + AdSense/SEO files"
    existing = [p for p in PATHS if os.path.exists(os.path.join(REPO, p))]
    if not existing:
        print("没有可提交的内容路径，退出。")
        return
    run(["git", "add", "--", *existing])
    code = run(["git", "commit", "-m", msg])
    if code != 0:
        print("commit 未产生（可能没有变化，或需先 git pull）。")
        return
    rc = run(["git", "push", "origin", "main"])
    if rc == 0:
        print("已推送 main。GitHub Actions 将在下次 cron 自动重新构建并部署。")
    else:
        print("push 失败（可能是本机凭证或网络限制）。改动已 commit 在本地 main，"
              "可在能推送的环境执行 `git push origin main`，或等 CI 拉取后自动部署。")


if __name__ == "__main__":
    main()
