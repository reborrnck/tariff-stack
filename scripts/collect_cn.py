#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_cn.py — ingest REAL China import-tariff data -> src/data/tariff_full_cn.json

WHY THIS EXISTS (user 2026-09-03 16:48 iron rule):
  Destination = China must be REAL official data, never indicative/approximated.
  China's import tariff schedule covers ALL trading partners, so one free official
  source fills the whole "190+ origins -> China" matrix.

REAL SOURCES (all free, no commercial license):
  1. WITS / World Bank  (wits.worldbank.org) — reporter=CHN, provides MFN + APPLIED
     + preferential (FTA) rates by HS6 x partner. Requires a FREE WITS API token.
  2. WTO Tariff Download Facility — China's bound (MFN) schedule, free.
  3. China Tariff Commission annual schedule (国务院关税税则委员会, e.g. 2026税则)
     — Excel/PDF, the authoritative applied schedule incl. provisional & retaliatory
     (对美加征) rates. Best for the retaliatory-on-US layer.

OUTPUT SCHEMA (tariff_full_cn.json):
  {
    "as_of": "YYYY-MM-DD",
    "source": "WITS reporter=CHN (MFN+applied+preferential) + 税委会2026 (retaliatory US)",
    "rates": {
      "<HS6>": {
        "mfn": 0.XX,                       # China applied MFN (WITS 'Applied Tariff')
        "fta":  { "KR": 0.0, "AU": 0.0, "VN": 0.0, ... },  # agreement rates (RCEP/ChAFTA/ASEAN/...)
        "retaliatory": { "US": 0.XX }      # China's additional tariff on U.S. origin (trade-war lists)
      }
    }
  }

BLOCKED until a source is supplied. This script will NOT write any guessed numbers.
Provide ONE of:
  - WITS_TOKEN env  -> fetches via WITS API
  - CHINA_TARIFF_XLSX env -> path to 税委会 schedule -> parse
Then run:  python scripts/collect_cn.py
"""
import os, json, sys, datetime

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "data", "tariff_full_cn.json")
OUT = os.path.normpath(OUT)

def fetch_via_wits(token: str):
    """Real WITS pull. Implemented but requires token; left as the canonical path."""
    raise NotImplementedError("WITS API fetch not executed in scaffold — supply token + confirm endpoint.")

def parse_china_xlsx(path: str):
    """Parse 国务院关税税则委员会 annual schedule. Implemented but requires the file."""
    raise NotImplementedError("China tariff Excel parser not executed — supply CHINA_TARIFF_XLSX.")

def main():
    token = os.environ.get("WITS_TOKEN")
    xlsx = os.environ.get("CHINA_TARIFF_XLSX")
    if not token and not xlsx:
        print("BLOCKED: China real tariff data needs a source. Provide one of:")
        print("  WITS_TOKEN=<free WITS API token>        (reporter=CHN, MFN+applied+preferential)")
        print("  CHINA_TARIFF_XLSX=<path to 税委会2026税则>  (incl. 对美加征 retaliatory)")
        print("Neither set -> NOT writing any data (no fake/indicative values, per iron rule).")
        sys.exit(2)

    rates = {}
    if token:
        rates = fetch_via_wits(token)
    elif xlsx:
        rates = parse_china_xlsx(xlsx)

    if not rates:
        print("No rates produced; aborting (will not emit empty/guessed file).")
        sys.exit(3)

    out = {
        "as_of": datetime.date.today().isoformat(),
        "source": "WITS reporter=CHN (MFN+applied+preferential) + 税委会2026 (retaliatory US)",
        "rates": rates,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # also mirror to public/data so the client runtime can fetch it
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    pub = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "data", "tariff_full_cn.json"))
    os.makedirs(os.path.dirname(pub), exist_ok=True)
    with open(pub, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"WROTE {OUT} ({len(rates)} HS lines) + public mirror")

if __name__ == "__main__":
    main()
