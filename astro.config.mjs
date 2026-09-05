import { defineConfig } from 'astro/config';

// 静态站：默认零 JS 产物，AI 爬虫可读全文。
// 计算器交互用少量 client script（Astro 自动打包），不影响 SEO/GEO。
export default defineConfig({
  site: 'https://tariff-stack.zmarkz123zxc.workers.dev',
  trailingSlash: 'ignore',
  // 压缩产物，便于 Cloudflare Worker 静态资源零服务器部署
  compressHTML: true,
});
