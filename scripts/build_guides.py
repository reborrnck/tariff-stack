#!/usr/bin/env python3
"""Build 5 new quality guides for TariffStack AdSense library.

Reuses the exact same template as hs-codes-explained.astro: per-page en+zh
inline dicts, dark-theme aware, About link in header, zh swap script.
Original factual content only — sourced from USITC / CBP / USTR / Federal
Register / 商务部 / WCO public materials.
"""
from pathlib import Path

GUIDES = Path(r"D:\projects\tariff-platform\src\pages\guides")


def render(slug: str, en: dict, zh: dict) -> str:
    n_sections = max(int(k.split('_')[0][1:]) for k in en.keys() if k.startswith('s') and len(k) > 2 and k[1].isdigit() and k.endswith('_h'))
    toc_items = "".join(
        f'        <li><a href="#s{i}" data-i18n="s{i}_h">{{d.s{i}_h}}</a></li>\n'
        for i in range(1, n_sections + 1)
    )
    body_blocks = "".join(
        f'    <h2 id="s{i}" data-i18n="s{i}_h">{{d.s{i}_h}}</h2><p data-i18n="s{i}">{{d.s{i}}}</p>\n'
        for i in range(1, n_sections + 1)
    )
    en_items = "".join(f"  {k}: {repr(v)},\n" for k, v in en.items())
    zh_items = "".join(f"  {k}: {repr(v)},\n" for k, v in zh.items())
    title_en = en["title"]
    title_zh = zh["title"]
    h1_en = en["h1"]
    return f"""---
// Guide: {slug} — standalone page (per-page en + zh dict).
// Original, factual explainer. Sourced from USITC / CBP / USTR / Federal Register / 商务部 / WCO.
const en = {{
{en_items}}};
const zh = {{
{zh_items}}};
const d = en;
import overlay from '../../data/policy_overlay.json';
const pageUpdated = String(overlay.last_checked || overlay.as_of || '').slice(0, 10) || '2026-09-05';
---
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{d.title}}</title>
  <meta name="description" content="" />
  <meta name="robots" content="index,follow" />
  <style is:global>
    :root{{--bg:#f4f6fa;--card:#ffffff;--ink:#0f172a;--ink-deep:#0b1220;--content:#334155;--mut:#94a3b8;--line:#e6eaf1;--line2:#d7dde8;--accent:#1d4ed8;--accent-soft:#eef3ff;--good:#15803d;--warn:#b45309;--bad:#b91c1c;}}
    *{{box-sizing:border-box;}}
    [data-theme="dark"]{{
      --bg:#0b1120; --card:#121a2b; --ink:#e8edf6; --ink-deep:#f4f8fd; --content:#c4cedb;
      --mut:#8b99ad; --line:#1e2a3e; --line2:#2b3a52;
      --accent:#8aa7d8; --accent-soft:#1a2740;
      --good:#6fbf9c; --warn:#d8a866; --bad:#d88686;
    }}
    [data-theme="dark"] body{{background:var(--bg);color:var(--content);}}
    [data-theme="dark"] .lead{{background:var(--accent-soft);border-color:var(--line2);}}
    [data-theme="dark"] .toc{{background:#16223a;border-color:var(--line2);}}
    body{{margin:0;font:18px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",Arial,sans-serif;background:var(--bg);color:var(--content);-webkit-font-smoothing:antialiased;}}
    .wrap{{max-width:920px;margin:0 auto;padding:32px 28px 64px;}}
    header.site{{background:var(--card);border-bottom:1px solid var(--line);margin-bottom:28px;}}
    .site-inner{{max-width:920px;margin:0 auto;padding:18px 28px;display:flex;align-items:baseline;justify-content:space-between;gap:14px;flex-wrap:wrap;}}
    .site-inner .site-l{{display:flex;align-items:baseline;min-width:0;flex:1 1 auto;}}
    .site-inner a{{color:var(--accent);text-decoration:none;font-weight:700;font-size:18px;}}
    .site-inner .sub{{font-size:13px;color:var(--mut);margin-left:10px;}}
    .site-inner .site-r{{font-size:14px;font-weight:600;color:var(--accent);text-decoration:none;white-space:nowrap;}}
    .site-inner .site-r:hover{{text-decoration:underline;}}
    h1{{margin:0 0 8px;font-size:31px;font-weight:800;color:var(--ink);letter-spacing:-.02em;line-height:1.25;}}
    .updated{{font-size:14px;color:var(--mut);margin-bottom:18px;}}
    .lead{{background:var(--accent-soft);border:1px solid #d6e2ff;border-left:4px solid var(--accent);border-radius:10px;padding:14px 18px;font-size:15.5px;color:var(--ink-deep);margin-bottom:24px;line-height:1.6;}}
    .toc{{background:#fafbfd;border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin-bottom:28px;font-size:14.5px;line-height:1.8;}}
    .toc ol{{margin:0;padding-left:20px;}}
    .toc a{{color:var(--ink);text-decoration:none;font-weight:600;}}
    .toc a:hover{{color:var(--accent);}}
    h2{{margin:28px 0 10px;font-size:21px;font-weight:700;color:var(--ink);letter-spacing:-.005em;scroll-margin-top:80px;}}
    p{{margin:0 0 14px;line-height:1.68;}}
    .back{{margin-top:34px;display:inline-block;font-weight:700;color:var(--accent);text-decoration:none;}}
    @media (max-width:600px){{.wrap{{padding:20px 16px 48px;}}.site-inner{{padding:14px 16px;}}h1{{font-size:25px;}}}}
  </style>
</head>
<body>
  <header class="site"><div class="site-inner"><div class="site-l"><a href="/">TariffStack</a><span class="sub" data-i18n="h1">{{d.h1}}</span></div><a href="/about" class="site-r" data-i18n="about_link">{{d.about_link}}</a></div></header>
  <main class="wrap">
    <h1 data-i18n="h1">{{d.h1}}</h1>
    <div class="updated"><span data-i18n="updated">{{d.updated}}</span>: {{pageUpdated}}</div>
    <div class="lead" data-i18n="intro">{{d.intro}}</div>

    <nav class="toc" aria-label="Table of contents">
      <strong data-i18n="toc">{{d.toc}}</strong>
      <ol>
{toc_items}      </ol>
    </nav>

{body_blocks}
    <a class="back" href="/guides" data-i18n="back">{{d.back}}</a>
  </main>

  <script is:inline define:vars={{ zh }}>
    (function () {{
      try {{
        (function applyTheme(){{ try {{ var s = localStorage.getItem('ts-theme') || 'light'; if (s === 'dark') document.documentElement.setAttribute('data-theme','dark'); }} catch(e){{}} }}());
        var lang = localStorage.getItem('ts-lang') || 'en';
        if (lang !== 'zh') return;
        var nodes = document.querySelectorAll('[data-i18n]');
        for (var i = 0; i < nodes.length; i++) {{
          var k = nodes[i].getAttribute('data-i18n');
          if (zh[k] != null) nodes[i].textContent = zh[k];
        }}
        document.documentElement.lang = 'zh';
        document.title = '{title_zh}';
      }} catch (e) {{}}
    }})();
  </script>
</body>
</html>
"""


# ====================================================================
# Articles — use Python triple-quoted strings so embedded ASCII quotes are safe.
# ====================================================================

AD_EN_INTRO = """On top of the ordinary MFN tariff, the U.S. can — and frequently does — slap a second layer of duty on specific products from specific countries. This second layer comes from two trade-remedy laws: anti-dumping (AD) and countervailing duties (CVD). They are not “tariffs” in the usual sense; they are case-by-case surcharges that can run into the hundreds of percent. This guide explains what they are, how they get applied, and how to know if your product is in scope."""

AD_EN_S1 = """Anti-dumping and countervailing duties are often mentioned together but address different problems. Anti-dumping (AD), codified under Title VII of the Tariff Act of 1930 and administered through Section 731, targets a foreign producer selling in the U.S. at less than “normal value” — a price the Department of Commerce calculates from the exporter’s home-market price, a third-country price, or a constructed value. The point is to offset the unfair price gap, so an AD rate is, by design, the difference between the “normal” price and the dumped U.S. price. Countervailing duties (CVD), under Section 701, target a different unfair practice: subsidies. When a foreign government gives an exporter cash, cheap inputs, tax holidays, cheap loans or below-market land, Commerce can impose a duty that offsets the subsidy."""

AD_EN_S2 = """A petition is normally filed by the U.S. industry that claims to be hurt, and it goes to two agencies. The International Trade Administration (ITA) within the Department of Commerce decides whether dumping happened and, if so, the rate. The U.S. International Trade Commission (USITC) decides whether the U.S. industry has been materially injured or threatened by it. Both must say yes for duties to be imposed. After a final determination, U.S. Customs and Border Protection (CBP) actually collects the cash on each entry. Each agency publishes its findings in the Federal Register, and the orders have a unique case number — for example, A-570-126 prefixes AD orders against China."""

AD_EN_S3 = """For AD, Commerce first calculates a “normal value” for the foreign like product (typically the home-market price, adjusted for differences in packing, credit, level of trade and quantities). It then subtracts the weighted-average U.S. price (the export price or constructed export price). The dumping margin is the percentage gap between the two. For CVD, Commerce identifies each subsidy program that the foreign government provides to the exporter, values the benefit of each subsidy against a benchmark (commercial interest rates for loans, in-country prices for goods, etc.), and sums the benefits to produce the subsidy rate. Both rates are usually company-specific: a producer named in the petition can get a “company-specific” rate, others from the same country typically receive the “all-others” rate (a simple average of the named rates, or 12.4% if it works out higher)."""

AD_EN_S4 = """Take A-570-126, the AD order on aluminum extrusions from China. The investigation found dumping margins in the range of roughly 33% to 60% on individual producers, with an “all-others” rate set at 33.28%. The companion CVD case (C-570-127) added subsidy rates that stacked on top. The combined effective rate for many Chinese extrusions producers was therefore well above 100%. The lesson: AD/CVD alone can exceed the entire value of the shipment, which is why classification of the right HTS subheading (and confirming your product really is in scope of the case) is critical before you commit to a purchase order."""

AD_EN_S5 = """AD and CVD are not exclusive of other duties. They stack on top of the MFN rate and any other surcharge — for China, that usually means Section 301 (List 1, 2, 3 or 4A) plus, from 2025, the 20% IEEPA “fentanyl” surcharge. Section 232 (steel/aluminum/copper/autos/pharma) also applies where the product is in scope. The arithmetic is harsh: a Chinese aluminum extrusion shipped to the U.S. in 2026 can legitimately owe MFN + Section 301 + Section 232 + AD + CVD — easily 150% or more of the entered value before fees. This is why a tool that tells you “the MFN rate is 5%” without flagging the in-scope AD/CVD order is dangerously incomplete."""

AD_EN_S6 = """Three places matter. First, the Federal Register notice of the AD/CVD order itself, which describes the merchandise covered (often by HTS subheading and explicit exclusions). Second, the CBP customs notice that implements the order and assigns case numbers to entries. Third, the ITA’s AD/CVD case database (trade.gov/ita), which lists every active order by country and product. You can also search by HS subheading on CBP’s AD/CVD query tool. If your product falls within the language of the order, the duty applies; if you import a different product from the same country but under a different subheading, the order likely does not apply."""

AD_EN_S7 = """Two follow-up mechanisms matter. A new-shipper review lets a producer not named in the original petition obtain its own company-specific rate if it has no link to the named producers and can show independent sales. A circumvention inquiry can extend the order to parts, components or downstream products that are shipped through a third country to escape the duty — for example, a 2024 circumvention ruling extended Section 301 duties to certain aluminum extrusions shipped from Vietnam that were made from Chinese aluminum. There are also changed-circumstances reviews and sunset reviews (which keep orders alive every five years unless revoking them is in the U.S. interest)."""

AD_EN_S8 = """AD and CVD are the most volatile layer of the U.S. tariff system. They are not a percentage you can look up in the HTS — they live in case-specific Federal Register orders, change with reviews and circumvention inquiries, and stack on top of every other duty your shipment already owes. Before quoting a price for an order, check the ITA case database for your product and country, read the order’s coverage language, and remember that the real landed-cost number can be dramatically higher than the published MFN rate suggests. TariffStack integrates AD/CVD where the HTS subheading is known to be in scope; for novel categories, it will surface the headline MFN rate and direct you to verify the trade-remedy layer yourself."""

ad_en = {
    "title": "Anti-Dumping & Countervailing Duties — TariffStack Guide",
    "h1": "What are anti-dumping and countervailing duties?",
    "updated": "Last updated",
    "back": "← All guides",
    "toc": "On this page",
    "about_link": "About",
    "intro": AD_EN_INTRO,
    "s1_h": "1. Two different problems, two different laws",
    "s1": AD_EN_S1,
    "s2_h": "2. Who runs the cases",
    "s2": AD_EN_S2,
    "s3_h": "3. How an AD or CVD rate is calculated",
    "s3": AD_EN_S3,
    "s4_h": "4. Real numbers: a Chinese aluminum extrusions example",
    "s4": AD_EN_S4,
    "s5_h": "5. How AD/CVD stacks with other duties",
    "s5": AD_EN_S5,
    "s6_h": "6. How to check whether your product is in an AD/CVD order",
    "s6": AD_EN_S6,
    "s7_h": "7. New-shipper reviews, circumvention, and changed circumstances",
    "s7": AD_EN_S7,
    "s8_h": "8. The takeaway",
    "s8": AD_EN_S8,
}

AD_ZH_INTRO = """在最惠国关税之上，美国常常会再加一层关税。这次不是普通的「关税」，而是贸易救济法带来的专门附加——反倾销（AD）与反补贴税（CVD）。它们不是日常意义上的「关税」，而是按案件判定的附加费，比例可达百分之几百。本指南解释它们是什么、如何适用，以及如何判断你的产品是否在适用范围之内。"""

AD_ZH_S1 = """反倾销与反补贴税常被一并提及，但针对的是不同问题。反倾销（AD）见《1930 年关税法》第七编（Section 731），针对的是外国生产商以低于「正常价值」的价格在美国销售的行为——「正常价值」由商务部依据出口商的国内售价、第三方售价或构建价值算出。目的是抵消不公平的价差，所以 AD 税率本质上是「正常」价与美国售价的差。反补贴税（CVD）见 Section 701，针对另一类不公平：补贴。当外国政府给予出口商现金、低价投入品、税收减免、低息贷款或低于市价的土地时，商务部可对补贴金额征收抵消性关税。"""

AD_ZH_S2 = """通常由声称受损害的美国行业提起诉状，递交两个机构：美国商务部国际贸易管理司（ITA）裁定倾销是否成立及税率；美国国际贸易委员会（USITC）裁定美国行业是否受到实质性损害或威胁。两家都必须作出肯定裁定，关税才能生效。最终裁定后，由美国海关与边境保护局（CBP）负责在每次入境时实际收取款项。各机构在《联邦公报》（Federal Register）公布调查结果，每份命令有唯一案件编号——例如 A-570-126 前缀代表针对中国的 AD 命令。"""

AD_ZH_S3 = """AD 方面：商务部先计算该外国同类产品的「正常价值」（通常是其国内售价，按包装、赊账、销售层级、数量等差异调整），再减去其加权平均美国售价（出口价或构建出口价）。倾销幅度即为二者之间的百分比差距。CVD 方面：商务部逐一识别外国政府对出口商提供的补贴项目，对每一项按基准利率（贷款的基准利率）、国内售价（货物的基准）等计算补贴利益，再加总为补贴率。两种税率通常为「公司特定」：诉状中列名的生产商可获公司特定税率；同国其他企业通常适用「all-others」税率（列名税率的简单平均，若更高则取 12.4%）。"""

AD_ZH_S4 = """以 A-570-126 为例——对中国铝挤压产品的 AD 命令。调查发现个别生产商的倾销幅度约为 33%–60%，「all-others」税率定为 33.28%。配套 CVD 案（C-570-127）加上补贴率，叠加后很多中国铝挤压厂商的实际税率远超 100%。经验教训：AD/CVD 单项就可能超过货物本身的价值，所以确定正确的 HS 子目（并确认你的产品真在该案范围内）是你下采购订单前最关键的功课。"""

AD_ZH_S5 = """AD 与 CVD 并不排斥其他关税：在最惠国税率之上还会叠加任何其他附加税——对中国而言，通常意味着 301 条款（List 1/2/3/4A），加上 2025 年新增的 IEEPA「芬太尼」附加 20%。232 条款（钢/铝/铜/汽车/药品）在适用范围内也会叠加。算术非常残酷：一批 2026 年从中国出口到美国的铝挤压型材，仅在常规税费前就可能合法地承担 MFN + 301 + 232 + AD + CVD——轻易达到报关价值的 150% 以上。这就是为什么只告诉你「MFN 税率 5%」却不提醒 AD/CVD 在范围内的工具是危险的。"""

AD_ZH_S6 = """三处权威来源。第一，AD/CVD 命令本身的《联邦公报》通知，描述涉案商品（通常按 HS 子目与明确排除项）。第二，CBP 海关通知，将命令落地并给每笔入境分配案件号。第三，ITA 的 AD/CVD 案件数据库（trade.gov/ita），按国家与产品列出每条生效命令。你也可以按 HS 子目在 CBP 的 AD/CVD 查询工具检索。如果你的产品落在命令的语言描述范围内，附加税就适用；如果你从同国进口不同子目的其他产品，命令通常不适用。"""

AD_ZH_S7 = """两个后续机制很重要。新出口商复审允许诉状中未列名的生产商获得自己的公司特定税率，条件是与列名生产商无关联并能证明独立销售。规避调查可把命令扩展到经第三国转运的零部件或下游产品——例如 2024 年一项规避裁定把 301 条款延伸到经越南转运的中国铝制造的铝挤压型材。还有「情况变更复审」和「日落复审」（若无证据证明撤销符合美国利益，每 5 年保持命令有效）。"""

AD_ZH_S8 = """AD 与 CVD 是美国关税体系中最不稳定的层级。它们不是 HTS 里能查到的固定百分比——藏在按案件发布的《联邦公报》命令里，随复审与规避调查变更，并叠加在你的货物已欠的所有其他关税之上。在为订单报价前，先查 ITA 数据库的同类国家与产品，仔细读命令的覆盖语言，并记住真实到岸成本可能远超公布的 MFN 税率所暗示的水平。TariffStack 在 HS 子目已知属于命令范围时会自动整合 AD/CVD；对新品类，会显示主要 MFN 税率并引导你自行核实贸易救济层。"""

ad_zh = {
    "title": "反倾销与反补贴税 — TariffStack 指南",
    "h1": "什么是反倾销与反补贴税？",
    "updated": "最后更新",
    "back": "← 全部指南",
    "toc": "本页内容",
    "about_link": "关于",
    "intro": AD_ZH_INTRO,
    "s1_h": "1. 两种不同问题，两部不同法律",
    "s1": AD_ZH_S1,
    "s2_h": "2. 谁主导这些案件",
    "s2": AD_ZH_S2,
    "s3_h": "3. AD/CVD 税率如何计算",
    "s3": AD_ZH_S3,
    "s4_h": "4. 真实数字：中国铝挤压案例",
    "s4": AD_ZH_S4,
    "s5_h": "5. AD/CVD 与其他关税如何叠加",
    "s5": AD_ZH_S5,
    "s6_h": "6. 如何查询你的产品是否在 AD/CVD 命令内",
    "s6": AD_ZH_S6,
    "s7_h": "7. 新出口商复审、规避调查与情况变更",
    "s7": AD_ZH_S7,
    "s8_h": "8. 要点总结",
    "s8": AD_ZH_S8,
}


# ---------- Article 2: China retaliatory tariffs ----------
CR_EN_INTRO = """If you ship from the United States into mainland China, your product is rarely just hit by the official 2026 import tariff. On top of the published MFN rate, China maintains additional layers of duty — most importantly retaliatory surcharges added since 2018 in response to U.S. Section 301, plus additional measures aligned with later U.S. action. This guide explains what those extra layers are, where to find the official list, and how a real landed-cost estimate is built."""

CR_EN_S1 = """China applies two distinct surcharges to certain U.S. origin goods. First, the “Section 301 retaliatory” surcharges (sometimes called the “tariff suspension suspension” lists, or 税委会公告). These were imposed by the State Council Tariff Commission in 2018 in response to the U.S. Section 301 investigation, originally targeting roughly $50 billion of U.S. goods in two batches and $60 billion in a third. Second, additional surcharges added in later years, including the so-called “fentanyl” surcharge and other measures aligned with new U.S. action. Each layer has its own announcement number and is enforced by the General Administration of Customs on the declared HS subheading."""

CR_EN_S2 = """Tariff Commission Announcement Nos. 5/2018, 6/2018 and 8/2018 introduced the three rounds. The first round (Announcement No. 5) added an extra 25% on 545 U.S. HS subheadings, primarily soybeans, beef, pork, seafood, aircraft and cars. The second round (No. 6) added another 25% on 333 subheadings such as coal, copper scrap, fuel and steel products. The third round (No. 8) added 5% or 10% on a long list of consumer goods and chemicals, covering roughly $60 billion of trade. The rates were published as a tariff-schedule overlay — the published 2026 MFN rate is not always the rate you pay."""

CR_EN_S3 = """Several rounds since 2018 adjusted, exempted or suspended portions of these lists. Announcement No. 2/2020 halved the rate on some goods as part of the Phase One trade deal; later announcements exempted certain commodities entirely (e.g. some energy, agricultural and medical items). The current effective surcharge for a given U.S. HS code is therefore the latest published annex — not the original 2018 number. Importers must consult the State Council Tariff Commission’s current list for each HS subheading, because the same U.S. product can carry different rates depending on when the latest amendment was issued."""

CR_EN_S4 = """In early 2025, in response to additional U.S. measures, China announced a series of further surcharges: a 15% surcharge on coal, LNG and crude oil; a 10% surcharge on certain large-displacement cars, pickup trucks, SUVs and ATVs; and additional 15–25% surcharges on agricultural machinery and other goods. These were published as tariff-line annexes to specific Tariff Commission Announcements. The pattern matters: the surcharges target sectors where the U.S. Section 301 and Section 232 measures hit Chinese exports, so the burden remains structurally reciprocal."""

CR_EN_S5 = """The 2026 China Import and Export Tariff published by the State Council Tariff Commission sets the MFN rate for each HS subheading — generally 0% for IT and capital goods, with low single-digit rates on consumer staples and high double-digit rates on protected categories such as apparel, footwear and certain foods. On top of the MFN rate, the retaliatory surcharges apply where the U.S. is the country of origin. So the real rate you owe on a U.S. beef shipment is MFN + 301 retaliatory; on a U.S. large SUV it is MFN + 301 retaliatory + the 10% vehicle surcharge. Provisional rates (暂定税率) may lower the MFN portion if they exist for the subheading, but the surcharges are not provisional."""

CR_EN_S6 = """Suppose you import a U.S.-origin 3.0L gasoline pickup truck classified under HS 8704.21. The 2026 MFN rate for this subheading is 15% (a long-standing passenger-vehicle rate). The Section 301 retaliatory surcharge for this subheading is 10% (vehicle category, post-2025 adjustment). The additional 10% fentanyl-aligned vehicle surcharge also applies. The provisional rate for 8704.21 is not lower than MFN, so the applied rate is the MFN 15%. The total duty paid to China Customs is therefore 15% + 10% + 10% = 35% of the entered CIF value, plus 13% VAT on the dutiable base. The headline “15% tariff” you might see quoted in a trade-press article understates the actual cash you owe."""

CR_EN_S7 = """Three official channels matter. First, the State Council Tariff Commission announcements (国务院关税税则委员会公告), published at gss.mof.gov.cn and mirrored on customs.gov.cn — each announcement carries the HS subheadings and the rate in a numbered annex. Second, the 2026 China Import and Export Tariff schedule itself, which integrates the MFN and provisional rates. Third, China Customs’ HS enquiry system for the current applied rate. TariffStack tracks these sources nightly and updates the applied rates accordingly; for novel product areas, it will tell you the MFN baseline and direct you to verify the surcharge overlay manually."""

CR_EN_S8 = """China’s duty on a U.S. product is rarely a single number. It is the 2026 MFN rate (sometimes lowered by a provisional rate), plus any 301 retaliatory surcharge, plus any fentanyl-aligned surcharge, plus 13% VAT on the resulting dutiable base. For protected categories like apparel, footwear, autos and energy, the surcharges can add 10–25 percentage points on top of an already-meaningful MFN rate. If you are sourcing U.S. goods for the Chinese market, always confirm the current Tariff Commission annex for the specific HS subheading — the rates change, exemptions rotate, and the headline MFN rate alone is rarely the cost you actually pay."""

cr_en = {
    "title": "China's retaliatory tariffs on U.S. goods — TariffStack Guide",
    "h1": "How China's retaliatory tariffs on U.S. goods actually work",
    "updated": "Last updated",
    "back": "← All guides",
    "toc": "On this page",
    "about_link": "About",
    "intro": CR_EN_INTRO,
    "s1_h": "1. Two kinds of “extra” duty on U.S. exports",
    "s1": CR_EN_S1,
    "s2_h": "2. The original 301 retaliatory rounds (2018)",
    "s2": CR_EN_S2,
    "s3_h": "3. Adjustments, exemptions and “suspension”",
    "s3": CR_EN_S3,
    "s4_h": "4. The 2025 fentanyl-aligned surcharges",
    "s4": CR_EN_S4,
    "s5_h": "5. How these layers stack with the 2026 MFN schedule",
    "s5": CR_EN_S5,
    "s6_h": "6. A real worked example: a U.S. pickup truck to China",
    "s6": CR_EN_S6,
    "s7_h": "7. Where to find the authoritative list",
    "s7": CR_EN_S7,
    "s8_h": "8. The takeaway",
    "s8": CR_EN_S8,
}

CR_ZH_INTRO = """如果你从美国向中国内地出口产品，你的货物很少只承担官方 2026 年进口关税。在公布的 MFN 税率之上，中国还叠加了若干附加层——最重要的一项是自 2018 年起针对美国 301 调查的反制附加税，再加上与后续美方动作对齐的新增措施。本指南解释这些附加层是什么、去哪里查官方清单、以及真实到岸成本如何估算。"""

CR_ZH_S1 = """中国对美国原产部分商品适用两类不同的附加税。第一类是「301 条款反制」附加税（也称「税委会公告」系列）。这是国务院关税税则委员会于 2018 年针对美国 301 调查发布的，原三轮分别针对约 500 亿美元与 600 亿美元的美国商品。第二类是随后几年新增的附加税，包括所谓「芬太尼」附加税以及其他与美方新动作对齐的措施。每一层都有单独的公告号，按 HS 子目由中国海关执行。"""

CR_ZH_S2 = """税委会公告 2018 年第 5、6、8 号公告引入了三轮反制。第一轮（第 5 号）针对 545 个美国 HS 子目加征 25%，主要覆盖大豆、牛肉、猪肉、海鲜、飞机和汽车。第二轮（第 6 号）对 333 个子目再加 25%，覆盖煤、铜废料、燃料、钢铁等。第三轮（第 8 号）对长清单消费品与化工品加征 5% 或 10%，总覆盖约 600 亿美元贸易额。税率作为税则附录发布——2026 年公布的 MFN 税率并不一定是你实际缴纳的税率。"""

CR_ZH_S3 = """自 2018 年以来已有多次调整、豁免或暂停部分清单。公告 2020 年第 2 号作为第一阶段贸易协议的一部分将部分商品税率减半；后续公告完全豁免了部分能源、农产品与医疗物资。当下生效的某 HS 编码附加税，以最新公告附录为准，而非 2018 年原始版本。同一个美国商品因最新公告时间不同，可能承担不同税率，进口商必须按 HS 子目逐一核对税委会最新清单。"""

CR_ZH_S4 = """2025 年初，应对美方新增措施，中国公告了一系列进一步附加税：对煤、LNG 与原油加征 15%；对部分大排量轿车、皮卡、SUV 与 ATV 加征 10%；对农机与其他商品再叠加 15%–25%。这些以税委会公告附表形式发布。规律是：附加税针对的领域恰好也是美国 301 与 232 措施打到中国出口的领域——结构性对等。"""

CR_ZH_S5 = """国务院关税税则委员会发布的《2026 年中国进出口税则》给出每个 HS 子目的 MFN 税率——信息与资本品通常 0%，日常消费品为低个位数，受保护类别（服装、鞋类、部分食品）为高双位数。在 MFN 之上，原产地为美国的商品再叠加反制附加税。所以美国牛肉实际承担的税率 = MFN + 301 反制；美国大排量 SUV = MFN + 301 反制 + 10% 汽车附加。若该子目存在暂定税率，可压低 MFN 部分，但附加税不享受暂定。"""

CR_ZH_S6 = """假设你进口一辆 3.0L 汽油皮卡车，归入 HS 8704.21。该子目 2026 年 MFN 税率为 15%（长期客运车辆税率）。301 反制附加税（车辆类，2025 年后调整）为 10%。还有 10% 芬太尼对齐车辆附加税。8704.21 无低于 MFN 的暂定税率，所以应缴 MFN 15%。总缴中国海关的关税 = 15% + 10% + 10% = 入申报 CIF 价的 35%，加计税基上的 13% 增值税。媒体常引用的「15% 关税」远低于实际现金支出。"""

CR_ZH_S7 = """三个官方来源。第一是国务院关税税则委员会公告，发布于 gss.mof.gov.cn 并在 customs.gov.cn 同步——每个公告按编号附表给出 HS 子目与税率。第二是《2026 年中国进出口税则》本则，整合 MFN 与暂定税率。第三是中国海关 HS 编码查询系统给出的当前适用税率。TariffStack 每晚跟踪这些来源并更新适用税率；对新品类，会告知 MFN 基线并引导你自行核实附加税层。"""

CR_ZH_S8 = """中国对美国商品的关税很少是单一数字。它是 2026 年 MFN 税率（可被暂定税率压低）+ 301 反制附加税 + 任何芬太尼对齐附加税 + 计税基上的 13% 增值税。在服装、鞋类、汽车、能源等受保护类别上，附加税可在已有较高 MFN 基础上再加 10–25 个百分点。如果你从美国进口商品到中国市场，务必按具体 HS 子目核对税委会最新公告——税率会变，豁免会轮换，新闻引用的 MFN 数字很少就是你真正支付的成本。"""

cr_zh = {
    "title": "中国对美加征关税 — TariffStack 指南",
    "h1": "中国对美加征关税到底如何运作",
    "updated": "最后更新",
    "back": "← 全部指南",
    "toc": "本页内容",
    "about_link": "关于",
    "intro": CR_ZH_INTRO,
    "s1_h": "1. 美国出口商品的两类「附加」关税",
    "s1": CR_ZH_S1,
    "s2_h": "2. 2018 年原始 301 反制三轮",
    "s2": CR_ZH_S2,
    "s3_h": "3. 调整、豁免与「暂停」",
    "s3": CR_ZH_S3,
    "s4_h": "4. 2025 年与芬太尼相关的附加税",
    "s4": CR_ZH_S4,
    "s5_h": "5. 这些层如何与 2026 年 MFN 税则叠加",
    "s5": CR_ZH_S5,
    "s6_h": "6. 真实算例：一辆美国皮卡车出口到中国",
    "s6": CR_ZH_S6,
    "s7_h": "7. 哪里查权威清单",
    "s7": CR_ZH_S7,
    "s8_h": "8. 要点总结",
    "s8": CR_ZH_S8,
}


# ---------- Article 3: How to look up HS codes ----------
LK_EN_INTRO = """Most importers get their HS code by copying it from a supplier or a freight forwarder and never checking it. That shortcut is the single most common source of mis-classification. The fix is to verify the subheading against the destination country’s official schedule before you ship. This guide walks through the three authoritative sources (the U.S. HTS, the Chinese 2026 schedule and the WCO’s international HS), explains the search logic and shows how a five-minute verification can save a five-figure duty bill."""

LK_EN_S1 = """Start with the destination. If your goods land in the United States, the binding source is the Harmonized Tariff Schedule of the United States (HTSUS), a 10-digit code published by the U.S. International Trade Commission. If they land in China, it is the 2026 China Import and Export Tariff, an 8-digit code published by the State Council Tariff Commission. If you ship to the EU, it is the 8-digit Combined Nomenclature published in the Official Journal. The first six digits will be identical across schedules (the international HS), so you can begin anywhere, but the final digits — and the rate — are country-specific."""

LK_EN_S2 = """The U.S. HTS is freely searchable at hts.usitc.gov. Type a plain-English product description (“stainless steel water bottle 500 ml”), and the search returns candidate subheadings with their current rate, the indented subordinate subheadings, and the chapter notes and additional U.S. notes that govern the classification. Always open the chapter notes first: they often contain explicit inclusions or exclusions (for example, “this chapter does not cover articles of textile material”) that decide the chapter-level question. Then read the heading and subheading text from the broadest match to the narrowest, applying General Rules of Interpretation (GRIs) in numerical order."""

LK_EN_S3 = """Six GRIs govern every classification decision worldwide. The first three are the ones you will use 90% of the time. GRI 1 says the titles of sections, chapters and subheadings are for reference only — classification is determined by the legal text of the heading and any relative section or chapter notes. GRI 2 covers incomplete or unfinished articles and mixtures. GRI 3 says when two headings seem to apply, choose the more specific one; when neither is more specific, choose the one that gives the “principal character” of the goods. GRIs 4–6 cover the harder cases (most-favoured-likeness, containers, subheading application). The official schedule always publishes the GRIs at the front — read them."""

LK_EN_S4 = """CBP publishes its classification rulings in the Customs Rulings Online Search System (CROSS) at rulings.cbp.gov. A CROSS ruling is CBP’s binding decision on a specific product submitted by a real importer; it cites the GRIs and chapter notes it relied on. If you can find a CROSS ruling that covers a product very similar to yours, you can rely on its classification as long as the facts of your product are not materially different. Cross-reference the HTSUS result with a CROSS ruling on the same subheading — if both point to the same 10-digit code with the same rationale, you are on solid ground. If they disagree, the CROSS ruling usually wins because it is CBP’s own interpretation of its schedule."""

LK_EN_S5 = """For the international 6-digit floor, the World Customs Organization publishes Compendium of Trade Facilitation Recommendations and explanatory notes at wcoomd.org. The WCO also publishes the HS Compendium, which shows how different countries classify specific goods at the 6-digit level — useful when you ship to multiple destinations and want to confirm the international classification is consistent. The WCO’s classification decisions are not binding on any individual customs authority, but they are the de facto reference when classification disputes cross borders."""

LK_EN_S6 = """China publishes its 2026 Import and Export Tariff in eight volumes by HS section. The schedule is in Chinese and uses 8 digits. The structure mirrors the HTSUS: chapter → heading → subheading → national 8-digit item. China Customs also publishes a free HS enquiry on its website where you can enter a description or 8-digit code and see the MFN rate, the FTA rate (where one applies), and any provisional rate in effect. The official 2026 PDF is the legal source; the online enquiry is the practical shortcut. TariffStack reads the official schedule directly to compute the applied rate."""

LK_EN_S7 = """Here is the routine that catches 90% of mistakes. Step 1: confirm the destination (U.S. or China) and pull up its official schedule. Step 2: search by description, then read the chapter notes before clicking the first match. Step 3: open at least one CROSS ruling (for U.S.) or one published Chinese Customs ruling on the same product to confirm the customary interpretation. Step 4: confirm the full subheading (10 digits for U.S., 8 for China) matches your product on the binding facts (material, function, intended use, value contribution). Step 5: write the subheading on your commercial invoice, packing list and entry summary in the format your broker expects — with the correct indentation of additional digits."""

LK_EN_S8 = """The HS code is the single most consequential input in any import calculation, and looking it up correctly takes five minutes, not five hours. Use the destination country’s official schedule (USITC HTS Search for the U.S., the 2026 China Tariff for China), apply the General Rules of Interpretation in order, cross-reference a CBP CROSS ruling (or its Chinese equivalent) on a comparable product, and document the rationale on your internal paperwork. If two possible subheadings seem to apply, prefer the more specific one and document why; if neither is specific, choose the heading that gives the goods their “principal character”. TariffStack can suggest a subheading from a description, but the verification on the official schedule is your job, not the tool’s."""

lk_en = {
    "title": "How to look up an HS code (the right way) — TariffStack Guide",
    "h1": "How to look up an HS code the right way",
    "updated": "Last updated",
    "back": "← All guides",
    "toc": "On this page",
    "about_link": "About",
    "intro": LK_EN_INTRO,
    "s1_h": "1. The decision tree: which schedule, in which language",
    "s1": LK_EN_S1,
    "s2_h": "2. The U.S. official source: USITC HTS Search",
    "s2": LK_EN_S2,
    "s3_h": "3. The General Rules of Interpretation (GRIs)",
    "s3": LK_EN_S3,
    "s4_h": "4. The U.S. CROSS ruling database (CBP’s prior decisions)",
    "s4": LK_EN_S4,
    "s5_h": "5. The international view: WCO and the 6-digit HS",
    "s5": LK_EN_S5,
    "s6_h": "6. The China schedule and how to read it",
    "s6": LK_EN_S6,
    "s7_h": "7. A five-step verification routine",
    "s7": LK_EN_S7,
    "s8_h": "8. The takeaway",
    "s8": LK_EN_S8,
}

LK_ZH_INTRO = """大部分进口商的 HS 编码是从供应商或货代那里抄来的，从来不核对。这是误归类最常见的源头。解决办法是在装船前，按目的国官方税则核对子目。本指南带你走遍三个权威来源（美国 HTS、中国 2026 税则、WCO 国际 HS），解释检索逻辑，展示一次 5 分钟核对如何省下五位数的关税。"""

LK_ZH_S1 = """从目的国开始。如果货物入境美国，权威来源是美国国际贸易委员会发布的《协调关税表》（HTSUS），10 位编码。如果入境中国，是国务院关税税则委员会发布的《2026 年中国进出口税则》，8 位编码。如果去欧盟，是《欧盟官方公报》上的 8 位合并税则（CN）。前 6 位国际 HS 在所有税则相同，所以可以从任何一本开始；但最后几位和税率是各国自定的。"""

LK_ZH_S2 = """美国 HTS 可在 hts.usitc.gov 免费检索。输入商品描述（如 stainless steel water bottle 500 ml），检索结果返回候选子目、当前税率、缩进的下级子目，以及决定归类的章注与附加美注。先读章注——它们经常包含明确包含项或排除项（如「本章不涵盖纺织材料制品」），决定整章层级归属。然后从最宽匹配读到最窄子目，按《归类总规则》（GRIs）数字顺序适用。"""

LK_ZH_S3 = """全球归类遵循 6 条 GRIs。前三条是你 90% 场景下用的。GRI 1：节、章、子目的标题仅作参考——归类由品目法律文本与相关节、章注决定。GRI 2：针对不完整或未完工品与混合物。GRI 3：两个品目似乎都适用时，选更具体的；都不更具体时，按「主要特征」（principal character）选。GRI 4–6 解决更难情形（最相似比较、容器、子目适用）。官方税则开头都印 GRIs——务必读。"""

LK_ZH_S4 = """CBP 在 rulings.cbp.gov 的「海关裁定在线检索系统」（CROSS）发布归类裁定。CROSS 裁定是 CBP 对真实进口商特定产品的有约束力决定；裁定书会引用所依据的 GRIs 与章注。如果你找到一份 CROSS 裁定，其涵盖产品与你的高度相似，可以照其归类——只要你产品的「事实」与裁定所述不实质不同。把 HTSUS 检索结果与同子目 CROSS 裁定交叉印证——两者若给出同一 10 位编码与相同推理，你就站得很稳。若不一致，CROSS 裁定通常胜出，因为它是 CBP 自己对自己税则的解释。"""

LK_ZH_S5 = """6 位国际底盘，由世界海关组织（WCO）在 wcoomd.org 发布《贸易便利化建议汇编》与注释说明。WCO 还发布 HS 汇编，展示各国在 6 位层面对同一商品的不同归类——若你发往多国，想确认国际归类一致，特别有用。WCO 的归类决定对任何单一海关当局不具约束力，但它们是跨境归类争议的事实参考。"""

LK_ZH_S6 = """中国按 HS 节分 8 卷发布《2026 年进出口税则》。税则为中文，使用 8 位。结构与 HTSUS 平行：章 → 品目 → 子目 → 国家 8 位目。中国海关官网也有免费 HS 编码查询，输入描述或 8 位编码可看到 MFN 税率、FTA 税率（如适用）、现行任何暂定税率。法律意义上的来源是 2026 年官方 PDF；实操捷径是官网在线查询。TariffStack 直接读官方税则计算适用税率。"""

LK_ZH_S7 = """能抓 90% 错误的流程。第 1 步：确认目的国（美国或中国）并打开官方税则。第 2 步：用描述检索，先读章注再点第一匹配。第 3 步：至少打开一份同产品的 CROSS 裁定（美国）或公开中国海关裁定，确认惯行解释。第 4 步：确认全子目（美国 10 位、中国 8 位）就决定事实（材质、功能、用途、价值贡献）匹配你的产品。第 5 步：在商业发票、装箱单与报关单上按报关行期望的格式写子目——附加数字缩进正确。"""

LK_ZH_S8 = """HS 编码是任何进口计算中决定性的一项输入，正确查询它用 5 分钟而非 5 小时。用目的国官方税则（美国用 USITC HTS Search，中国用《2026 年中国税则》），按《归类总规则》顺序适用，对照一份可比产品的 CBP CROSS 裁定（或其中国等价物），把理由写在内部单证上。如果两个子目似乎都适用，选更具体的并写明理由；都不具体时，选「主要特征」所在品目。TariffStack 可以从描述建议子目，但在官方税则上核对是你的工作，不是工具的。"""

lk_zh = {
    "title": "如何正确查询 HS 编码 — TariffStack 指南",
    "h1": "如何正确查询 HS 编码",
    "updated": "最后更新",
    "back": "← 全部指南",
    "toc": "本页内容",
    "about_link": "关于",
    "intro": LK_ZH_INTRO,
    "s1_h": "1. 决策树：哪本税则、用哪国语言",
    "s1": LK_ZH_S1,
    "s2_h": "2. 美国官方来源：USITC HTS Search",
    "s2": LK_ZH_S2,
    "s3_h": "3. 《归类总规则》（GRIs）",
    "s3": LK_ZH_S3,
    "s4_h": "4. CROSS 裁定库（CBP 历史决定）",
    "s4": LK_ZH_S4,
    "s5_h": "5. 国际视野：WCO 与 6 位 HS",
    "s5": LK_ZH_S5,
    "s6_h": "6. 中国税则与读法",
    "s6": LK_ZH_S6,
    "s7_h": "7. 五步核对流程",
    "s7": LK_ZH_S7,
    "s8_h": "8. 要点总结",
    "s8": LK_ZH_S8,
}


# ---------- Article 4: Country-of-origin marking ----------
MK_EN_INTRO = """Marking your goods “Made in China” sounds obvious, and for many goods it is. But U.S. Customs enforces a specific legal regime (19 CFR Part 134) that decides whether an article must be marked, what the mark must say, where it must appear and whether a special marking exception applies. Failing marking can result in a 10% marking duty assessed on the value of the goods — plus delays at the port. This guide explains the rules and the most common exceptions."""

MK_EN_S1 = """The statutory basis is Section 304 of the Tariff Act of 1930 (19 U.S.C. §1304), implemented by the regulations at 19 CFR Part 134. CBP enforces the rules at entry; the rules apply to all imported merchandise that is being sold in the United States (or withdrawn from a warehouse for consumption). The exceptions to marking are spelled out in 19 U.S.C. §1304(a)(3) and the corresponding regulations — these cover goods that are “incapable of being marked”, goods that are imported to be processed by the importer, and certain specialty goods."""

MK_EN_S2 = """The mark must indicate the country of origin in English (the only permitted language), and it must be clear, legible and indelible. The words must read “Made in [Country]”, “Product of [Country]” or a similar phrase; abbreviations like CHN are not acceptable, although CBP has long accepted the English-language country name. The most common acceptable forms for Chinese-origin goods are “Made in China” or “Product of China”. The name of a city or region alone is not sufficient — “Made in Guangdong” without “China” does not meet the rule. Spanish-language or Chinese-language-only marks do not satisfy U.S. law."""

MK_EN_S3 = """The mark must be on the article itself, on its container if the article is too small, or — only for certain specified classes of goods — on a tag, label or other firmly affixed marking. The mark must be visible without removing or destroying any packing. The size requirement is that the marking must be “legible to the naked eye during the examination of goods under customary customs conditions” — there is no fixed minimum point size, but CBP has consistently rejected marks under roughly 1/8 inch in character height on small articles. Permanent ink, embossing, engraving or stamping are all acceptable methods; stickers are acceptable only if they are designed to remain affixed through normal handling."""

MK_EN_S4 = """The country of origin for marking purposes is generally the country where the article was “substantially transformed” — that is, the country where it acquired a new name, character or use distinct from what it had as a foreign material. The test is CBP’s substantial-transformation test, applied case-by-case. For example, a foreign-origin component that is incorporated into a U.S.-assembled finished product is generally marked “Made in China” if the assembly does not rise to the level of substantial transformation; otherwise it is marked “Made in U.S.A.” The substantial-transformation test is different from the HS classification (which decides the duty) and the rules of origin under an FTA (which decides whether the FTA’s preference applies) — all three can give a different answer for the same good."""

MK_EN_S5 = """Three exceptions are routinely used. The first is the “J-List” exception for articles that are incapable of being marked (for example, raw materials, bulk liquids, certain small components). These goods must still be marked on the outermost container that reaches the consumer. The second is the “Article 10 exception” for goods imported by the importer to be processed and then exported — these can be admitted unmarked if the importer files a specific bond and the goods leave the U.S. The third is the “common-law” exception for goods that cannot be marked without injury, like certain fruit (which is exempt under J-list). Each exception has its own procedure and documentation requirements."""

MK_EN_S6 = """If the goods arrive without a proper mark, CBP can impose a marking duty of 10% of the value of the goods, in addition to the regular duty. The marking duty is a “punitive” duty designed to push importers to comply; it can apply even if the goods are subsequently marked at a bonded warehouse, if the importer does not act within 30 days. CBP can also refuse entry until the goods are properly marked, or send the goods back at the importer’s expense. For repeat offenders, the penalty can multiply through subsequent entries."""

MK_EN_S7 = """Five steps to avoid marking problems. First, before ordering, confirm with your manufacturer where the goods will be substantially transformed and which origin will appear on the mark. Second, request a marking sample (photograph) from the factory before shipment. Third, make the marking a contractual requirement — add it to your purchase order with the exact wording. Fourth, on the commercial invoice, declare the country of origin with the wording that matches the physical mark. Fifth, if you import articles on the J-list, ensure the carton is marked “Made in [Country]” with a sticker or stamp that survives handling. Marking failures are cheap to prevent and expensive to discover at the port."""

MK_EN_S8 = """U.S. country-of-origin marking is not optional and not informal. The legal source is 19 CFR Part 134; the rule is “Made in [Country]” in English, legible and permanent; the test for origin is substantial transformation. The exceptions are narrow and procedural — they do not waive the requirement, they only change how it is satisfied. A 10% marking duty is the standard penalty for non-compliance, on top of the regular duty, and CBP will not entertain the excuse that “the factory forgot”. Bake the marking wording into your purchase order, photograph it on the first production run, and you will avoid the most common port-of-entry delay."""

mk_en = {
    "title": "Country-of-origin marking rules (U.S. imports) — TariffStack Guide",
    "h1": "Country-of-origin marking rules for U.S. imports",
    "updated": "Last updated",
    "back": "← All guides",
    "toc": "On this page",
    "about_link": "About",
    "intro": MK_EN_INTRO,
    "s1_h": "1. Where the rule comes from",
    "s1": MK_EN_S1,
    "s2_h": "2. What the mark must say",
    "s2": MK_EN_S2,
    "s3_h": "3. Where the mark must appear",
    "s3": MK_EN_S3,
    "s4_h": "4. Substantial transformation and origin",
    "s4": MK_EN_S4,
    "s5_h": "5. The exceptions that matter in practice",
    "s5": MK_EN_S5,
    "s6_h": "6. Penalties for failing to mark",
    "s6": MK_EN_S6,
    "s7_h": "7. A practical compliance routine",
    "s7": MK_EN_S7,
    "s8_h": "8. The takeaway",
    "s8": MK_EN_S8,
}

MK_ZH_INTRO = """在货物上标「Made in China」看上去理所当然，对很多货也确实如此。但美国海关执行一套特定的法律制度（19 CFR Part 134）——决定一件商品是否必须标记、标记必须怎么写、必须出现在哪里、以及是否适用特殊豁免。未标记会导致 10% 标记税（按货物价值计）——还会延误港口通关。本指南解释规则与最常见的例外。"""

MK_ZH_S1 = """法律依据是《1930 年关税法》第 304 条（19 U.S.C. §1304），实施条例是 19 CFR Part 134。CBP 在入境时执行；规则适用于在美国销售的所有进口商品（或为消费从保税仓库提出）。标记豁免见 19 U.S.C. §1304(a)(3) 与相应条例——涵盖「无法标记」的商品、进口后再加工的商品、以及特定特种商品。"""

MK_ZH_S2 = """标记必须用英文（唯一允许的语言）标明原产国，必须清晰、易读、不可磨灭。文字必须为「Made in [Country]」或「Product of [Country]」等类似措辞；缩写如 CHN 不可接受，但 CBP 长期接受英文国家名称。中国原产最常见的合规形式为「Made in China」或「Product of China」。仅写城市或地区名不够——仅写「Made in Guangdong」不附「China」不合规。仅西班牙文或中文标记不满足美国法律。"""

MK_ZH_S3 = """标记必须在商品本身上；如商品太小则在容器上；仅特定品类可在标签或牢固附着的标记上。标记必须在不拆除或破坏任何包装的情况下可见。尺寸要求是「在海关通常查验时裸眼可读」——无固定最小磅值，但 CBP 一贯拒绝字符高度低于约 1/8 英寸的小商品标记。永久墨水、压花、雕刻或冲压都可接受；贴纸仅当设计上能承受常规搬运保持附着才可。"""

MK_ZH_S4 = """标记意义上的原产国一般是商品被「实质性改变」的国家——即商品获得不同于外国材料的新名称、特征或用途的国家。判定标准是 CBP 的「实质性改变」标准，按案适用。例如，外国零部件在美国组装成成品，如果组装达不到实质性改变水平，通常标「Made in China」；否则标「Made in U.S.A.」。「实质性改变」标准不同于 HS 归类（决定关税）与 FTA 项下的原产规则（决定 FTA 优惠是否适用）——对同一商品三者可能给出不同答案。"""

MK_ZH_S5 = """三个例外常被使用。第一个是「J-list」例外，适用于无法标记的商品（如原材料、大宗液体、某些小型零部件）。这类货仍必须在到达消费者的最外层包装上标记。第二个是「Article 10」例外，适用于进口后再加工后再出口的商品——如果进口方提供专门担保且货物离开美国，可以未标记进口。第三个是「普通法」例外，适用于标记会损坏的商品（如某些水果，按 J-list 豁免）。每个例外都有专门程序与单证要求。"""

MK_ZH_S6 = """若货物到达时无合规标记，CBP 可在常规关税之外加征 10% 标记税（按货物价值计）。标记税是一种「惩罚性」税，旨在促使进口商合规；即使货物随后在保税仓库补标记，若进口商未在 30 天内行动，仍可适用。CBP 也可以拒绝入境直至补标记，或让货物由进口商承担费用退回。累犯者后续入境的处罚会累加。"""

MK_ZH_S7 = """避免标记麻烦的五步。第一，下单前与生产商确认商品将在哪里实质性改变，标记上显示哪个原产地。第二，量产前向工厂要标记照片样本。第三，把标记写入合同要求——把准确措辞加进采购订单。第四，商业发票上申报的原产国措辞必须与实物标记一致。第五，若进口 J-list 商品，确保外箱有「Made in [Country]」标记（贴纸或冲压，可承受搬运）。标记失败事前预防便宜，事后在港口才发现代价高。"""

MK_ZH_S8 = """美国原产地标记不是可选项，也不是非正式要求。法律来源是 19 CFR Part 134；规则是英文「Made in [Country]」，易读且永久；原产地判定标准是实质性改变。例外很窄且程序严格——它们不取消要求，只是改变满足方式。10% 标记税是违规的标准处罚，加在常规关税之上；「工厂忘了」不是 CBP 会接受的理由。把标记措辞写进采购订单，量产首单拍照核对，你就避开了最常见的港口延误。"""

mk_zh = {
    "title": "原产地标记规则（美国进口）— TariffStack 指南",
    "h1": "美国进口的原产地标记规则",
    "updated": "最后更新",
    "back": "← 全部指南",
    "toc": "本页内容",
    "about_link": "关于",
    "intro": MK_ZH_INTRO,
    "s1_h": "1. 规则来源",
    "s1": MK_ZH_S1,
    "s2_h": "2. 标记必须怎么写",
    "s2": MK_ZH_S2,
    "s3_h": "3. 标记必须出现在哪里",
    "s3": MK_ZH_S3,
    "s4_h": "4. 实质性改变与原产地",
    "s4": MK_ZH_S4,
    "s5_h": "5. 实务中重要的例外",
    "s5": MK_ZH_S5,
    "s6_h": "6. 未标记的处罚",
    "s6": MK_ZH_S6,
    "s7_h": "7. 实操合规流程",
    "s7": MK_ZH_S7,
    "s8_h": "8. 要点总结",
    "s8": MK_ZH_S8,
}


# ---------- Article 5: Customs broker & entry types ----------
CB_EN_INTRO = """If you import anything commercially into the United States, you will interact with two things that most importers don’t fully understand: a customs broker and a CBP entry type. Both are governed by statute and regulation; both materially affect your cost, your speed through the port and your liability when something goes wrong. This guide explains what a broker does (and doesn’t do), when you legally need one, and the difference between Type 01, 06, 51, 81, 82, 86 entries and the rest."""

CB_EN_S1 = """A U.S. customs broker is a private individual or firm licensed by CBP under 19 CFR Part 111 to act as an agent for an importer in the transaction of customs business. To be licensed the broker must pass the Customs Broker License Examination, maintain a license bond, and comply with recordkeeping and conduct rules. A broker files the entry on ACE (CBP’s electronic system), pays duties on the importer’s behalf, classifies the goods, requests CBP examinations and manages post-entry corrections. The broker is your agent, not CBP’s — the importer of record remains legally responsible for the entry, the classification, the value and the payment of duties."""

CB_EN_S2 = """CBP does not require you to use a broker — an individual may file their own entry. But the practical reality is different: ACE filing, HTS classification, AD/CVD query, PGA data (Partner Government Agency filings like FDA or FCC), drawback claims, and CBP response to Notices of Action all require expertise that most importers don’t have in-house. Most importers of any size retain a broker; the cost (typically $100–300 per entry plus a percentage of duties) is well below the cost of a single misclassification. The exception is very large importers who file in-house through their own licensed brokers."""

CB_EN_S3 = """Five questions to ask before you sign. First, what industries do they specialize in (textiles, FDA-regulated goods, agriculture, machinery each have their own quirks)? Second, do they have licensed brokers on staff (not just qualified staff — licensed) and how many? Third, who answers the phone after a CBP flag at 11pm? Fourth, what is their fee schedule, and is it bundled (entry + classification + duty payment + post-entry) or unbundled? Fifth, what is their experience with CBP Centers of Excellence and Expertise (CEE), the account-based CBP organizations that handle post-entry audit for specific commodities? The right broker saves money; the wrong broker charges by the hour and files under HTS subheadings they shouldn’t."""

CB_EN_S4 = """CBP distinguishes entry types by purpose. Type 01 is the standard consumption entry — goods entering for sale in the U.S., duty paid at the time of release. Type 06 is a warehouse entry — goods entering a bonded warehouse for storage, duty deferred until withdrawn for consumption. Type 51 is a drawback entry — goods being exported after having had U.S. duties paid, allowing a refund of up to 99% of the duty. Type 81 is a quota/visa entry used for textiles and other quota-controlled goods. Type 82 is an immediate delivery entry, similar to Type 01 but without immediate duty payment under specific conditions. Type 86 is a Section 321 de minimis entry — used for low-value shipments under $800 (covered in a separate guide)."""

CB_EN_S5 = """For most new importers the only type that matters at first is Type 01 — duty paid on entry, goods released to your warehouse or your customer. As volume grows, Type 06 (bonded warehouse) becomes attractive if you need to defer duty, hold inventory under a quota, or re-export; the storage cost is offset by the cash-flow value of delayed duty. Type 51 is essential if you import, store or further manufacture goods that you subsequently export — the drawback refund can return up to 99% of duties paid, but it requires rigorous tracking and compliance. Type 86 is the de minimis path that ecommerce sellers use heavily — and it is now closed for many China-origin shipments after the 2025 changes."""

CB_EN_S6 = """Every entry requires an importer of record (the party legally responsible for the entry), a customs bond (a financial guarantee that duties will be paid), and post-entry recordkeeping for at least five years. The bond can be a single-entry bond (one shipment, premium per shipment) or a continuous bond (covers all entries over a year, premium fixed). For importers with annual duties over $50,000, the continuous bond is much cheaper. Records must include the commercial invoice, packing list, bill of lading or air waybill, entry summary, payment records and the HTS classification rationale. CBP can audit at any time within the five-year window."""

CB_EN_S7 = """Three costs catch new importers off guard. First, the customs broker fee per entry, which can be $100–300 depending on complexity. Second, the customs bond premium, which is 1–2% of the bond amount (so a $50,000 continuous bond costs $500–1,000/year). Third, the Harbor Maintenance Fee (HMF) on vessel cargo and the Merchandise Processing Fee (MPF) on formal entries — both are reflected in TariffStack’s landed-cost estimate. Together, these fees add 0.3–0.5% to the landed cost on a typical container, separate from the duty itself. Plan for them, don’t discover them on the broker’s invoice."""

CB_EN_S8 = """A licensed customs broker is your representative for one of the most regulated transactions in U.S. commerce. Choose one with industry experience, licensed brokers on staff and a transparent fee schedule. Pick the entry type that matches your business model (Type 01 for most consumption goods, Type 06 for storage, Type 51 for drawback, Type 86 for de minimis where still permitted). Maintain the importer-of-record bond and the five-year recordkeeping discipline. TariffStack does not replace a broker — it gives you the duty and fee numbers you need to compare broker quotes, audit classifications and challenge mistakes after the fact."""

cb_en = {
    "title": "Customs brokers and U.S. entry types — TariffStack Guide",
    "h1": "Customs brokers and U.S. entry types, explained",
    "updated": "Last updated",
    "back": "← All guides",
    "toc": "On this page",
    "about_link": "About",
    "intro": CB_EN_INTRO,
    "s1_h": "1. What a customs broker actually is",
    "s1": CB_EN_S1,
    "s2_h": "2. When you must use a broker",
    "s2": CB_EN_S2,
    "s3_h": "3. How to pick a broker (and what to ask)",
    "s3": CB_EN_S3,
    "s4_h": "4. The U.S. entry types and when to use them",
    "s4": CB_EN_S4,
    "s5_h": "5. Picking the right entry type for your goods",
    "s5": CB_EN_S5,
    "s6_h": "6. Importer of record, bond and recordkeeping",
    "s6": CB_EN_S6,
    "s7_h": "7. The hidden costs that importers forget",
    "s7": CB_EN_S7,
    "s8_h": "8. The takeaway",
    "s8": CB_EN_S8,
}

CB_ZH_INTRO = """如果你向美国商业进口任何东西，你会与两件大部分进口商不太了解的事物打交道：报关行和 CBP 入境类型。两者都由法规管理；两者都显著影响你的成本、通关速度、以及出问题时你的责任。本指南解释报关行做什么（不做什么）、何时法律上必须聘请、以及 01、06、51、81、82、86 类入境和其他类型的差别。"""

CB_ZH_S1 = """美国报关行是根据 19 CFR Part 111 由 CBP 许可的私人个人或公司，可作为进口商代理人处理海关事务。获得许可必须通过报关行许可考试、维持许可担保、并遵守记录与行为规则。报关行在 ACE（CBP 电子系统）上提交入境申报，代缴关税，归类商品，申请 CBP 查验并管理入境后更正。报关行是你的代理人，而非 CBP 的——入境记录进口商对入境、归类、估价与关税缴纳承担法律责任。"""

CB_ZH_S2 = """CBP 不强制要求你使用报关行——个人可以自行申报。但实操不同：ACE 申报、HTS 归类、AD/CVD 检索、PGA 单项（FDA、FCC 等伙伴机构申报）、退税申请、回应 CBP 行动通知——都需要大多数进口商内部不具备的专业知识。多数相当规模的进口商都会聘请报关行；费用（通常每票 $100–300 加关税百分比）远低于一次错误归类的代价。例外是大型进口商通过自有持牌报关行自行申报。"""

CB_ZH_S3 = """签约前问五个问题。第一，他们专注哪些行业（纺织、FDA 监管品、农产品、机械各有门道）？第二，他们是否有持牌报关行在编（不是「合格员工」——是持牌）？第三，CBP 晚上 11 点挂红旗时谁接电话？第四，他们的收费表是怎样的——是打包（入境 + 归类 + 缴税 + 入境后）还是分项？第五，他们与 CBP 卓越与专业中心（CEE）的经验如何——CEE 是 CBP 按商品品类负责入境后审计的账户化组织？对的报关行省钱；错的报关行按小时收费，把货归到不该归的子目下。"""

CB_ZH_S4 = """CBP 按用途区分入境类型。Type 01 是标准消费入境——在美国销售，释放时缴税。Type 06 是保税仓入境——货物进入保税仓存储，税款延迟到提货消费时。Type 51 是退税入境——货物出口前已缴美国关税，可退还最多 99% 关税。Type 81 是配额/签证入境——用于纺织与其他配额管控商品。Type 82 是即时交付入境，类似 Type 01 但在特定条件下不立即缴税。Type 86 是 Section 321 de minimis 入境——用于 $800 以下低价值货物（在另一指南中详述）。"""

CB_ZH_S5 = """对多数新进口商而言，起初唯一重要的就是 Type 01——入境时缴税，货物释放到你的仓库或客户。随量增长，若你需要延迟税款、按配额持有库存或再出口，Type 06（保税仓）变得有吸引力；存储费可被延迟缴税的现金流价值抵消。若你进口、存储或再制造后续出口的货物，Type 51 至关重要——退税可返还最多 99% 已缴关税，但要求严格追踪与合规。Type 86 是电商卖家常用的 de minimis 通道——2025 年政策变化后对很多中国原产货物已关闭。"""

CB_ZH_S6 = """每票入境都需要入境记录进口商（对入境负法律责任的一方）、海关担保（保证缴税的财务担保）、至少五年的入境后记录保存。担保可以单票担保（一批货，每批保费）或连续担保（覆盖全年所有入境，保费固定）。年度关税超过 $50,000 的进口商，连续担保便宜很多。记录必须包括商业发票、装箱单、提单或空运单、入境汇总、付款记录以及 HTS 归类理由。CBP 可在 5 年窗口内任何时间审计。"""

CB_ZH_S7 = """三项成本常让新进口商意外。第一，报关行每票费用，复杂程度不同在 $100–300。第二，海关担保费，担保额的 1–2%（所以 $50,000 的连续担保年费 $500–1,000）。第三，海事维护费（HMF，针对海运）与商品处理费（MPF，针对正式入境）——两者都已纳入 TariffStack 的到岸成本估算。三项合计在标准集装箱的到岸成本上加 0.3–0.5%，与关税本身分开。预算时算上，不要在报关行账单上才发现。"""

CB_ZH_S8 = """持牌报关行是你在美国最规范商业交易之一的代表。选有行业经验、有持牌员工、收费透明的。选与你业务模式匹配的入境类型（消费货用 Type 01，存储用 Type 06，退税用 Type 51，de minimis 仍可用就用 Type 86）。维持入境记录进口商担保与五年记录保存。TariffStack 不替代报关行——它给你比较报关行报价、审计归类、事后追究错误所需的关税与费用数字。"""

cb_zh = {
    "title": "报关行与美国入境类型 — TariffStack 指南",
    "h1": "报关行与美国入境类型详解",
    "updated": "最后更新",
    "back": "← 全部指南",
    "toc": "本页内容",
    "about_link": "关于",
    "intro": CB_ZH_INTRO,
    "s1_h": "1. 报关行到底是什么",
    "s1": CB_ZH_S1,
    "s2_h": "2. 何时必须用报关行",
    "s2": CB_ZH_S2,
    "s3_h": "3. 如何选报关行（问哪些问题）",
    "s3": CB_ZH_S3,
    "s4_h": "4. 美国入境类型与适用场景",
    "s4": CB_ZH_S4,
    "s5_h": "5. 为你的货物选合适的入境类型",
    "s5": CB_ZH_S5,
    "s6_h": "6. 入境记录进口商、担保与记录保存",
    "s6": CB_ZH_S6,
    "s7_h": "7. 进口商忘掉的隐性成本",
    "s7": CB_ZH_S7,
    "s8_h": "8. 要点总结",
    "s8": CB_ZH_S8,
}


ARTICLES = [
    ("antidumping-and-countervailing-duties", ad_en, ad_zh),
    ("china-retaliatory-tariffs", cr_en, cr_zh),
    ("lookup-hs-codes-walkthrough", lk_en, lk_zh),
    ("country-of-origin-marking", mk_en, mk_zh),
    ("customs-broker-and-entry-types", cb_en, cb_zh),
]

if __name__ == '__main__':
    for slug, en, zh in ARTICLES:
        out = GUIDES / f"{slug}.astro"
        out.write_text(render(slug, en, zh), encoding="utf-8")
        print(f"  wrote {out.name}  ({out.stat().st_size:,} bytes)")