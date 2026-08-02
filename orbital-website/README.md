# Orbital — earth observation terminal

Earth at the centre of a deep starfield, with the Blender-built comms satellite in a
tilted orbit. Hover the globe for live coordinates; click the satellite to target a
place by name or by latitude/longitude.

## Run

```bash
npm install       # once - pulls three.js
npm run serve     # http://localhost:8123/
```

It must be served over HTTP — the ES module import map won't resolve over `file://`.

## Test

```bash
npm test          # 319 assertions on coordinate maths + query parsing (node only)
npm run test:e2e  # 29 assertions driving a real headless browser over CDP
```

`test-e2e.mjs` needs the server running. It hovers the globe, hovers and clicks the
satellite, types a query, submits it, rejects a bad one, presses Escape and resizes
the viewport — then fails the run if the page logged any error.

## Deep links

| URL | Effect |
| --- | --- |
| `/` | free orbit |
| `/?target=Tokyo` | opens already locked on Tokyo |
| `/?lat=51.5&lon=-0.13` | same, by coordinate |
| `/?debug=1` | dumps live camera/satellite state into a `#debug` element |

## Controls

- **Drag** to orbit, **scroll** to zoom
- **Hover the globe** — live lat/lon readout follows the cursor, plus a surface reticle
  and the nearest known place
- **Click the satellite** — opens the targeting console
- **Escape** — closes the console, or releases the target and resumes free orbit

The console accepts `Tokyo`, `35.68, 139.69`, or `51°30'N 0°7'W`.

## Assets

Everything is local; there is no runtime network call and no geocoding service, so
the page works fully offline.

| File | Source |
| --- | --- |
| `assets/satellite.glb` | `build_satellite.py`, exported from Blender (147 KB) |
| `assets/earth_day/night/topo/ocean.jpg` | BlenderKit "Earth" by Matteo Pascale, 4096×2048 |
| `assets/earth_clouds.jpg` | same, 2048×1024 — soft enough that 4K only cost file size |
| `places.js` | 150-entry offline gazetteer |

Total payload 3.3 MB. Regenerate the textures with `../export_web_textures.py`, which
runs Blender headless against the cached asset — no GUI or MCP addon needed:

```bash
blender --background "%TEMP%/blenderkit_cache/804a6541-...-resolution_4K.blend" \
        --python ../export_web_textures.py
```

Earth textures are royalty-free per the BlenderKit listing. Check the licence before
shipping this publicly.

## Layout

| File | Role |
| --- | --- |
| `main.js` | scene, shaders, orbit rig, interaction |
| `geo.js` | lat/lon maths and query parsing — pure, no DOM, unit tested |
| `places.js` | gazetteer, fuzzy search, reverse lookup |
| `server.mjs` | static file server |

## Notes

- The Earth uses a custom shader: the normal is perturbed from the topography map so
  mountain ranges catch the light (land only — the ocean stays glassy); day and night
  blend across a soft terminator with warm scattering through it; city lights burn
  only where the sun is properly down and dim under cloud; the sun glint is tight,
  fresnel-weighted, masked to water and blocked by cloud; and cloud shadows are
  displaced away from the sun rather than straight down.
- The atmosphere is two fresnel lobes — a tight bright band at the limb over a faint
  outer haze — reddening toward the terminator where the light path is longest.
- Bloom runs at a threshold of 1.20 in the linear HDR buffer. That is deliberately
  above 1.0: sunlit cloud tops sit right at white, and any lower blooms the whole
  daylit disc into haze instead of just the lights, limb and glint.
- The satellite reproduces the Blender rig — the dish stays locked on nadir and the
  solar wings rotate on their spar to track the sun.
- Stars are three shells at different distances; orbiting the camera parallaxes them
  against each other, which is what sells the depth.
- `prefers-reduced-motion` snaps targeting transitions instead of slewing.
