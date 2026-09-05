// Generate public/sitemap.xml from the real route table.
// Covers: static routes, every guide detail page, and paginated /guides/N pages.
// Run automatically before `astro build` (see package.json "build" script),
// so the sitemap never goes stale when guides or page size change.
import { readdirSync, writeFileSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

// Resolve repo root from this script's location (portable: works in CI too).
const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const cfg = readFileSync(join(ROOT, 'astro.config.mjs'), 'utf8');
const SITE = (cfg.match(/site:\s*['"]([^'"]+)['"]/)?.[1] || 'https://tariffstack.bbroot.com').replace(/\/$/, '');
const PAGE_SIZE = 8;

const guidesDir = join(ROOT, 'src/pages/guides');
const guideSlugs = readdirSync(guidesDir)
  .filter((f) => f.endsWith('.astro'))
  .filter((f) => !/^index\.astro$/.test(f) && !/^\[\.+\w+\]\.astro$/.test(f))
  .map((f) => f.replace(/\.astro$/, ''))
  .sort();

const staticRoutes = ['/', '/about', '/privacy', '/terms', '/guides'];
const totalPages = Math.max(1, Math.ceil(guideSlugs.length / PAGE_SIZE));
const paginated = [];
for (let p = 2; p <= totalPages; p++) paginated.push(`/guides/${p}`);

const all = [...staticRoutes, ...guideSlugs.map((s) => `/guides/${s}`), ...paginated];

const urlOf = (p) => SITE + (p === '/' ? '/' : p + '/');
const today = new Date().toISOString().slice(0, 10);

const priorityOf = (p) => {
  if (p === '/') return '1.0';
  if (p === '/guides' || p.startsWith('/guides/')) return '0.8';
  return '0.7';
};
const freqOf = (p) => (p.startsWith('/guides/') && p !== '/guides' ? 'monthly' : 'weekly');

const xml =
`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.s3.org/1999/ns/sitemap">
${all.map((p) => `  <url>
    <loc>${urlOf(p)}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${freqOf(p)}</changefreq>
    <priority>${priorityOf(p)}</priority>
  </url>`).join('\n')}
</urlset>
`;

// Local-dev fallback: sandboxed shells can't overwrite D:\public\sitemap.xml (file watcher),
// so write to a temp path; WorkBuddy Write tool copies the result to the real location.
const outPath = process.env.TS_SITEMAP_OUT || join(ROOT, 'public/sitemap.xml');
writeFileSync(outPath, xml);
console.log(`sitemap.xml written: ${all.length} urls (${guideSlugs.length} guides, ${totalPages} guide pages)`);
