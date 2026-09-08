// build_hs_ssg.mjs — GEO 修复：把前 N 条真实税率快照进静态 JSON，
// 供 hs-codes.astro 服务端渲染进静态 HTML，使 AI 爬虫无需执行 JS 即可读到真税率。
//
// 仅用 node 内置模块（fs/path），不依赖任何 npm 包 → 本机与 CI 均可直接 `node` 运行。
// 设计：取自然序前 CAP 条（与客户端 render() 首屏顺序一致，避免加载闪烁）。

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

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

const usFull = loadJson('tariff_full.json');          // { code: {desc, base, ch99, ch99_rate} }
const cnFull = loadJson('tariff_full_cn.json');       // { meta, by_hs8 }

const usKeys = Object.keys(usFull);
const cnBy = (cnFull && cnFull.by_hs8) ? cnFull.by_hs8 : cnFull;
const cnKeys = Object.keys(cnBy);

const us = usKeys.slice(0, CAP).map(k => {
  const r = usFull[k] || {};
  return {
    code: k,
    desc: r.desc || '',
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
    name: r.name || '',
    mfn: (r.mfn === undefined ? null : r.mfn),
    general: (r.general === undefined ? null : r.general),
  };
});

// 高频/高价值锚点码：AI 最常被问的品类（服装/电子/鞋/玩具/家具等）。
// 单独成「热门」静态区块，与首屏自然序表互不干扰，避免客户端渲染顺序闪烁。
const US_ANCHORS = ['6109.10.00', '6203.42.40', '6403.99.30', '8517.62.00', '8471.30.00', '8528.72.64', '8703.23.00', '3926.90.99', '9503.00.00', '9403.60.80', '8450.11.00', '4202.92.90'];
const CN_ANCHORS = ['61091000', '62034290', '64039900', '85176200', '84713000', '85287200', '87032300', '39269000', '95030000', '94036000', '84501100', '42029200'];
// 锚点多为 HTS/HS 前缀（如 6203.42.40 实际键是 6203.42.40.10），精确匹配会漏；
// 用前缀解析：先精确，再按前缀首匹配（US 8 位、CN 6 位），保证高频品类都进静态 HTML。
function resolveKey(dict, anchor, prefixLen) {
  if (dict[anchor]) return anchor;
  const a = anchor.replace(/\./g, '');
  const keys = Object.keys(dict);
  const exact = keys.find(k => k.replace(/\./g, '') === a);
  if (exact) return exact;
  const pre = a.slice(0, prefixLen);
  return keys.find(k => k.replace(/\./g, '').startsWith(pre)) || null;
}
const featuredUs = US_ANCHORS
  .map(a => resolveKey(usFull, a, 6))
  .filter(Boolean)
  .map(k => { const r = usFull[k]; return { code: k, desc: r.desc || '', base: r.base, ch99: r.ch99 || '', ch99_rate: r.ch99_rate || 0 }; });
const featuredCn = CN_ANCHORS
  .map(a => resolveKey(cnBy, a, 6))
  .filter(Boolean)
  .map(k => { const r = cnBy[k]; return { code: k, ex: !!r.ex, name: r.name || '', mfn: r.mfn, general: r.general }; });

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
};

const outPath = path.join(dataDir, 'hs_codes_ssg.json');
fs.writeFileSync(outPath, JSON.stringify(out));
console.log(`[build_hs_ssg] wrote ${us.length} US + ${cn.length} CN rows → ${outPath}`);
console.log(`[build_hs_ssg] totals: US=${out.meta.usTotal}, CN=${out.meta.cnTotal}, as_of=${out.meta.generatedAt}`);
