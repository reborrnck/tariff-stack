// scripts/translate_desc.mjs
// ---------------------------------------------------------------------------
// Seed the HS-description translation table (public/data/desc_i18n.json) with
// FREE, no-key machine translation (MyMemory), so we own and can correct every
// string in-repo. This is the "full coverage" engine behind our hand-curated
// translations: high-frequency phrases are hand-written in desc_i18n.json; this
// script fills the long tail incrementally and idempotently.
//
// Design notes:
//  - Keyed by the NORMALIZED English source (normDescKey): strip trailing ":"
//    and parenthetical heading codes ("Of cotton (369)" -> "Of cotton"), because
//    at runtime descTrans() looks up exactly these normalized segment strings.
//  - Languages are filled in PRIORITY order (zh, zh-TW first — our main audience)
//    until the daily character budget is exhausted, so coverage grows where it
//    matters most first.
//  - Idempotent: skips keys/langs already present; safe to run every day.
//  - Budgeted under MyMemory's ~50k char/day anonymous limit (use MYMEMORY_EMAIL
//    to raise it). Set DESC_CHAR_BUDGET to throttle per run.
//  - Respects 429 / network errors with retries + backoff; never throws fatally.
// ---------------------------------------------------------------------------
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SRC_FULL = path.join(ROOT, 'src/data/tariff_full.json');
const OUT = path.join(ROOT, 'public/data/desc_i18n.json');

const LANGS = ['zh', 'zh-TW', 'ja', 'ko', 'es', 'fr', 'pt', 'de', 'it'];
const PAIR = {
  zh: 'en|zh', 'zh-TW': 'en|zh-TW', ja: 'en|ja', ko: 'en|ko',
  es: 'en|es', fr: 'en|fr', pt: 'en|pt', de: 'en|de', it: 'en|it',
};
const EMAIL = process.env.MYMEMORY_EMAIL || 'TariffStack@outlook.com';
const DAILY_CHAR_BUDGET = Number(process.env.DESC_CHAR_BUDGET || 45000);
const CONCURRENCY = Number(process.env.DESC_CONCURRENCY || 4);

function normKey(s) {
  return (s || '').trim().replace(/:\s*$/, '').replace(/\s*\(\d+\)\s*$/, '').trim();
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

function collectSources() {
  const j = JSON.parse(fs.readFileSync(SRC_FULL, 'utf8'));
  const freq = new Map();
  for (const k in j) {
    const d = (j[k].desc || '').replace(/:\s*$/, '').trim();
    if (!d) continue;
    const key = normKey(d);
    freq.set(key, (freq.get(key) || 0) + 1);
  }
  return freq; // Map<key, count>
}

async function translate(text, pair) {
  const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${pair}&de=${encodeURIComponent(EMAIL)}`;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const r = await fetch(url);
      if (r.status === 429) { await sleep(2500); continue; }
      if (!r.ok) return null;
      const j = await r.json();
      const t = j && j.responseData && j.responseData.translatedText;
      if (!t) return null;
      if (/MYMEMORY WARNING/i.test(t)) return null;
      const out = t.trim();
      if (!out || out.toLowerCase() === text.toLowerCase()) return null; // untranslated echo
      return out;
    } catch (e) {
      await sleep(1200);
    }
  }
  return null;
}

async function main() {
  const freq = collectSources();
  let table = {};
  if (fs.existsSync(OUT)) {
    try { table = JSON.parse(fs.readFileSync(OUT, 'utf8')); } catch (e) { table = {}; }
  }

  // Build a worklist of {key, missing[]} for keys missing one or more priority langs.
  const work = [];
  for (const [key, count] of freq) {
    const e = table[key] || {};
    const missing = LANGS.filter(l => !e[l]);
    if (missing.length) work.push({ key, missing, count });
  }
  // Sort by browse frequency DESC so the daily budget covers the most-seen
  // descriptions first (fastest visible coverage growth), then by fewest-missing.
  work.sort((a, b) => (b.count - a.count) || (a.missing.length - b.missing.length));

  console.log(`[translate_desc] unique sources=${freq.size}, already in table=${Object.keys(table).length}, need work=${work.length}`);

  let budget = DAILY_CHAR_BUDGET;
  let doneKeys = 0, doneTrans = 0, skipped = 0;

  // Process with bounded concurrency, stopping when budget is exhausted.
  let idx = 0;
  async function worker() {
    while (idx < work.length) {
      const job = work[idx++];
      const entry = table[job.key] || (table[job.key] = {});
      for (const lang of job.missing) {
        if (budget <= 0) { skipped++; continue; }
        const cost = job.key.length;
        if (cost > budget) { skipped++; continue; }
        const tr = await translate(job.key, PAIR[lang]);
        if (tr) {
          entry[lang] = tr;
          budget -= cost;
          doneTrans++;
        } else {
          skipped++;
        }
        await sleep(120); // gentle pacing to avoid 429
      }
      // Count fully-covered keys
      if (LANGS.every(l => entry[l])) doneKeys++;
    }
  }

  const workers = [];
  for (let i = 0; i < Math.min(CONCURRENCY, work.length || 1); i++) workers.push(worker());
  await Promise.all(workers);

  fs.writeFileSync(OUT, JSON.stringify(table, null, 2) + '\n', 'utf8');
  const fullyCovered = Object.values(table).filter(e => LANGS.every(l => e[l])).length;
  console.log(`[translate_desc] done: translations=${doneTrans}, fullyCoveredKeys=${fullyCovered}/${freq.size}, budgetLeft=${budget}, skippedNoBudget=${skipped}`);
}

main().catch(e => { console.error('[translate_desc] fatal:', e); process.exit(1); });
