// Origin (export country) master list + destination-linkage logic.
//
// Per user 2026-09-03 16:48 iron rule:
//   - All origins are REAL ISO 3166-1 countries (see scripts/build_origins.py).
//   - Selecting an origin must filter the DESTINATION dropdown to only countries
//     that have a REAL bilateral trade relationship with that origin.
//       * tradesUs  = False  -> destination "US" is HIDDEN (U.S. comprehensive
//         embargo: Cuba / Iran / North Korea / Syria per OFAC 2026).
//       * tradesCn  = True   -> "CN" always shown (China keeps no embargo).
//   - Destinations are exactly ["US", "CN"].

import data from '../data/origins.json';

export interface Origin {
  iso2: string;
  en: string;
  zh: string;
  tradesUs: boolean;
  tradesCn: boolean;
}
export const ORIGINS: Origin[] = (data as any).origins as Origin[];
export const DESTINATIONS: string[] = (data as any).destinations as string[]; // ["US","CN"]
export const US_EMBARGOED: string[] = (data as any).usEmbargoed as string[];

// Which destinations are selectable for a given origin — the linkage the user demanded.
// Per user 2026-09-04 iron rule: when origin === destination, hide it (domestic trade
// makes no sense for an import-duty calculator). Examples: origin=US -> only CN shown;
// origin=CN -> only US shown; CU/IR/KP/SY -> only CN (OFAC embargo hides US).
export function destOptionsFor(iso2: string): string[] {
  const o = ORIGINS.find((x) => x.iso2 === iso2);
  if (!o) return DESTINATIONS.slice();
  return DESTINATIONS.filter((d) => d !== iso2 && (d === 'US' ? o.tradesUs : d === 'CN' ? o.tradesCn : true));
}

// Localized origin name. Full 10-language coverage is a follow-up task; for now
// zh / zh-TW use the bundled Chinese name, everything else falls back to English
// (English names are themselves real, never invented).
export function originName(iso2: string, lang: string): string {
  const o = ORIGINS.find((x) => x.iso2 === iso2);
  if (!o) return iso2;
  if (lang === 'zh' || lang === 'zh-TW') return o.zh;
  return o.en;
}

export function originTradesUs(iso2: string): boolean {
  const o = ORIGINS.find((x) => x.iso2 === iso2);
  return o ? o.tradesUs : true;
}
export function originTradesCn(iso2: string): boolean {
  const o = ORIGINS.find((x) => x.iso2 === iso2);
  return o ? o.tradesCn : true;
}
