/* SPARC dashboard end-to-end checks.
 *
 * Drives the P0 analytical journey, the contract failure states, and the
 * responsive/accessibility gates from docs/project-status.md over the Chrome
 * DevTools Protocol. Screenshots each step. Any console error fails the run.
 *
 *   Prerequisites:  cd apps/web && npm run dev      (serves http://localhost:5173)
 *                   uvicorn apps.api.app.main:app --port 8000   (for the API steps)
 *
 *   Usage:  node tests/frontend/dashboard-e2e.mjs [baseUrl]
 *
 * The API steps exercise the *unreachable* path deliberately by blocking
 * /api/v1/* at the network layer — that is the offline recovery the demo
 * rehearsal depends on, so it is tested rather than assumed. */

import { spawn } from 'node:child_process';
import { existsSync, writeFileSync, mkdirSync } from 'node:fs';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const args = process.argv.slice(2);
const suppliedUrl = args.find((arg) => /^https?:\/\//.test(arg));
/* A handoff URL includes a hash route.  The test later constructs its own
 * dashboard deep links, so using the entire supplied URL as BASE would append
 * a second hash and create an invalid route such as
 * #/locate?...#/dashboard/vegetation.  Retain it for a dedicated handoff
 * check, but use the hash-free document URL for the rest of the suite. */
const HANDOFF_URL = suppliedUrl && new URL(suppliedUrl).hash ? suppliedUrl : null;
const BASE = (() => {
  if (!suppliedUrl) return 'http://localhost:5173/';
  const url = new URL(suppliedUrl);
  url.hash = '';
  url.search = '';
  return url.href;
})();
const API_MODE = args.includes('--api');
const OUT = process.env.SPARC_E2E_SHOTS ?? path.join(tmpdir(), 'sparc-dashboard-shots');
const PORT = 9510;
mkdirSync(OUT, { recursive: true });
console.log(`base: ${BASE}\nshots: ${OUT}`);

const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find(existsSync);
if (!CHROME) { console.error('no chrome'); process.exit(2); }

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const profile = await mkdtemp(path.join(tmpdir(), 'sparc-dash-'));
const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu',
  '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--disable-background-networking', '--no-first-run',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--window-size=1280,900', 'about:blank',
], { stdio: 'ignore' });

let ws, msgId = 0;
const pending = new Map();
const errors = [];
let pass = 0, fail = 0;
const ok = (name, cond, extra = '') => {
  if (cond) { pass++; console.log(`  ok    ${name}`); }
  else { fail++; console.log(`  FAIL  ${name} ${extra}`); }
};

function send(method, params = {}) {
  const id = ++msgId;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((res, rej) => {
    pending.set(id, { res, rej });
    setTimeout(() => { if (pending.delete(id)) rej(new Error(`${method} timeout`)); }, 60000);
  });
}
async function evaluate(expression) {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || 'threw');
  return r.result.value;
}
async function shot(name) {
  const r = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(path.join(OUT, `${name}.png`), Buffer.from(r.data, 'base64'));
  console.log(`    -> ${name}.png`);
}
const text = () => evaluate('document.body.innerText');
async function waitFor(label, expr, timeout = 20000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    if (await evaluate(expr)) return true;
    await sleep(200);
  }
  throw new Error(`timed out waiting for ${label}`);
}
const step = (s) => console.log(`\n${s}`);

try {
  let wsUrl;
  for (let i = 0; i < 60 && !wsUrl; i++) {
    try {
      const list = await fetch(`http://127.0.0.1:${PORT}/json/list`).then((r) => r.json());
      wsUrl = list.find((t) => t.type === 'page')?.webSocketDebuggerUrl;
    } catch { /* waiting */ }
    if (!wsUrl) await sleep(400);
  }
  if (!wsUrl) throw new Error('Chrome remote-debugging endpoint did not become ready');
  ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id);
      pending.delete(m.id);
      m.error ? rej(new Error(m.error.message)) : res(m.result);
    } else if (m.method === 'Runtime.exceptionThrown') {
      errors.push(m.params.exceptionDetails.exception?.description || 'exception');
    } else if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') {
      errors.push(m.params.entry.text);
    }
  };
  await send('Runtime.enable'); await send('Log.enable'); await send('Page.enable'); await send('Network.enable');

  if (HANDOFF_URL) {
    step('0. open the supplied Orbit handoff link');
    await send('Page.navigate', { url: HANDOFF_URL });
    await waitFor('handoff document', 'document.body.innerText.includes("Where do you want to look?") || document.body.innerText.includes("Which two periods should we compare?") || document.querySelectorAll(".card").length >= 3');
    // The location console renders before its coordinate-resolution effect has
    // finished. Wait for the resulting stage/message before asserting; otherwise
    // this check races a valid handoff and reports a false failure.
    await waitFor('handoff resolution', 'document.body.innerText.includes("Which two periods should we compare?") || document.body.innerText.includes("No packaged result covers") || document.body.innerText.includes("Synthetic demo data")');
    const handoffText = await text();
    ok('handoff route is handled by the dashboard, not the static server', !handoffText.includes('404 app/'));
    ok('handoff coordinates are either resolved or declined honestly',
      handoffText.includes('Which two periods should we compare?')
        || handoffText.includes('No packaged result covers')
        || handoffText.includes('Synthetic demo data'));
  }

  step('1. choose the bundled fixture and frozen period');
  await send('Page.navigate', { url: BASE });
  await waitFor('location console', 'document.body.innerText.includes("Where do you want to look?")');
  ok('location step is meaningful without WebGL', (await evaluate('document.body.innerText.trim().length')) > 0);
  ok('location step has no required canvas', (await evaluate('document.querySelectorAll("canvas").length')) === 0);
  ok('Nagpur fixture is selectable without the globe',
    await evaluate(`[...document.querySelectorAll('.citycard')].some(b => b.textContent.includes('Nagpur'))`));
  ok('Nagpur fixture is visibly synthetic',
    await evaluate(`[...document.querySelectorAll('.citycard')].find(b => b.textContent.includes('Nagpur'))?.textContent.includes('mock fixture')`));
  ok('Nagpur fixture is not mislabelled as real data',
    await evaluate(`![...document.querySelectorAll('.citycard')].find(b => b.textContent.includes('Nagpur'))?.textContent.toLowerCase().includes('real pack')`));
  await evaluate(`[...document.querySelectorAll('.citycard')].find(b => b.textContent.includes('Nagpur')).click()`);
  await waitFor('period console or single-period summary', 'document.body.innerText.includes("Which two periods should we compare?") || document.querySelectorAll(".card").length >= 3');
  if (await evaluate('document.querySelector(".period-card") !== null')) {
    await evaluate('document.querySelector(".period-card").click()');
  }
  await waitFor('summary', 'document.querySelectorAll(".card").length >= 3');
  const t1 = await text();
  ok('three indicator cards render', (await evaluate('document.querySelectorAll(".card").length')) === 3);
  ok('synthetic-data badge is visible', t1.includes('Synthetic demo data'));
  ok('transport is named', t1.includes(API_MODE ? 'Local API (mock fixtures)' : 'Offline demo pack'));
  ok('boundary disclaimer present', t1.includes('not an authoritative legal or cadastral boundary'));
  // plan.md requires the geoBoundaries ODbL provenance, attribution and
  // share-alike obligations to be preserved wherever the geometry travels.
  ok('boundary licence named on the summary', t1.includes('Open Data Commons Open Database License 1.0'));
  ok('share-alike stated on the summary', t1.includes('share-alike'));
  ok('pinned release id shown', t1.includes('IND-ADM2-76128533'));
  ok('proxy (non-SDG) disclaimer present', t1.includes('not official UN SDG indicators'));
  ok('no 3D canvas on the analytical route', (await evaluate('document.querySelectorAll("canvas").length')) === 0);
  ok('SDG targets are named on the cards', t1.includes('SDG 6.6') && t1.includes('SDG 15.1') && t1.includes('SDG 11.3'));
  ok('SDG scope is qualified', t1.includes('does not produce official SDG indicator values'));
  ok('district-only scope stated', t1.includes('No subdistrict boundary has passed its approval gate'));
  await shot('1-summary');

  step('2. open an indicator detail');
  await evaluate(`[...document.querySelectorAll('.btn--card')][0].click()`);
  await waitFor('detail', 'location.hash.startsWith("#/dashboard/")');
  await waitFor('quality panel', 'document.body.innerText.includes("Quality evidence")');
  const t2 = await text();
  ok('route is shareable', (await evaluate('location.hash')) === '#/dashboard/surface-water');
  ok('interpretation shown', t2.includes('What this shows'));
  ok('caveats shown', t2.includes('What it does not show'));
  ok('quality evidence shown', t2.includes('Common-valid coverage'));
  ok('threshold sensitivity shown', t2.includes('Threshold sensitivity'));
  ok('no-independent-validation warning', t2.includes('No independent validation'));
  ok('provenance shown', t2.includes('Provenance') && t2.includes('Parameters hash'));
  ok('layer bounds + attribution shown', t2.includes('West') && t2.includes('Attribution'));
  ok('SDG target + what it is not', t2.includes('SDG relevance') && t2.includes('Is not:'));
  ok('boundary licence panel present', t2.includes('Boundary source and licence'));
  ok('geoBoundaries attribution reproduced', t2.includes('Contains modified geoBoundaries data'));
  ok('ODbL share-alike obligation explained', t2.includes('derived database must be offered'));
  ok('not represented as CC-BY-only',
    t2.includes('CC BY 4.0') && t2.includes('SPARC follows the source-specific ODbL record'));
  ok('no Survey of India geometry claimed', t2.includes('No Survey of India ABDB geometry'));
  await shot('2-detail');

  step('3. reload the deep link (route survives refresh)');
  await send('Page.navigate', { url: `${BASE}#/dashboard/vegetation` });
  await waitFor('vegetation detail', 'document.body.innerText.includes("Vegetation")');
  ok('deep link restores the detail view', (await evaluate('location.hash')) === '#/dashboard/vegetation');
  await shot('3-deeplink');

  if (API_MODE) {
  step('4. API unreachable -> bundled-demo recovery');
  await send('Network.setBlockedURLs', { urls: ['*/api/v1/*'] });
  await send('Page.navigate', { url: `${BASE}#/dashboard` });
  await waitFor('error state', 'document.body.innerText.includes("did not respond")', 25000);
  const t4 = await text();
  ok('API-down state explains the failure', t4.includes('The API did not respond'));
  ok('offers the offline recovery', t4.includes('Switch to offline demo pack'));
  ok('recovery action is a real button',
    (await evaluate(`[...document.querySelectorAll('button')].some(b => b.textContent.includes('Switch to offline demo pack'))`)));
  await shot('4-api-down');

  step('5. recovery actually recovers');
  await evaluate(`[...document.querySelectorAll('button')].find(b => b.textContent.includes('Switch to offline demo pack')).click()`);
  await waitFor('recovered', 'document.querySelectorAll(".card").length >= 3');
  ok('offline pack restores the journey with the API still blocked', true);
  await shot('5-recovered');
  await send('Network.setBlockedURLs', { urls: [] });
  }

  step('6. 360 px viewport');
  await send('Emulation.setDeviceMetricsOverride', { width: 360, height: 780, deviceScaleFactor: 2, mobile: true });
  await sleep(900);
  const overflow = await evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth');
  ok('no horizontal overflow at 360 px', overflow <= 1, `overflow=${overflow}px`);
  await shot('6-360px');

  step('7. 200% zoom');
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await evaluate(`document.documentElement.style.fontSize = '200%'`);
  await sleep(700);
  const zoomOverflow = await evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth');
  ok('no horizontal overflow at 200% text zoom', zoomOverflow <= 1, `overflow=${zoomOverflow}px`);
  await shot('7-zoom200');
  await evaluate(`document.documentElement.style.fontSize = ''`);

  step('8. keyboard journey');
  const kb = await evaluate(`(() => {
    const sel = 'a[href], button:not([disabled]), select, input:not([disabled]), summary, [tabindex]:not([tabindex="-1"])';
    const items = [...document.querySelectorAll(sel)].filter(el => el.offsetParent !== null || el.classList.contains('skip'));
    return { count: items.length, first: items[0]?.textContent?.trim().slice(0, 40) };
  })()`);
  ok('skip link is the first focusable element', kb.first?.includes('Skip to results'), JSON.stringify(kb));
  // Skip link, two header actions and three indicator buttons are the minimum
  // controls on the dashboard. The location form is exercised above.
  ok('every dashboard control is reachable', kb.count >= 6, `focusable=${kb.count}`);
  const labelled = await evaluate(`(() => {
    const bad = [...document.querySelectorAll('select, input')].filter(el => {
      const id = el.id;
      return !id || !document.querySelector('label[for="' + id + '"]');
    });
    return bad.length;
  })()`);
  ok('every form control has a label', labelled === 0, `unlabelled=${labelled}`);

  step('9. non-colour status encoding');
  const pills = await evaluate(`[...document.querySelectorAll('.pill')].map(p => p.textContent.trim())`);
  ok('status/quality carry text, not just colour',
    pills.length > 0 && pills.every(p => /[A-Za-z]/.test(p)), JSON.stringify(pills.slice(0, 4)));
} catch (e) {
  fail++;
  console.log(`\nFATAL ${e.message}`);
} finally {
  try { ws?.close(); } catch {}
  chrome.kill();
}

if (errors.length) {
  fail += errors.length;
  console.log('\npage errors:');
  [...new Set(errors)].forEach((e) => console.log('  ' + String(e).slice(0, 400)));
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
