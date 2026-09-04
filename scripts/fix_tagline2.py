import re
p = "src/lib/i18n.ts"
s = open(p, encoding="utf-8").read()
new_vals = [
 "China (official 2026 tariff schedule - live, real rates)",
 "中国（2026 官方税则 - 已接入真实税率）",
 "中国（2026 年公式関税スケジュール - 本番実税率）",
 "China (arancel oficial 2026 - tasas reales en vivo)",
 "China (offizieller 2026-Zolltarif - echte Satze live)",
 "中國（2026 官方稅則 - 已接入真實稅率）",
 "중국 (2026 공식 관세 일정 - 실제 세율 라이브)",
 "Chine (tarif officiel 2026 - taux reels en ligne)",
 "China (tarifa oficial 2026 - taxas reais no ar)",
 "Cina (tariffa ufficiale 2026 - aliquote reali attive)",
]
assert len(new_vals) == 10, len(new_vals)
idx = {"n": 0}
pat = re.compile(r"tagline2_post:[ \t]*(['\"])((?:(?!\1)[^\\]|\\.)*)\1")
def repl(m):
    q = m.group(1)
    v = new_vals[idx["n"]]
    idx["n"] += 1
    return "tagline2_post: " + q + v + q
s2, n = pat.subn(repl, s)
print("replaced:", n)
assert n == 10, n
open(p, "w", encoding="utf-8").write(s2)
print("done")
