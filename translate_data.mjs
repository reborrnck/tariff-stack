// translate_data.mjs — bake HTS description translations into tariff_full.json
//
// Your audience is in China, so client-side Google/DeepL calls are blocked by the GFW.
// The robust fix is to translate ONCE at build time and ship the text statically.
// Each record gains:  desc_i18n: { zh, ja, es, de }
// renderMatches() then prefers desc_i18n over the English source (see bestDesc()).
//
// Providers (China-accessible first):
//   Baidu (recommended, free tier):  TRANSLATOR=baidu BAIU_APP_ID=xxx BAIU_APP_KEY=yyy node translate_data.mjs
//   DeepL (non-China fallback):       TRANSLATOR=deepl DEEPL_KEY=xxx node translate_data.mjs
//
// A per-string cache (.trash/desc_i18n_cache.json) means re-runs only translate what's missing.
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { createHash } from 'node:crypto';

const __dir = dirname(fileURLToPath(import.meta.url));
const DATA = join(__dir, 'public', 'data', 'tariff_full.json');
const CACHE_DIR = join(__dir, '.trash');
const CACHE = join(CACHE_DIR, 'desc_i18n_cache.json');

const provider = process.env.TRANSLATOR || 'baidu';
// [ourLang, providerTargetLang]
const TARGETS = [['zh', 'zh'], ['ja', 'ja'], ['es', 'es'], ['de', 'de']];
const PROVIDER_TO = {
  baidu: { zh: 'zh', ja: 'jp', es: 'spa', de: 'de' }, // Baidu uses jp/spa
  deepl: { zh: 'ZH', ja: 'JA', es: 'ES', de: 'DE' },
};

function load() { return JSON.parse(readFileSync(DATA, 'utf8')); }
function save(obj) { writeFileSync(DATA, JSON.stringify(obj)); }
function loadCache() { return existsSync(CACHE) ? JSON.parse(readFileSync(CACHE, 'utf8')) : {}; }
function saveCache(c) { if (!existsSync(CACHE_DIR)) mkdirSync(CACHE_DIR, { recursive: true }); writeFileSync(CACHE, JSON.stringify(c)); }

async function baidu(q, to) {
  const appid = process.env.BAIU_APP_ID, key = process.env.BAIU_APP_KEY;
  if (!appid || !key) throw new Error('set BAIU_APP_ID and BAIU_APP_KEY');
  const salt = String(Math.random()).slice(2, 12);
  const sign = createHash('md5').update(appid + q + salt + key).digest('hex');
  const url = `https://fanyi-api.baidu.com/api/trans/vip/translate?q=${encodeURIComponent(q)}&from=en&to=${to}&appid=${appid}&salt=${salt}&sign=${sign}`;
  const r = await fetch(url); const j = await r.json();
  if (j.error_code) throw new Error(`Baidu ${j.error_code} ${j.error_msg}`);
  return j.trans_result[0].dst;
}
async function deepl(q, to) {
  const key = process.env.DEEPL_KEY; if (!key) throw new Error('set DEEPL_KEY');
  const r = await fetch('https://api-free.deepl.com/v2/translate', {
    method: 'POST',
    headers: { 'Authorization': `DeepL-Auth-Key ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: [q], target_lang: to }),
  });
  const j = await r.json(); if (j.message) throw new Error(`DeepL ${j.message}`);
  return j.translations[0].text;
}
async function translateOne(q, lang) {
  const to = PROVIDER_TO[provider][lang];
  return provider === 'baidu' ? baidu(q, to) : deepl(q, to);
}

(async () => {
  if (!existsSync(DATA)) { console.error('no', DATA); process.exit(1); }
  const data = load();
  const cache = loadCache();
  const keys = Object.keys(data);
  let done = 0;
  for (const hts of keys) {
    const rec = data[hts]; const desc = rec.desc; if (!desc) { done++; continue; }
    if (rec.desc_i18n && Object.keys(rec.desc_i18n).length === 4) { done++; continue; }
    const out = {};
    for (const [lang] of TARGETS) {
      const ck = `${hts}|${lang}`;
      if (cache[ck]) { out[lang] = cache[ck]; continue; }
      try {
        out[lang] = await translateOne(desc, lang);
        cache[ck] = out[lang];
      } catch (e) {
        console.error('FAIL', hts, lang, e.message);
        out[lang] = desc; // fallback to English, keep going
      }
      await new Promise(r => setTimeout(r, 60)); // be friendly to rate limits
    }
    rec.desc_i18n = out;
    done++;
    if (done % 200 === 0) { save(data); saveCache(cache); console.log('progress', done, '/', keys.length); }
  }
  save(data); saveCache(cache);
  console.log('DONE', done, 'records translated ->', DATA);
})();
