// validate_tariffs.mjs — TariffStack 全量数据 + 页面取数完整性校验。
//
// 目的：守住"官方真值"这一核心卖点，防止 ÷100 / resolveKey 错位 / 单位错乱 类 bug
// 再次随部署上线。仅用 node 内置模块，本机与 CI 均可直接 `node` 运行。
//
// 校验项：
//  1) US tariff_full.json：每条 base 必须是有限数且 ≥ 0（小数约定，0.165=16.5%）。
//     注意：美国从价税可合法超过 100%——花生超额关税 131.8%（存 1.318）、烟叶 350%（存 3.5）
//     均真实（已 USITC 核验）。故上界放宽为 base > 5（>500%，美国法定关税最高约 350%）才判
//     单位 bug（如把 16.5% 存成 16.5、把 350% 存成 350）。
//  2) CN tariff_full_cn.json：mfn/general 必须是百分点或 null（null=该子目无 mfn，合法）；
//     mfn ∈ [0,100]，general 应 ≥ mfn（WTO 最惠国≤普通）。越界即疑似数据错。
//  3) 已知真值抽样断言（6109.10.00=0.165 / 61091000 mfn=6 / 64039900 mfn=8）。
//  4) resolveKey 压力测试（核心 bug 防复发）：对站点实际使用的全部锚点 + Top20 详情码
//     + 一组边界 battery，断言——只要该前缀下存在 base>0 的真子码，resolveKey 不得返回
//     base==0 的 heading（否则页面会误显 Free）。
//  5) SSG 输出（hs_codes_ssg.json）抽样：us/featuredUs 的 base 仍在 [0,5]（容纳合法高税率），cn 的 mfn 仍在 [0,100]。
//
// 退出码：0 = 无违规（仅允许合法 null）；1 = 发现违规（CI 应据此阻断部署）。

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { resolveKey } from './build_hs_ssg.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(path.resolve(__dirname, '..'), 'src', 'data');

const load = (n) => JSON.parse(fs.readFileSync(path.join(dataDir, n), 'utf8'));
const usFull = load('tariff_full.json');
const cnFull = load('tariff_full_cn.json');
const ssg = load('hs_codes_ssg.json');

const violations = [];
const warns = [];
const log = (...a) => console.log(...a);
const v = (msg) => violations.push(msg);
const w = (msg) => warns.push(msg);

// ---------- 1) US 范围/单位 ----------
let usN = 0, usFree = 0, usRated = 0;
for (const [code, rec] of Object.entries(usFull)) {
  usN++;
  const b = rec && rec.base;
  if (typeof b !== 'number' || !isFinite(b)) { v(`US ${code}: base 非有限数 (${JSON.stringify(b)})`); continue; }
  if (b < 0) v(`US ${code}: base < 0 (${b})`);
  // 美国法定关税最高约 350%（烟叶 2401.10.65）；base > 5(>500%) 视为单位 bug（忘 ÷100）。
  // 合法高税率（花生 1.318/烟叶 3.5）在此放行。
  if (b > 5) v(`US ${code}: base > 5 (${b}) — 疑似单位 bug（应 ÷100，如 1.318=131.8%、3.5=350%）`);
  if (b === 0) usFree++; else usRated++;
}
log(`US: ${usN} 码，rated(${usRated}) + free(${usFree})`);

// ---------- 2) CN 范围/单位 ----------
const cnBy = cnFull.by_hs8 || cnFull;
let cnN = 0, cnNull = 0;
for (const [code, rec] of Object.entries(cnBy)) {
  cnN++;
  const mfn = rec && rec.mfn;
  const gen = rec && rec.general;
  if (mfn === null || mfn === undefined) { cnNull++; continue; }
  if (typeof mfn !== 'number' || !isFinite(mfn)) { v(`CN ${code}: mfn 非有限数 (${JSON.stringify(mfn)})`); continue; }
  if (mfn < 0) v(`CN ${code}: mfn < 0 (${mfn})`);
  if (mfn > 100) v(`CN ${code}: mfn > 100 (${mfn}) — 超出合理区间`);
  if (typeof gen === 'number' && gen < mfn) w(`CN ${code}: general(${gen}) < mfn(${mfn})`);
}
log(`CN: ${cnN} 码，null-mfn(${cnNull}) 为合法`);

// ---------- 3) 已知真值抽样断言 ----------
const expectUs = (code, val, label) => {
  const r = usFull[code];
  if (!r) { v(`抽样缺失 US ${code}`); return; }
  if (Math.abs(r.base - val) > 1e-9) v(`US ${code} base=${r.base} 期望≈${val} (${label})`);
};
const expectCn = (code, val, label) => {
  const r = cnBy[code];
  if (!r) { v(`抽样缺失 CN ${code}`); return; }
  if (typeof r.mfn === 'number' && Math.abs(r.mfn - val) > 1e-9) v(`CN ${code} mfn=${r.mfn} 期望≈${val} (${label})`);
};
expectUs('6109.10.00', 0.165, '棉T恤 16.5%');
expectCn('61091000', 6.0, '棉T恤 MFN 6%');
expectCn('64039900', 8.0, '皮鞋 MFN 8%');

// ---------- 4) resolveKey 压力测试（核心 bug 防复发）----------
const US_ANCHORS = ['6109.10.00', '6203.42.40', '6403.99.30', '8517.62.00', '8471.30.00', '8528.72.64', '8703.23.00', '3926.90.99', '9503.00.00', '9403.60.80', '8450.11.00', '4202.92.90'];
const CN_ANCHORS = ['61091000', '62034290', '64039900', '85176200', '84713000', '85287200', '87032300', '39269000', '95030000', '94036000', '84501100', '42029200'];
const TOP_CODES = ['610910','620342','640399','851762','847130','852872','870323','392690','950300','940360','845011','420292','871120','730890','841810','940161','610610','620462','732393','854231'];
// 边界 battery：各种长度/有无点，专打 6位 heading 误命中
const battery = [
  '6109','610910','6109.10','6109.10.00','6203','620342','6203.42','6403','640399','6403.99',
  '8528','852872','8703','870323','3926','392690','0101','010121','9503','9403','8517','851762',
  '8471','847130','8450','845011','4202','420292','7308','730890','8542','854231','6106','610610',
  '6204','620462','7323','732393','8418','841810','9401','940161'
];

function checkResolve(dict, anchors, prefixLen, tag) {
  for (const a of anchors) {
    const k = resolveKey(dict, a, prefixLen);
    if (!k) { v(`${tag} resolveKey('${a}') => null`); continue; }
    const r = dict[k];
    const da = a.replace(/\./g, '');
    const pre = da.slice(0, prefixLen);
    const hasRatedSub = Object.keys(dict).some(c => {
      const dc = c.replace(/\./g, '');
      return dc.startsWith(pre) && dict[c] && dict[c].base > 0;
    });
    const isZero = !r || r.base === 0 || r.base === null || r.base === undefined;
    if (isZero && hasRatedSub) {
      v(`${tag} resolveKey('${a}') => '${k}' base=${r ? r.base : 'n/a'} 但该前缀下存在 base>0 真子码 — 页面会误显 Free`);
    }
  }
}
checkResolve(usFull, [...US_ANCHORS, ...TOP_CODES, ...battery], 6, 'US');
checkResolve(cnBy, [...CN_ANCHORS, ...TOP_CODES, ...battery], 6, 'CN');

// ---------- 5) SSG 输出抽样 ----------
for (const r of ssg.us) {
  if (typeof r.base !== 'number' || r.base < 0 || r.base > 5) v(`SSG.us ${r.code}: base 越界 (${r.base})`);
}
for (const r of ssg.featuredUs) {
  if (typeof r.base !== 'number' || r.base < 0 || r.base > 5) v(`SSG.featuredUs ${r.code}: base 越界 (${r.base})`);
}
for (const r of ssg.cn) {
  if (r.mfn !== null && (typeof r.mfn !== 'number' || r.mfn < 0 || r.mfn > 100)) v(`SSG.cn ${r.code}: mfn 越界 (${r.mfn})`);
}
for (const r of ssg.featuredCn) {
  if (r.mfn !== null && (typeof r.mfn !== 'number' || r.mfn < 0 || r.mfn > 100)) v(`SSG.featuredCn ${r.code}: mfn 越界 (${r.mfn})`);
}
// SSG details：US/CN 真值不得越界
for (const d of ssg.details) {
  if (d.us && (typeof d.us.base !== 'number' || d.us.base < 0 || d.us.base > 5)) v(`SSG.details ${d.code} US base 越界 (${d.us.base})`);
  if (d.cn && d.cn.mfn !== null && (typeof d.cn.mfn !== 'number' || d.cn.mfn < 0 || d.cn.mfn > 100)) v(`SSG.details ${d.code} CN mfn 越界 (${d.cn.mfn})`);
}

// ---------- 报告 ----------
log(`\n==== 校验 ${violations.length === 0 ? 'PASS ✅' : 'FAIL ❌'} ====`);
log(`违规 ${violations.length} 条，警告 ${warns.length} 条`);
if (warns.length) { log('\n-- 警告（不阻断）--'); warns.slice(0, 20).forEach(x => log('  ! ' + x)); }
if (violations.length) { log('\n-- 违规 --'); violations.slice(0, 60).forEach(x => log('  X ' + x)); }
process.exit(violations.length ? 1 : 0);
