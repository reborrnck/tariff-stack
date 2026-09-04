import re
p = "src/lib/i18n.ts"
s = open(p, encoding="utf-8").read()
new_vals = [
 "China destination - official 2026 tariff schedule (State Council Tariff Commission, effective 2026-01-01) is now live with REAL rates. If this notice still shows, the HS code was not matched or data is still loading; switch to the U.S. destination for live data.",
 "中国目的地 - 2026 年官方关税税则（国务院关税税则委员会，2026-01-01 生效）已接入真实税率。若仍见此提示，说明该税号未匹配或数据仍在加载；请切换到美国目的地查看实时真实数据。",
 "中国向け - 2026 年公式関税スケジュール（国務院関税税則委員会、2026-01-01 発効）は本番の実税率で公開済みです。この通知が表示される場合は、該当 HS が未照合、またはデータ読込中です。本番データは米国向けをご利用ください。",
 "Destino China: el arancel oficial 2026 (Comision de Aranceles del Consejo de Estado, vigente 2026-01-01) ya esta en vivo con tasas reales. Si ves esto, el codigo no coincidio o los datos aun cargan; usa el destino EE.UU. para datos reales.",
 "Ziel China: Der offizielle Zolltarif 2026 (Zolltarifkommission, ab 2026-01-01) ist mit echten Satzen live. Erscheint dieser Hinweis, wurde der Code nicht zugeordnet oder Daten laden noch; nutzen Sie das US-Ziel fur echte Daten.",
 "中國目的地 - 2026 年官方關稅稅則（國務院關稅稅則委員會，2026-01-01 生效）已接入真實稅率。若仍見此提示，表示該稅號未匹配或資料仍在載入；請切換到美國目的地查看即時真實資料。",
 "중국 목적지 - 2026년 공식 관세 일정(국무원 관세세칙위원회, 2026-01-01 발효)이 실제 세율로 라이브 상태입니다. 이 알림이 보이면 코드가 일치하지 않거나 데이터를 불러오는 중입니다. 실시간 실제 데이터는 미국 목적지를 이용하세요.",
 "Destinataire Chine : le tarif officiel 2026 (Commission des tarifs du Conseil d Etat, en vigueur 2026-01-01) est desormais en ligne avec des taux reels. Si cet avis s affiche, le code n a pas ete apparié ou les donnees chargent encore ; utilisez la destination Etats-Unis pour des donnees reelles.",
 "Destino China: a tarifa oficial 2026 (Comissao de Tarifas do Conselho de Estado, em vigor 2026-01-01) ja esta no ar com taxas reais. Se isto aparecer, o codigo nao foi correspondido ou os dados ainda carregam; use o destino EUA para dados reais.",
 "Destinazione Cina: la tariffa doganale ufficiale 2026 (Commissione tariffaria del Consiglio di Stato, in vigore 2026-01-01) e ora attiva con aliquote reali. Se vedi questo avviso, il codice non e stato abbinato o i dati stanno caricando; usa la destinazione USA per dati reali.",
]
assert len(new_vals) == 10, len(new_vals)
idx = {"n": 0}
pat = re.compile(r"cn_pending:[ \t]*(['\"])((?:(?!\1)[^\\]|\\.)*)\1")
def repl(m):
    q = m.group(1)
    v = new_vals[idx["n"]]
    idx["n"] += 1
    return "cn_pending: " + q + v + q
s2, n = pat.subn(repl, s)
print("replaced:", n)
assert n == 10, n
open(p, "w", encoding="utf-8").write(s2)
print("done")
