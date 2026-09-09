// build_hs_ssg.mjs — GEO 修复：把前 N 条真实税率快照进静态 JSON，
// 供 hs-codes.astro 服务端渲染进静态 HTML，使 AI 爬虫无需执行 JS 即可读到真税率。
//
// 仅用 node 内置模块（fs/path），不依赖任何 npm 包 → 本机与 CI 均可直接 `node` 运行。
// 设计：取自然序前 CAP 条（与客户端 render() 首屏顺序一致，避免加载闪烁）。
//
// resolveKey 已 export，供 validate_tariffs.mjs 复用（避免逻辑漂移）。
// 主逻辑包在 main() 内，仅在 `node build_hs_ssg.mjs` 直接运行时执行；
// 被 import 时不触发构建（否则校验脚本会顺带重写 hs_codes_ssg.json）。

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const dataDir = path.join(root, 'src', 'data');

const CAP = 200;

function loadJson(name) {
  const p = path.join(dataDir, name);
  if (!fs.existsSync(p)) {
    console.error(`[build_hs_ssg] MISSING ${p} — 跳过（构建前请确保数据已刷新）`);
    process.exit(0); // 不阻断 CI；缺失时 hs-codes.astro 仍有客户端渲染兜底
  }
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

// 锚点多为 HTS/HS 前缀（如 6203.42.40 实际键是 6203.42.40.10），精确匹配会漏；
// 用前缀解析：先精确，再按前缀首匹配（US 8 位、CN 6 位），保证高频品类都进静态 HTML。
// 关键修复：US HTS 的 6 位 heading（如 6203.42）本身不带税率（base=0），
// 若按"首个 prefix 匹配"会拿到 heading → 显示 Free 错。改为：优先选最长且有真税率
// 的子码（base>0），同长度按税率更高优先（更代表该类目），全 Free 才退化到 heading。
// ⚠️ exact 步骤仅在 anchor 长度 > prefixLen 时启用：6 位 anchor（如 '620342'）若做
// exact 会直接命中 6 位 heading（数字串相等），根本走不到 prefix 分支 → 又退回 heading。
export function resolveKey(dict, anchor, prefixLen) {
  // 仅当精确命中且带真税率（base>0）才直接返回；否则落到前缀匹配去选有税率的子码。
  // 否则 6 位 heading（如 6109/6203.42，base=0）会被精确命中直接返回 → 误显 Free。
  if (dict[anchor] && dict[anchor].base > 0) return anchor;
  const a = anchor.replace(/\./g, '');
  const keys = Object.keys(dict);
  // 仅在 anchor 比 prefix 长（如 8 位 anchor 配 8 位子码）时启用 digits-only exact，
  // 避免 6 位 anchor 误命中 6 位 heading。命中但 base=0 时跳过，继续找有税率子码。
  const exact = a.length > prefixLen
    ? keys.find(k => k.replace(/\./g, '').length === a.length && k.replace(/\./g, '') === a)
    : null;
  if (exact && dict[exact] && dict[exact].base > 0) return exact;
  const pre = a.slice(0, prefixLen);
  const cands = keys.filter(k => k.replace(/\./g, '').startsWith(pre));
  const withRate = cands
    .filter(k => dict[k] && dict[k].base > 0)
    .sort((x, y) => {
      const lenDiff = y.replace(/\./g, '').length - x.replace(/\./g, '').length;
      return lenDiff !== 0 ? lenDiff : (dict[y].base - dict[x].base);
    });
  return withRate[0] || cands[0] || null;
}

// 组合描述：沿 HS 层级从 heading(4位) 拼到叶子，丢弃纯 "Other" 节点，去重后拼接。
// 解决叶子节点只存 "Other"（如 6203.42.07="Other"）导致“描述看不懂”的问题；
// 同时做截断兜底——源数据 desc 被抓取脚本按固定长度砍断（连 heading 都中招，
// 如 "…other apparatus for the tra"），长描述且不以句末标点结尾 → 截到末空格加 …。
export function composeDesc(dict, leafKey) {
  if (!leafKey || !dict[leafKey]) return '';
  const chain = [leafKey];
  let cur = leafKey;
  while (cur.length > 4) {
    const i = cur.lastIndexOf('.');
    if (i <= 0) break;
    cur = cur.slice(0, i);
    chain.unshift(cur);
  }
  const parts = [];
  for (const k of chain) {
    const s = cleanDescPart(dict[k] && dict[k].desc);
    if (!s) continue;
    if (s.toLowerCase() === 'other') continue;
    if (parts.length && parts[parts.length - 1].toLowerCase() === s.toLowerCase()) continue;
    parts.push(s);
  }
  let out = parts.join(' — ');
  // 回退：整条 HS 链在源数据缺中间 heading（如 1101 只存 10 位子码）时，
  // composeDesc 会丢失全部文本。此时叶子原始 desc 即官方 "Other"（HTS 未另列名子类），
  // 带 HS 章号上下文显示 Ch.<章> Other，避免孤立 "Other" 用户看不懂。
  if (!out) {
    const ch = leafKey.replace(/\./g, '').slice(0, 2);
    out = `Ch.${ch} Other`;
  }
  return out;
}
function cleanDescPart(d) {
  let s = (d || '').replace(/:\s*$/, '').trim();
  if (!s) return '';
  if (s.length > 100 && !/[.!?:;'"”’)\]]$/.test(s)) {
    const i = s.lastIndexOf(' ');
    if (i > 20) s = s.slice(0, i) + '…';
  }
  return s;
}
// CN name 在源数据里带层级缩进横线（如 "---棉制"、"----局用电话交换机"），去前导横线/连字符。
export function cleanCnName(name) {
  return (name || '').replace(/^[-–—\u2013\u2014\s]+/, '').trim();
}

function main() {
  const usFull = loadJson('tariff_full.json');          // { code: {desc, base, ch99, ch99_rate} }
  const cnFull = loadJson('tariff_full_cn.json');       // { meta, by_hs8 }

  const usKeys = Object.keys(usFull);
  const cnBy = (cnFull && cnFull.by_hs8) ? cnFull.by_hs8 : cnFull;
  const cnKeys = Object.keys(cnBy);

  const us = usKeys.slice(0, CAP).map(k => {
    const r = usFull[k] || {};
    return {
      code: k,
      desc: composeDesc(usFull, k),
      base: (r.base === undefined ? null : r.base),
      ch99: r.ch99 || '',
      ch99_rate: (r.ch99_rate === undefined ? 0 : r.ch99_rate),
    };
  });

  const cn = cnKeys.slice(0, CAP).map(k => {
    const r = cnBy[k] || {};
    return {
      code: k,
      ex: !!r.ex,
      name: cleanCnName(r.name),
      mfn: (r.mfn === undefined ? null : r.mfn),
      general: (r.general === undefined ? null : r.general),
    };
  });

  // 高频/高价值锚点码：AI 最常被问的品类（服装/电子/鞋/玩具/家具等）。
  // 单独成「热门」静态区块，与首屏自然序表互不干扰，避免客户端渲染顺序闪烁。
  const US_ANCHORS = ['6109.10.00', '6203.42.40', '6403.99.30', '8517.62.00', '8471.30.00', '8528.72.64', '8703.23.00', '3926.90.99', '9503.00.00', '9403.60.80', '8450.11.00', '4202.92.90'];
  const CN_ANCHORS = ['61091000', '62034290', '64039900', '85176200', '84713000', '85287200', '87032300', '39269000', '95030000', '94036000', '84501100', '42029200'];

  const featuredUs = US_ANCHORS
    .map(a => resolveKey(usFull, a, 6))
    .filter(Boolean)
    .map(k => { const r = usFull[k]; return { code: k, desc: composeDesc(usFull, k), base: r.base, ch99: r.ch99 || '', ch99_rate: r.ch99_rate || 0 }; });
  const featuredCn = CN_ANCHORS
    .map(a => resolveKey(cnBy, a, 6))
    .filter(Boolean)
    .map(k => { const r = cnBy[k]; return { code: k, ex: !!r.ex, name: cleanCnName(r.name), mfn: r.mfn, general: r.general }; });

  // 高频 HS 6 位前缀专属详情页（GEO 改造②）：Top20 高频码，各解析代表性 US 10 位 HTS + CN 8 位 HS 真值。
  const TOP_CODES = ['610910','620342','640399','851762','847130','852872','870323','392690','950300','940360','845011','420292','871120','730890','841810','940161','610610','620462','732393','854231'];
  const details = TOP_CODES.map(code => {
    const usKey = resolveKey(usFull, code, 6);
    const cnKey = resolveKey(cnBy, code, 6);
    const u = usKey ? usFull[usKey] : null;
    const c = cnKey ? cnBy[cnKey] : null;
    return {
      code,
      chapter: code.slice(0, 2),
      us: u ? { code: usKey, desc: composeDesc(usFull, usKey), base: (u.base === undefined ? null : u.base), ch99: u.ch99 || '', ch99_rate: (u.ch99_rate === undefined ? 0 : u.ch99_rate) } : null,
      cn: c ? { code: cnKey, name: cleanCnName(c.name), mfn: (c.mfn === undefined ? null : c.mfn), general: (c.general === undefined ? null : c.general) } : null,
    };
  });

  const out = {
    meta: {
      usTotal: usKeys.length,
      cnTotal: cnKeys.length,
      generatedAt: new Date().toISOString().slice(0, 10),
      source: 'USITC Harmonized Tariff Schedule + China Tariff Commission 2026 schedule',
    },
    us,
    cn,
    featuredUs,
    featuredCn,
    details,
  };

  const outPath = path.join(dataDir, 'hs_codes_ssg.json');
  fs.writeFileSync(outPath, JSON.stringify(out));
  console.log(`[build_hs_ssg] wrote ${us.length} US + ${cn.length} CN rows → ${outPath}`);
  console.log(`[build_hs_ssg] totals: US=${out.meta.usTotal}, CN=${out.meta.cnTotal}, as_of=${out.meta.generatedAt}`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
