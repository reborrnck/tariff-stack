// TariffStack /api/calc — programmatic tariff calculation endpoint.
// Served as a Cloudflare Worker alongside the static site (wrangler.toml `main`).
// The large rate tables are fetched from static assets at request time (kept out
// of the worker bundle); the small config JSONs are imported directly.

import { computeStack } from '../src/lib/calc.ts';
import sample from '../src/data/tariff_sample.json';
import overlay from '../src/data/policy_overlay.json';

interface AssetsEnv {
  ASSETS: { fetch: (req: Request | string) => Promise<Response> };
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET, POST, OPTIONS',
      'cache-control': 'public, max-age=300',
    },
  });
}

export default {
  async fetch(req: Request, env: AssetsEnv): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === '/api/calc') {
      if (req.method === 'OPTIONS') {
        return new Response(null, {
          status: 204,
          headers: {
            'access-control-allow-origin': '*',
            'access-control-allow-methods': 'GET, POST, OPTIONS',
            'access-control-allow-headers': 'content-type',
          },
        });
      }
      if (req.method !== 'GET' && req.method !== 'POST') {
        return json({ error: 'Method not allowed. Use GET or POST.' }, 405);
      }

      let params: Record<string, string> = {};
      try {
        if (req.method === 'POST') {
          const ct = req.headers.get('content-type') || '';
          if (ct.includes('application/json')) params = (await req.json()) as Record<string, string>;
          else {
            const fd = await req.formData();
            fd.forEach((v, k) => { params[k] = String(v); });
          }
        } else {
          url.searchParams.forEach((v, k) => { params[k] = v; });
        }
      } catch { params = {}; }

      const dest = String(params.dest || 'US').toUpperCase();
      const hts = String(params.hts || '').trim();
      const origin = String(params.origin || 'CN').toUpperCase();
      const goods = parseFloat(params.goods as string);
      const goodsVal = isFinite(goods) ? goods : 1000;

      if (!hts) return json({ error: 'Missing required parameter: hts' }, 400);

      const [fullRes, cnRes] = await Promise.all([
        env.ASSETS.fetch(new Request(new URL('/data/tariff_full.json', url))),
        env.ASSETS.fetch(new Request(new URL('/data/tariff_full_cn.json', url))),
      ]);
      let FULL: any = null, cnFull: any = null;
      try { FULL = await fullRes.json(); } catch {}
      try { cnFull = await cnRes.json(); } catch {}
      const cnRates = cnFull && cnFull.by_hs8 ? cnFull.by_hs8 : cnFull;
      const fixed = (sample as any).fixed;
      const rates = FULL || (sample as any).rates;

      let res: any = null;
      if (dest === 'CN') res = computeStack(dest, hts, origin, goodsVal, rates, fixed, overlay as any, cnRates);
      else res = rates && rates[hts] ? computeStack(dest, hts, origin, goodsVal, rates, fixed, overlay as any) : null;

      if (!res) {
        return json({
          error: 'HTS not found for destination',
          hts, dest,
          suggestion: 'U.S. needs a 10-digit HTS; China needs an 8-digit HS. Verify the code.',
        }, 404);
      }

      return json({
        meta: {
          tool: 'TariffStack',
          destination: dest,
          data_as_of: (overlay as any).as_of,
          data_last_checked: (overlay as any).last_checked,
          generated_at: new Date().toISOString(),
        },
        result: res,
      });
    }

    // everything else -> serve the static site
    return env.ASSETS.fetch(req);
  },
};
