import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '..', '..');
const output = path.join(repo, 'vercel-output');

await fs.rm(output, { recursive: true, force: true });
await fs.mkdir(output, { recursive: true });

const copy = (source, target) => fs.cp(
  path.join(repo, source),
  path.join(output, target),
  { recursive: true, force: true },
);

// Preserve the combined local release shape: the Orbital globe at `/` and
// the Vite dashboard at `/app/`. Only runtime assets are copied; dependencies
// and raw processing data never enter the static output.
for (const file of [
  'index.html',
  'style.css',
  'main.js',
  'geo.js',
  'landmask.js',
  'places.js',
  'quality.js',
  'shaders.js',
]) {
  await copy(path.join('orbital-website', file), file);
}
await copy(path.join('orbital-website', 'assets'), 'assets');
await copy(path.join('orbital-website', 'node_modules', 'three'), path.join('node_modules', 'three'));
await copy(path.join('apps', 'web', 'dist'), 'app');

console.log(`Assembled Vercel static output at ${output}`);
