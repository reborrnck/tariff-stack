// Destination markets for the landed-cost calculator.
//
// Per the 2026-09-03 iron rule, destinations are EXACTLY two:
//   - US : full official stacked tariff (REAL — USITC HTS base MFN + Section 301
//          List 4A + forced-labour duty 9903.05.31 + MPF/HMF). Live now.
//   - CN : China destination. Official 2026 China Customs import tariff schedule
//          (国务院关税税则委员会, effective 2026-01-01) is NOW LIVE with REAL rates
//          parsed from the open government PDF (MFN + general + provisional). Never
//          fabricates a rate; unmatched HS codes return an honest "not matched" note.
//
// The previous 14-market chapter-level model (EU/GB/JP/KR/CA/AU/MX/VN/TH/SG/
// MY/AE/IN/BR) has been REMOVED entirely — those schedules were not individually
// verified per HS code and violated the all-real-data rule. The destination
// dropdown is driven by src/lib/origins.ts (DESTINATIONS = ["US","CN"]) so the
// origin→destination trade-linkage logic stays the single source of truth.

import type { Lang } from './i18n.ts';

const US_LABEL: Record<string, string> = {
  en: 'United States', zh: '美国', 'zh-TW': '美國', ja: 'アメリカ',
  ko: '미국', es: 'Estados Unidos', fr: 'États-Unis', pt: 'Estados Unidos',
  de: 'Vereinigte Staaten', it: 'Stati Uniti',
};

const CN_LABEL: Record<string, string> = {
  en: 'China', zh: '中国', 'zh-TW': '中國', ja: '中国',
  ko: '중국', es: 'China', fr: 'Chine', pt: 'China',
  de: 'China', it: 'Cina',
};

// Localized destination name for the dropdown + result headings.
// Only US and CN are valid destinations now.
export function destLabel(code: string, lang: Lang): string {
  if (code === 'US') return US_LABEL[lang] ?? US_LABEL.en;
  if (code === 'CN') return CN_LABEL[lang] ?? CN_LABEL.en;
  return US_LABEL.en; // safety fallback (UI never offers other codes)
}
