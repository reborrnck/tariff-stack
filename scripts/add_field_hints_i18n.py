import re

path = "src/lib/i18n.ts"
src = open(path, encoding="utf-8").read()

langs = ["en", "zh", "ja", "es", "de", "zht", "ko", "fr", "pt", "it"]
trans = {
    "en": ("U.S. destination uses a 10-digit HTS code — e.g. 6109.10.00",
           "China destination uses an 8-digit HS code — e.g. 6109.10",
           "Declared value (tariff assessed in CNY)"),
    "zh": ("美国目的地使用 10 位 HTS 编码 — 例如 6109.10.00",
           "中国目的地使用 8 位 HS 编码 — 例如 6109.10",
           "申报货值（关税以人民币计征）"),
    "zht": ("美國目的地使用 10 位 HTS 編碼 — 例如 6109.10.00",
            "中國目的地使用 8 位 HS 編碼 — 例如 6109.10",
            "申報貨值（關稅以人民幣計徵）"),
    "ja": ("米国向けは 10 桁の HTS コード（例: 6109.10.00）",
           "中国向けは 8 桁の HS コード（例: 6109.10）",
           "申告貨物価値（関税は人民元で算定）"),
    "ko": ("미국은 10자리 HTS 코드 사용 — 예: 6109.10.00",
           "중국은 8자리 HS 코드 사용 — 예: 6109.10",
           "신고 물품 가액 (관세는 위안화 기준)"),
    "es": ("EE. UU. usa un codigo HTS de 10 digitos — p. ej. 6109.10.00",
           "China usa un codigo HS de 8 digitos — p. ej. 6109.10",
           "Valor declarado (arancel en CNY)"),
    "de": ("USA verwenden einen 10-stelligen HTS-Code — z. B. 6109.10.00",
           "China verwendet einen 8-stelligen HS-Code — z. B. 6109.10",
           "Angemeldeter Wert (Zoll in CNY)"),
    "fr": ("Etats-Unis : code HTS a 10 chiffres — ex. 6109.10.00",
           "Chine : code HS a 8 chiffres — ex. 6109.10",
           "Valeur declaree (droits en CNY)"),
    "pt": ("EUA usam um codigo HTS de 10 digitos — ex. 6109.10.00",
           "China usa um codigo HS de 8 digitos — ex. 6109.10",
           "Valor declarado (tarifa em CNY)"),
    "it": ("Stati Uniti: codice HTS a 10 cifre — es. 6109.10.00",
           "Cina: codice HS a 8 cifre — es. 6109.10",
           "Valore dichiarato (diritti in CNY)"),
}


def detect_quote(block_text):
    if re.search(r": '", block_text):
        return "'"
    if re.search(r': "', block_text):
        return '"'
    return "'"


out = src
for lang in langs:
    m = re.search(r"const " + re.escape(lang) + r": Dict = \{", out)
    if not m:
        print("WARN block not found:", lang)
        continue
    start = m.end()
    rest = out[start:]
    mm = re.search(r"\n\};", rest)
    if not mm:
        print("WARN close not found:", lang)
        continue
    close_pos = start + mm.start() + 1  # index of '}' in the closing '};'
    q = detect_quote(out[start:start + 500])
    us, cn, gl = trans[lang]
    insert = "  hs_hint_us: %s%s%s,\n  hs_hint_cn: %s%s%s,\n  goods_label_cn: %s%s%s,\n" % (
        q, us, q, q, cn, q, q, gl, q)
    out = out[:close_pos] + insert + out[close_pos:]

open(path, "w", encoding="utf-8").write(out)
print("done; inserted for", langs)
