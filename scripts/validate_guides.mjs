// Validate guide .astro frontmatter: JS parses, en/zh keys match, and every
// data-i18n key used in the HTML body exists in both en and zh dicts.
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import vm from 'node:vm';

const dir = 'D:/projects/tariff-platform/src/pages/guides';
const files = readdirSync(dir).filter((f) => f.endsWith('.astro'));
let failures = 0;

for (const f of files) {
  const src = readFileSync(join(dir, f), 'utf8');
  const m = src.split('---');
  if (m.length < 3) { console.log(`FAIL ${f}: no frontmatter`); failures++; continue; }
  let fm = m[1];
  // strip import + pageUpdated + const d = en; + export (getStaticPaths) lines
  fm = fm.split('\n').filter((l) => !/^\s*import /.test(l) && !/const pageUpdated/.test(l) && !/const d = en;/.test(l) && !/^\s*export\s/.test(l)).join('\n');
  let en, zh;
  try {
    // Mock Astro so paginated pages (const page = Astro.props.page) validate cleanly.
    const ctx = { Astro: { props: { page: { data: [], current: 1, last: 1, url: { prev: '', next: '' } } }, site: new URL('https://tariffstack.bbroot.com/'), url: new URL('https://tariffstack.bbroot.com/guides/') } };
    vm.createContext(ctx);
    vm.runInContext(fm + '\nthis.__en=en;this.__zh=zh;', ctx);
    en = ctx.__en; zh = ctx.__zh;
  } catch (e) {
    console.log(`FAIL ${f}: JS parse error -> ${e.message}`);
    failures++;
    continue;
  }
  if (!en || !zh) { console.log(`FAIL ${f}: missing en/zh`); failures++; continue; }
  const enKeys = Object.keys(en).sort().join(',');
  const zhKeys = Object.keys(zh).sort().join(',');
  if (enKeys !== zhKeys) {
    console.log(`FAIL ${f}: en/zh key mismatch`);
    failures++;
    continue;
  }
  // every data-i18n key in body must exist in dict
  const ignore = new Set(['g_read']); // literal string in index cards, not a dict key
  const used = [...src.matchAll(/data-i18n="([^"]+)"/g)].map((x) => x[1]);
  const missing = [...new Set(used)].filter((k) => !(k in en) && !ignore.has(k));
  if (missing.length) {
    console.log(`FAIL ${f}: missing dict keys -> ${missing.join(', ')}`);
    failures++;
    continue;
  }
  console.log(`OK   ${f}  (${Object.keys(en).length} keys, ${new Set(used).size} i18n used)`);
}
console.log(failures === 0 ? '\nALL GUIDES VALID' : `\n${failures} FAILURE(S)`);
process.exit(failures === 0 ? 0 : 1);
