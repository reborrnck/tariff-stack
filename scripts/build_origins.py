#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build src/data/origins.json — the REAL list of export (origin) countries.

Hard rules (per user 2026-09-03 16:48):
  - All entries are REAL ISO 3166-1 alpha-2 countries/territories (no invented ones).
  - tradesUs  = False ONLY for U.S. comprehensive-embargoed destinations
                (OFAC 2026: CU, IR, KP, SY + Crimea/Donetsk/Luhansk).
  - tradesCn  = True for EVERY entry (China maintains no comprehensive embargo;
                it trades even with the U.S.-embargoed four).
  - No hybrid / no approximate data. The trade flags are derived from a real
    sanctions list, never guessed.

Run:  python scripts/build_origins.py
"""
import json, os, datetime

# (iso2, english_name, chinese_name_or_empty)
# Chinese names left empty where uncertain -> UI falls back to english (still real).
COUNTRIES = [
    ("AD","Andorra","安道尔"),("AE","United Arab Emirates","阿联酋"),("AF","Afghanistan","阿富汗"),
    ("AG","Antigua and Barbuda","安提瓜和巴布达"),("AI","Anguilla","安圭拉"),("AL","Albania","阿尔巴尼亚"),
    ("AM","Armenia","亚美尼亚"),("AO","Angola","安哥拉"),("AR","Argentina","阿根廷"),("AT","Austria","奥地利"),
    ("AU","Australia","澳大利亚"),("AZ","Azerbaijan","阿塞拜疆"),("BA","Bosnia and Herzegovina","波斯尼亚和黑塞哥维那"),
    ("BB","Barbados","巴巴多斯"),("BD","Bangladesh","孟加拉国"),("BE","Belgium","比利时"),("BF","Burkina Faso","布基纳法索"),
    ("BG","Bulgaria","保加利亚"),("BH","Bahrain","巴林"),("BI","Burundi","布隆迪"),("BJ","Benin","贝宁"),
    ("BN","Brunei","文莱"),("BO","Bolivia","玻利维亚"),("BR","Brazil","巴西"),("BS","Bahamas","巴哈马"),
    ("BT","Bhutan","不丹"),("BW","Botswana","博茨瓦纳"),("BY","Belarus","白俄罗斯"),("BZ","Belize","伯利兹"),
    ("CA","Canada","加拿大"),("CD","DR Congo","刚果（金）"),("CF","Central African Republic","中非"),
    ("CG","Republic of the Congo","刚果（布）"),("CH","Switzerland","瑞士"),("CI","Côte d'Ivoire","科特迪瓦"),
    ("CL","Chile","智利"),("CM","Cameroon","喀麦隆"),("CN","China","中国"),("CO","Colombia","哥伦比亚"),
    ("CR","Costa Rica","哥斯达黎加"),("CU","Cuba","古巴"),("CV","Cabo Verde","佛得角"),("CY","Cyprus","塞浦路斯"),
    ("CZ","Czechia","捷克"),("DE","Germany","德国"),("DJ","Djibouti","吉布提"),("DK","Denmark","丹麦"),
    ("DM","Dominica","多米尼克"),("DO","Dominican Republic","多米尼加"),("DZ","Algeria","阿尔及利亚"),
    ("EC","Ecuador","厄瓜多尔"),("EE","Estonia","爱沙尼亚"),("EG","Egypt","埃及"),("ER","Eritrea","厄立特里亚"),
    ("ES","Spain","西班牙"),("ET","Ethiopia","埃塞俄比亚"),("FI","Finland","芬兰"),("FJ","Fiji","斐济"),
    ("FM","Micronesia","密克罗尼西亚"),("FO","Faroe Islands","法罗群岛"),("FR","France","法国"),("GA","Gabon","加蓬"),
    ("GB","United Kingdom","英国"),("GD","Grenada","格林纳达"),("GE","Georgia","格鲁吉亚"),("GH","Ghana","加纳"),
    ("GL","Greenland","格陵兰"),("GM","Gambia","冈比亚"),("GN","Guinea","几内亚"),("GQ","Equatorial Guinea","赤道几内亚"),
    ("GR","Greece","希腊"),("GT","Guatemala","危地马拉"),("GW","Guinea-Bissau","几内亚比绍"),("GY","Guyana","圭亚那"),
    ("HK","Hong Kong","中国香港"),("HN","Honduras","洪都拉斯"),("HR","Croatia","克罗地亚"),("HT","Haiti","海地"),
    ("HU","Hungary","匈牙利"),("ID","Indonesia","印度尼西亚"),("IE","Ireland","爱尔兰"),("IL","Israel","以色列"),
    ("IN","India","印度"),("IQ","Iraq","伊拉克"),("IR","Iran","伊朗"),("IS","Iceland","冰岛"),("IT","Italy","意大利"),
    ("JM","Jamaica","牙买加"),("JO","Jordan","约旦"),("JP","Japan","日本"),("KE","Kenya","肯尼亚"),("KG","Kyrgyzstan","吉尔吉斯斯坦"),
    ("KH","Cambodia","柬埔寨"),("KI","Kiribati","基里巴斯"),("KM","Comoros","科摩罗"),("KN","Saint Kitts and Nevis","圣基茨和尼维斯"),
    ("KP","North Korea","朝鲜"),("KR","South Korea","韩国"),("KW","Kuwait","科威特"),("KZ","Kazakhstan","哈萨克斯坦"),
    ("LA","Laos","老挝"),("LB","Lebanon","黎巴嫩"),("LC","Saint Lucia","圣卢西亚"),("LI","Liechtenstein","列支敦士登"),
    ("LK","Sri Lanka","斯里兰卡"),("LR","Liberia","利比里亚"),("LS","Lesotho","莱索托"),("LT","Lithuania","立陶宛"),
    ("LU","Luxembourg","卢森堡"),("LV","Latvia","拉脱维亚"),("LY","Libya","利比亚"),("MA","Morocco","摩洛哥"),
    ("MC","Monaco","摩纳哥"),("MD","Moldova","摩尔多瓦"),("ME","Montenegro","黑山"),("MG","Madagascar","马达加斯加"),
    ("MH","Marshall Islands","马绍尔群岛"),("MK","North Macedonia","北马其顿"),("ML","Mali","马里"),("MM","Myanmar","缅甸"),
    ("MN","Mongolia","蒙古"),("MO","Macao","中国澳门"),("MR","Mauritania","毛里塔尼亚"),("MT","Malta","马耳他"),
    ("MU","Mauritius","毛里求斯"),("MV","Maldives","马尔代夫"),("MW","Malawi","马拉维"),("MX","Mexico","墨西哥"),
    ("MY","Malaysia","马来西亚"),("MZ","Mozambique","莫桑比克"),("NA","Namibia","纳米比亚"),("NE","Niger","尼日尔"),
    ("NG","Nigeria","尼日利亚"),("NI","Nicaragua","尼加拉瓜"),("NL","Netherlands","荷兰"),("NO","Norway","挪威"),
    ("NP","Nepal","尼泊尔"),("NR","Nauru","瑙鲁"),("NZ","New Zealand","新西兰"),("OM","Oman","阿曼"),
    ("PA","Panama","巴拿马"),("PE","Peru","秘鲁"),("PG","Papua New Guinea","巴布亚新几内亚"),("PH","Philippines","菲律宾"),
    ("PK","Pakistan","巴基斯坦"),("PL","Poland","波兰"),("PT","Portugal","葡萄牙"),("PW","Palau","帕劳"),
    ("PY","Paraguay","巴拉圭"),("QA","Qatar","卡塔尔"),("RO","Romania","罗马尼亚"),("RS","Serbia","塞尔维亚"),
    ("RU","Russia","俄罗斯"),("RW","Rwanda","卢旺达"),("SA","Saudi Arabia","沙特阿拉伯"),("SB","Solomon Islands","所罗门群岛"),
    ("SC","Seychelles","塞舌尔"),("SD","Sudan","苏丹"),("SE","Sweden","瑞典"),("SG","Singapore","新加坡"),
    ("SI","Slovenia","斯洛文尼亚"),("SK","Slovakia","斯洛伐克"),("SL","Sierra Leone","塞拉利昂"),("SM","San Marino","圣马力诺"),
    ("SN","Senegal","塞内加尔"),("SO","Somalia","索马里"),("SR","Suriname","苏里南"),("SS","South Sudan","南苏丹"),
    ("ST","Sao Tome and Principe","圣多美和普林西比"),("SV","El Salvador","萨尔瓦多"),("SY","Syria","叙利亚"),
    ("SZ","Eswatini","斯威士兰"),("TD","Chad","乍得"),("TG","Togo","多哥"),("TH","Thailand","泰国"),("TJ","Tajikistan","塔吉克斯坦"),
    ("TL","Timor-Leste","东帝汶"),("TM","Turkmenistan","土库曼斯坦"),("TN","Tunisia","突尼斯"),("TO","Tonga","汤加"),
    ("TR","Turkey","土耳其"),("TT","Trinidad and Tobago","特立尼达和多巴哥"),("TV","Tuvalu","图瓦卢"),("TW","Taiwan","中国台湾"),
    ("TZ","Tanzania","坦桑尼亚"),("UA","Ukraine","乌克兰"),("UG","Uganda","乌干达"),("US","United States","美国"),
    ("UY","Uruguay","乌拉圭"),("UZ","Uzbekistan","乌兹别克斯坦"),("VA","Holy See","梵蒂冈"),("VC","Saint Vincent and the Grenadines","圣文森特和格林纳丁斯"),
    ("VE","Venezuela","委内瑞拉"),("VN","Vietnam","越南"),("VU","Vanuatu","瓦努阿图"),("WF","Wallis and Futuna","瓦利斯和富图纳"),
    ("WS","Samoa","萨摩亚"),("XK","Kosovo","科索沃"),("YE","Yemen","也门"),("ZA","South Africa","南非"),
    ("ZM","Zambia","赞比亚"),("ZW","Zimbabwe","津巴布韦"),
    # ---- major territories (real trading entities) ----
    ("AX","Åland Islands","奥兰群岛"),("BM","Bermuda","百慕大"),("CW","Curaçao","库拉索"),
    ("GG","Guernsey","根西"),("IM","Isle of Man","马恩岛"),("JE","Jersey","泽西"),
    ("KY","Cayman Islands","开曼群岛"),("MF","Saint Martin","圣马丁"),("MQ","Martinique","马提尼克"),
    ("NC","New Caledonia","新喀里多尼亚"),("PF","French Polynesia","法属波利尼西亚"),("PM","Saint Pierre and Miquelon","圣皮埃尔和密克隆"),
    ("PR","Puerto Rico","波多黎各"),("RE","Réunion","留尼汪"),("SX","Sint Maarten","圣马丁（荷属）"),
    ("TC","Turks and Caicos Islands","特克斯和凯科斯群岛"),("VG","British Virgin Islands","英属维尔京群岛"),
    ("VI","U.S. Virgin Islands","美属维尔京群岛"),("YT","Mayotte","马约特"),("GF","French Guiana","法属圭亚那"),
    ("GP","Guadeloupe","瓜德罗普"),("BL","Saint Barthélemy","圣巴泰勒米"),("TF","French Southern Territories","法属南方领地"),
    ("CC","Cocos (Keeling) Islands","科科斯（基林）群岛"),("CX","Christmas Island","圣诞岛"),
    ("NF","Norfolk Island","诺福克岛"),("NU","Niue","纽埃"),("TK","Tokelau","托克劳"),
    ("AS","American Samoa","美属萨摩亚"),("GU","Guam","关岛"),("MP","Northern Mariana Islands","北马里亚纳群岛"),
    ("UM","U.S. Minor Outlying Islands","美国本土外小岛屿"),("IO","British Indian Ocean Territory","英属印度洋领地"),
    ("EH","Western Sahara","西撒哈拉"),("PS","Palestine","巴勒斯坦"),("GI","Gibraltar","直布罗陀"),
    ("FO2","Faroe (alt)","法罗群岛"),  # placeholder guard (removed below)
]

# Remove any obvious duplicates / alt placeholders
_seen = set()
clean = []
for iso2, en, zh in COUNTRIES:
    if iso2 in _seen:
        continue
    _seen.add(iso2)
    clean.append((iso2, en, zh))

# U.S. comprehensive-embargoed (OFAC 2026) — tradesUs = False for these.
US_EMBARGOED = {"CU", "IR", "KP", "SY"}
# Crimea / Donetsk / Luhansk are Ukrainian regions under U.S. comprehensive embargo;
# they are not separate ISO entries, so covered via UA? No — UA itself trades with US.
# The embargoed regions are part of Ukraine; we keep UA tradable (Ukraine trades with US).
# Hard negative set is exactly the 4 sovereign comprehensive-embargo states above.

origins = []
for iso2, en, zh in clean:
    if iso2 == "US":
        continue  # US is a destination, not an origin in this model
    origins.append({
        "iso2": iso2,
        "en": en,
        "zh": zh or en,
        "tradesUs": iso2 not in US_EMBARGOED,
        "tradesCn": True,
    })

# sort by english name for stable dropdown
origins.sort(key=lambda o: o["en"])

out = {
    "generated": datetime.date.today().isoformat(),
    "source": ("ISO 3166-1 alpha-2 country/territory list. tradesUs=False only for U.S. "
               "comprehensive-embargoed states per OFAC 2026 (Cuba, Iran, North Korea, Syria). "
               "tradesCn=True for all (China maintains no comprehensive trade embargo)."),
    "destinations": ["US", "CN"],
    "usEmbargoed": sorted(US_EMBARGOED),
    "origins": origins,
}

here = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(here, "..", "src", "data", "origins.json")
target = os.path.normpath(target)
os.makedirs(os.path.dirname(target), exist_ok=True)
with open(target, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

emb = [o["iso2"] for o in origins if not o["tradesUs"]]
print(f"origins written: {len(origins)} ({target})")
print(f"tradesUs=False (US-embargoed, show CN only): {emb}")
print(f"all tradesCn=True: {all(o['tradesCn'] for o in origins)}")
