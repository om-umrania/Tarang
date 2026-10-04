// Fail the static website build before publishing an output without its entry pages.
import { readFileSync, statSync } from 'node:fs';
import { resolve, relative, isAbsolute, sep } from 'node:path';

function fail(message) {
  throw new Error(`Website routing check failed: ${message}`);
}
try {
  const root = process.cwd();
  const config = JSON.parse(readFileSync(resolve(root, 'vercel.json'), 'utf8'));
  if (config.outputDirectory !== 'docs') fail('outputDirectory must be docs; the repository root has no homepage.');
  const output = resolve(root, config.outputDirectory);
  function requireFile(name) {
    const file = resolve(output, name);
    const rel = relative(output, file);
    if (rel === '..' || rel.startsWith('..' + sep) || isAbsolute(rel)) fail(`Asset leaves the published directory: ${name}`);
    if (!statSync(file).isFile()) fail(`Missing published file: ${name}`);
    return readFileSync(file, 'utf8');
  }
  for (const page of ['index.html', 'dashboard.html']) {
    const html = requireFile(page);
    if (!/<title>Tarang/i.test(html)) fail(`${page} is not a Tarang entry page.`);
    for (const match of html.matchAll(/(?:src|href)=["']([^"']+)["']/g)) {
      const target = match[1];
      if (/^(?:[a-z][a-z\d+.-]*:|\/\/|#)/i.test(target)) continue;
      const path = decodeURIComponent(target.split(/[?#]/)[0]).replace(/^\//, '');
      if (!path || path === './') continue;
      requireFile(path);
    }
  }
  const dashboard = config.rewrites?.find(route => route.source === '/dashboard');
  if (dashboard?.destination !== '/dashboard.html') fail('/dashboard must resolve to the published dashboard.html.');
  const api = config.rewrites?.find(route => route.source === '/api/dashboard');
  if (api?.destination !== 'https://tarang-prototype.onrender.com/api/dashboard') fail('The dashboard API must route to the existing Render backend.');
  console.log('PASS: website homepage, dashboard, assets and API route are present in the published output.');
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
