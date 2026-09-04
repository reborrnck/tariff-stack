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

// Section 232 scope classifier.
// Maps an HTS code to the applicable IN-FORCE Section 232 measure(s) using the
// published USTR/CBP 232 proclamation scopes at HS chapter/heading level.
// 232 duties are ADDITIVE on top of MFN (and 301 where applicable) and, per the
// policy note, still apply to U.S. FTA partners (MX/CA) for metals/autos.
//
// PRECISION NOTE (honest limitation): the primary(50%) vs derivative(25%) sub-split
// within the metal chapters (72/73/74/76) is approximated at CHAPTER level — all
// primary metal articles in these chapters are charged the 50% rate; the separate
// 25% "derivatives" tier is NOT yet separately distinguished, so further-processed
// metal goods may be over-stated by up to 25 points. Refine with the official CBP
// 232 annex list when higher precision is required. Future-effective measures
// (pharma 2026-09-29, polysilicon 2026-12-04) are gated by their effective date.
function sec232Matches(
  hts: string,
  overlay: Overlay,
  now: Date
): { rate: number; label: string }[] {
  const code = hts.replace(/[^0-9]/g, '');
  const ch = code.slice(0, 2);
  const hs4 = code.slice(0, 4);
  const s = overlay.sec232;
  const out: { rate: number; label: string }[] = [];
  const inForce = (eff?: string) => !eff || now >= new Date(eff + 'T00:00:00Z');

  // Autos & parts — 25% (Chapter 87, headings 8701–8708)
  if (ch === '87' && ['8701', '8702', '8703', '8704', '8705', '8708'].includes(hs4)) {
    out.push({ rate: s.autos_parts, label: 'Section 232 — autos & parts (25%)' });
  }
  // Lumber — 10% (Chapter 44)
  if (ch === '44') {
    out.push({ rate: s.lumber, label: 'Section 232 — lumber (10%)' });
  }
  // Drones over 25kg — 100% (eff 2026-09-03, Chapter 88 / 8806)
  if (ch === '88' && hs4 === '8806' && inForce('2026-09-03')) {
    out.push({ rate: s.drones_over_25kg_eff_2026_09_03, label: 'Section 232 — drones >25kg (100%, eff 2026-09-03)' });
  }
  // Polysilicon — 15% (eff 2026-12-04, 2804.61)
  if (hs4 === '2804' && code.slice(4, 6) === '61' && inForce('2026-12-04')) {
    out.push({ rate: s.polysilicon_eff_2026_12_04, label: 'Section 232 — polysilicon (15%, eff 2026-12-04)' });
  }
  // Pharmaceuticals — 100% (eff 2026-09-29, Chapters 29/30)
  if ((ch === '29' || ch === '30') && inForce('2026-09-29')) {
    out.push({ rate: s.pharma_eff_2026_09_29, label: 'Section 232 — pharmaceuticals (100%, eff 2026-09-29)' });
  }
  // Steel / aluminum / copper — 50% (primary articles, Chapters 72/73/74/76)
  if (ch === '72' || ch === '73' || ch === '74' || ch === '76') {
    out.push({ rate: s.steel_alum_copper, label: 'Section 232 — steel/alum/copper (50%)' });
  }
  return out;
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
      note = "U.S. FTA partner: MFN base & forced-labour duty waived (Section 232 still applies where in scope, e.g. metals/autos).";
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

    // Section 232 — real, in-force 232 measures (additive on top of MFN; still
    // applies to U.S. FTA partners for metals/autos per policy note).
    const s2 = sec232Matches(hts, overlay, new Date());
    let duty232 = 0;
    for (const m of s2) {
      const amt = goods * m.rate;
      duty232 += amt;
      layers.push({ name: m.label, rate: m.rate, amt });
    }

    layers.push({ name: "MPF (0.3464%)", rate: mpfRate, amt: mpf });
    layers.push({ name: "HMF (0.125%)", rate: hmfRate, amt: hmf });

    const total = dutyBase + duty301 + dutyFl + duty232 + mpf + hmf;
    if (s2.length) note += ` Section 232 applied: ${s2.map((m) => m.label.split(' — ')[1] ?? m.label).join(', ')}.`;
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
