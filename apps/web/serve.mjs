/* The single SPARC server.
 *
 * One process, one port, everything: the built client, the bundled demo data,
 * the globe assets. There is no separate API process because there does not
 * need to be one — the demo transport resolves the immutable result packs
 * inside the bundle, which is also the offline path the release gate requires.
 * A second process would be a second thing to start, a second thing to fail
 * during a demo, and a second thing to explain.
 *
 * The optional FastAPI service still exists for contract work; run it
 * separately and set VITE_DATA_MODE=api at build time if you want the client
 * to talk to it. It is not part of this path.
 *
 *   node serve.mjs [port]
 */

import http from 'node:http';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '..', '..');

/* One public experience, two implementation roots.
 *
 *   /       the globe-led SPARC experience, served from orbital-website/.
 *   /app/*  compiled React panel assets loaded by the globe.
 *
 * The old standalone /app/ dashboard entry is intentionally redirected to /.
 * Keeping that URL as a second page made the product look like two different
 * sites. The panel still opens over the globe through window.SPARC. */
const APP_ROOT = path.join(HERE, 'dist');
const ORBIT_ROOT = path.join(REPO, 'orbital-website');
const PORT = Number(process.argv[2] ?? process.env.PORT ?? 8080);

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.glb': 'model/gltf-binary',
  '.woff2': 'font/woff2',
  '.map': 'application/json; charset=utf-8',
};

if (!fs.existsSync(APP_ROOT)) {
  console.error(`No build found at ${APP_ROOT}\nRun:  npm run build`);
  process.exit(1);
}

/* The globe imports three.js from its own node_modules through an import map,
   so that directory has to be reachable too. */
function resolveRequest(pathname) {
  if (pathname.startsWith('/app/')) {
    return { root: APP_ROOT, rel: pathname.slice(5).replace(/^[/\\]+/, ''), spa: false };
  }
  const rel = pathname === '/' ? 'index.html' : pathname.replace(/^[/\\]+/, '');
  return { root: ORBIT_ROOT, rel, spa: false };
}

http.createServer(async (req, res) => {
  let pathname;
  try {
    pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  } catch {
    res.writeHead(400, { 'Content-Type': 'text/plain' }).end('400 invalid request path');
    return;
  }
  if (pathname.includes('\0')) {
    res.writeHead(400, { 'Content-Type': 'text/plain' }).end('400 invalid request path');
    return;
  }

  // Keep old bookmarks working, but make the globe-led experience the only
  // public page. The URL fragment is never sent to the server, so a direct
  // /app/#/... bookmark safely lands on the globe and can target again there.
  if (pathname === '/app' || pathname === '/app/') {
    res.writeHead(302, {
      Location: '/',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
    }).end();
    return;
  }

  const { root, rel, spa } = resolveRequest(pathname);
  let file = path.resolve(root, rel);

  // Never serve outside the chosen root, whatever the caller encodes.
  if (file !== root && !file.startsWith(`${root}${path.sep}`)) {
    res.writeHead(403, { 'Content-Type': 'text/plain' }).end('403 forbidden');
    return;
  }

  let stat = await fsp.stat(file).catch(() => null);

  // Hash routes never reach the server, but a direct hit on an unknown path
  // under /app/ should still land on the client rather than a bare 404.
  if (!stat?.isFile()) {
    if (!spa) {
      res.writeHead(404, { 'Content-Type': 'text/plain' }).end('404 not found');
      return;
    }
    file = path.join(APP_ROOT, 'index.html');
    stat = await fsp.stat(file).catch(() => null);
    if (!stat?.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain' }).end('404 not found');
      return;
    }
  }

  const ext = path.extname(file).toLowerCase();
  const isHashed = /-[A-Za-z0-9_-]{8,}\./.test(path.basename(file));
  res.writeHead(200, {
    'Content-Type': TYPES[ext] ?? 'application/octet-stream',
    'Content-Length': stat.size,
    // Vite fingerprints asset filenames, so those are safe to cache hard;
    // index.html must not be, or a rebuild is invisible until a hard refresh.
    'Cache-Control': isHashed ? 'public, max-age=31536000, immutable' : 'no-cache',
    'X-Content-Type-Options': 'nosniff',
  });
  fs.createReadStream(file).pipe(res);
}).listen(PORT, () => {
  console.log(`SPARC  →  http://localhost:${PORT}/       (globe-led dashboard)`);
  console.log(`          /app/* serves panel assets only`);
  console.log('single public experience · globe, dashboard and demo data from one origin');
});
