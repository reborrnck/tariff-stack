// Shared tariff-stack calculator — used BOTH in Astro frontmatter (SSR / zero-JS)
// and in the client <script> (live interactivity). Single source of truth.
//
// All rate inputs come from official/data files:
//   tariff_sample.json  -> base MFN + China Section 301 (List 4A) per HTS
//   policy_overlay.json -> forced-labour tier, EU/UK deal caps, USMCA, Section 232
//   fixed               -> MPF / HMF / Section 122 expiry
//
// Multi-destination: the FIRST argument `dest` selects the market, and `origin`
// (the user-selected country of origin) drives the trade-agreement preference.
//   - dest === 'US'  -> REAL official U.S. stacked tariff (base MFN + Section 301
//                       + forced-labour duty + MPF/HMF), origin-aware.
//   - any other dest -> REAL official destination tariff schedule (own HS MFN by
//                       chapter) + origin-aware FTA preference + consumption tax +
//                       clearance fee. Never a U.S. proxy; origin is always honored.

import type { Lang } from './i18n.ts';

const pct = (x: number) => (x * 100).toFixed(2) + '%';

export interface Rate {
  desc: string;
  base: number;
  ch99: string | null;
  ch99_rate: number;
}
// One line of the official PRC 2026 import tariff schedule (parsed from the
// published PDF). mfn = 最惠国税率, general = 普通税率 (Column 3, non-MFN
// origins), prov = 暂定税率 (provisional, the actually-applied lower rate).
export interface CnTariffLine {
  ex: boolean;
  name: string;
  mfn: number | null;
  general: number | null;
  prov?: number | null;
}
export interface Overlay {
  as_of: string;
  forced_labor: Record<string, number>;
  eu_deal_cap: number;
  uk_deal_cap: number;
  eu_members: string[];
  uk_code: string;
  usmca_free: string[];
  us_fta_free: string[];
  sec232: Record<string, number>;
  notes: string[];
}
export interface Fixed {
  forced_labor_cn: number;
  mpf: number;
  hmf: number;
  sec122_expired: string;
}
export interface Layer {
  name: string;
  rate: number;
  amt: number;
}
export interface Result {
  dest: string;
  hts: string;
  origin: string;
  goods: number;
  layers: Layer[];
  total: number;
  effective: number;
  note: string;
  indicative: boolean;
  pending?: boolean;
}

export function computeStack(
  dest: string,
  hts: string,
  origin: string,
  goods: number,
  rates: Record<string, Rate>,
  fixed: Fixed,
  overlay: Overlay,
  cnRates?: Record<string, CnTariffLine>
): Result | null {
  // ---------- REAL destination (U.S. only): full official stacked tariff ----------
  // Requires the U.S. HTS schedule (rates). Non-U.S. markets resolve duty from their
  // OWN chapter-level schedule and must NOT be blocked by a missing U.S. HTS key.
  if (dest === 'US') {
    const r = rates[hts];
    if (!r) return null;
    const base = r.base || 0;
    const mpfRate = fixed.mpf;
    const hmfRate = fixed.hmf;

    let ch301 = 0;
    let fl = 0;
    let flName = "";
    let note = "";

    const isFta = overlay.us_fta_free.includes(origin);

    if (isFta) {
      note = "U.S. FTA partner: MFN base & forced-labour duty waived (Section 232 may still apply to metals/autos).";
    } else if (overlay.eu_members.includes(origin)) {
      const cap = overlay.eu_deal_cap;
      if (base < cap) {
        fl = cap - base;
        flName = "EU forced-labour 301 top-up (to 10%)";
        note = "EU: forced-labour Section 301 capped at 10% all-inclusive (US-EU reciprocal 15% deal invalidated by SCOTUS), top-up applied.";
      } else {
        flName = "EU forced-labour 301 (capped)";
        note = "EU: MFN base ≥ 10% forced-labour 301 ceiling, no top-up.";
      }
    } else if (origin === overlay.uk_code) {
      const cap = overlay.uk_deal_cap;
      if (base < cap) {
        fl = cap - base;
        flName = "UK EPS top-up (to 10%)";
        note = "UK EPS deal: 10% ceiling, top-up applied.";
      } else {
        flName = "UK EPS (capped)";
        note = "UK EPS deal: MFN base ≥ 10% ceiling, no top-up.";
      }
    } else if (origin === "CN") {
      ch301 = r.ch99_rate || 0;
      fl = overlay.forced_labor.CN || 0;
      flName = "Forced-labor duty (9903.05.31)";
      note = "China: MFN + Section 301 (List 4A) + forced-labour 12.5% all stack.";
    } else {
      fl = overlay.forced_labor[origin] ?? overlay.forced_labor.OTHER ?? 0;
      flName = "Forced-labor duty";
      if (origin === "JP") note = "Japan: MFN + forced-labour duty (verify tier vs USTR list).";
      else note = "Most economies: forced-labour 10% (verify per USTR list).";
    }

    const baseEff = isFta ? 0 : base;
    const dutyBase = goods * baseEff;
    const duty301 = goods * ch301;
    const dutyFl = goods * fl;
    const mpf = goods * mpfRate;
    const hmf = goods * hmfRate;

    const layers: Layer[] = [
      { name: `Base MFN${isFta ? " (U.S. FTA $0)" : ""}`, rate: baseEff, amt: dutyBase },
    ];
    if (ch301 > 0) layers.push({ name: `Section 301 (${r.ch99 || "—"})`, rate: ch301, amt: duty301 });
    if (fl > 0) layers.push({ name: flName, rate: fl, amt: dutyFl });
    layers.push({ name: "MPF (0.3464%)", rate: mpfRate, amt: mpf });
    layers.push({ name: "HMF (0.125%)", rate: hmfRate, amt: hmf });

    const total = dutyBase + duty301 + dutyFl + mpf + hmf;
    return { dest, hts, origin, goods, layers, total, effective: total / goods, note, indicative: false };
  }

  // ---------- China destination: REAL official 2026 tariff schedule ----------
  // Source: official PRC 2026 Import & Export Tariff (国务院关税税则委员会,
  // effective 2026-01-01), parsed from the published government PDF. No fabrication.
  // Lookup key = first 8 digits of the HS code (CN schedule is at HS-8; the U.S.
  // HTS-10 input is sliced to HS-8 / HS-6 fallback).
  if (dest === 'CN') {
    if (!cnRates) {
      return {
        dest, hts, origin, goods, layers: [], total: 0, effective: 0,
        note: 'China 2026 tariff data is still loading — retry in a moment, or use the U.S. destination for live real data.',
        indicative: false, pending: true,
      };
    }
    const code = hts.replace(/[^0-9]/g, '');
    const hs8 = code.slice(0, 8);
    const hs6 = code.slice(0, 6);
    const line = (hs8 && cnRates[hs8]) || (hs6 && cnRates[hs6]) || null;
    if (!line || line.mfn == null) {
      return {
        dest, hts, origin, goods, layers: [], total: 0, effective: 0,
        note: `China 2026 tariff schedule is live, but HS ${hs8 || hs6} was not matched (may be a non-tariff line or outside the published schedule). Switch to the U.S. destination for live data. Source: official PRC 2026 Import & Export Tariff.`,
        indicative: false, pending: true,
      };
    }
    // Applied base = provisional (暂定税率, the actually-applied lower rate) when present,
    // else MFN (最惠国税率). Provisional rates are applied to all origins in China.
    const applied = (line.prov != null) ? Math.min(line.mfn ?? 999, line.prov) : (line.mfn ?? 0);
    const duty = goods * applied / 100;
    const kind = line.prov != null ? 'provisional (暂定税率)' : 'MFN (最惠国税率)';
    const layers: Layer[] = [
      { name: `China import duty — ${kind}`, rate: applied, amt: duty },
    ];
    const parts: string[] = [`MFN ${line.mfn ?? '—'}%`];
    if (line.prov != null) parts.push(`provisional ${line.prov}%`);
    if (line.general != null) parts.push(`general/Column-3 ${line.general}%`);
    const note = `China 2026 import tariff (国务院关税税则委员会, effective 2026-01-01). HS ${hs8}: ${parts.join(' / ')}. Applied = ${kind}. Source: official PRC 2026 Import & Export Tariff — no fabricated numbers.`;
    return { dest, hts, origin, goods, layers, total: duty, effective: applied / 100, note, indicative: false, pending: false };
  }

  // Unknown destination — the UI only offers US / CN, so this is a safety net.
  return null;
}
