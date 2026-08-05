# Orbital — earth observation terminal

Earth at the centre of a deep starfield, with the Blender-built comms satellite in a
tilted orbit. Hover the globe for live coordinates; click the satellite to target a
place by name or by latitude/longitude.

## Run

```bash
# From the repository root:
cd orbital-website && npm install
cd ../apps/web && npm install && npm run build
cd ../../orbital-website && npm run serve
# http://localhost:8123/       globe-led SPARC dashboard
```

`npm run serve` starts the single combined SPARC server from `apps/web/serve.mjs`.
The globe is the only public page; selecting a target opens the analytical
dashboard as a panel over it. `/app/` is retained only as a redirect for old
bookmarks, while `/app/*` serves compiled panel assets. It must be served over
HTTP — the ES module import map won't resolve over `file://`.
Do not run `node server.mjs` for the full SPARC experience: that legacy
server does not include the compiled SPARC panel assets.

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
| `main.js` | scene, materials, orbit rig, interaction |
| `shaders.js` | GLSL chunks — the scattering integrator and the noise basis |
| `quality.js` | render tiers and device probing |
| `geo.js` | lat/lon maths and query parsing — pure, no DOM, unit tested |
| `places.js` | gazetteer, fuzzy search, reverse lookup |
| `server.mjs` | static file server |

## Quality tiers

Ultra is the default on anything with a real GPU: a 1536×768 displaced globe, a
32-step atmosphere, 8× MSAA and ~90k stars. Two cases step down — a software
rasteriser (SwiftShader/llvmpipe, which is also what the headless test runs on)
and mobile-class devices, which have to stay usable at 360 px.

`?quality=ultra|high|low` forces a tier in either direction if the probe reads a
machine wrong.

## Notes

- **The atmosphere is a real single-scattering integral**, not a rim gradient:
  Rayleigh + Mie + an ozone absorption layer, raymarched, with the planet
  occluding the sun march so the halo terminates instead of wrapping. The ozone
  term is what keeps the twilight wedge deep blue — without it the terminator
  goes muddy brown.
- **The same integrator runs over the ground** as aerial perspective. That shared
  path is the point: distant terrain loses contrast and gains blue exactly as
  hard as the limb glows, because both are the same air. Two separately tuned
  approximations always disagree somewhere on the limb.
- The atmosphere shell is stretched ~3.3× (a true 100 km is a hairline at these
  camera distances) and the scattering coefficients are divided by the same
  factor, so `beta * H` — the only thing the integral sees — stays physical.
  `BETA_R.b * H_RAY` is still 0.265, Earth's real vertical Rayleigh depth at
  440 nm. The halo gets thicker, not wrongly brighter.
- `SUN_INTENSITY` is tied to the surface term, not free. The surface is
  `albedo * 1.15 * cos(theta)`, i.e. `E/PI`, so the atmosphere is handed the same
  `E`. Change one without the other and the haze either vanishes or floods the
  disc.
- Terrain is **displaced in the vertex shader**, not just bump-shaded, so relief
  breaks the silhouette at the limb. The shading normal comes from central
  differences on the topography map, corrected for the equirectangular texel
  narrowing toward the poles.
- The ocean is GGX with a **roughness field**, not a wave normal map. Perturbing
  the normal per pixel puts crawling speckle on the water — neighbouring
  fragments flip in and out of a tight specular lobe with nothing to average
  them. Varying the lobe width instead is both alias-free and the more honest
  model, since roughness *is* the distribution of facets too small to resolve.
- Procedural surface and cloud detail fades in as the camera closes, standing in
  for basemap resolution that does not exist at 4K. Its top octave is kept
  several pixels wide at maximum zoom for the same aliasing reason.
- Bloom runs at a threshold of 1.20 in the linear HDR buffer. That is deliberately
  above 1.0: sunlit cloud tops sit right at white, and any lower blooms the whole
  daylit disc into haze instead of just the lights, limb and glint.
- Hover picking intersects the **ideal sphere**, not the globe mesh. At ultra the
  mesh is 2.4M triangles and three's raycast is a linear scan over every one of
  them, on a path that fires at input rate. The analytic solution is O(1) and
  reports the true surface rather than the nearest facet.
- The satellite is picked as a **screen-space disc** around its projected centre,
  sized from its own bounds so it tracks zoom. An exact mesh raycast missed
  constantly: the craft is a dish and two thin panels, almost all of that box is
  empty space between the struts, and the wings turn edge-on as they track the
  sun. The exact silhouette is not something the user can aim at; the position
  is. The pick is occlusion-tested against the globe, so it does not fire
  through the planet, and a click is ignored if the pointer travelled more than
  6 px since pointerdown, so orbit gestures ending near the craft do not open
  the console. Clicks re-pick at the event coordinates rather than reading the
  last frame's hover flag — touch never fires a hover, so the craft was
  previously not tappable at all on a phone.
- The satellite reproduces the Blender rig — the dish stays locked on nadir and the
  solar wings rotate on their spar to track the sun. One revolution takes ~101 s.
- The target designator is **corner brackets on a camera-facing quad held at a
  constant 54 px**, drawn procedurally so the arms stay one crisp antialiased
  width at any zoom. It reads as an instrument overlay rather than a decal, and
  it is equally legible whether the target faces you or sits on the limb.
  Underneath it are a thin ground ring — which *should* foreshorten, since that
  is how you read a patch of surface — and a dim mast carrying the HTML label
  clear of the brackets.
- That replaced a stack of additive pieces (halo disc, ring, expanding ping,
  glowing tip). Additively they summed past the 1.20 bloom threshold, so bloom
  turned the marker into a four-point starburst; and at a graze every flat piece
  foreshortens into the same spot, concentrating all of it into one sparkle. It
  read as a particle effect stuck on the planet. The designator is alpha-blended
  to stay under the threshold, and its only animation is a one-shot settle on
  acquisition — a loop with nothing to say keeps asking for attention.
- The designator draws with `depthTest: false` so terrain never clips it, which
  means the globe cannot hide it either; far-side culling is done on the CPU
  against the same facing test the label uses.
- The ground ring sits above `Q.displacement`, not on the ideal sphere — at the
  old 1.002 the displaced terrain cut it into a crescent.
- The beam is additive, a rim falloff over a base fill: rim alone draws the two
  silhouette walls and nothing between them, which looks like a wireframe cone
  rather than lit air. It stays exactly nadir on station — any slant you see is
  the projection of a 2,900 km vertical column viewed off-axis.
- Stars are three shells at different distances, mostly concentrated toward one
  great circle with a procedural Milky Way painted on the same plane. Orbiting
  parallaxes the shells against each other, which is what sells the depth.
- `prefers-reduced-motion` snaps targeting transitions instead of slewing, and
  freezes the grain — it is there to dither atmosphere banding, not to animate.

## On the Google Earth reference

The look is matched, not sourced. Google Earth's imagery is licensed and served
from their tile servers; this page has no runtime network call by design and has
to keep working offline, so pulling from `earth.google.com` is off the table on
both counts. What was actually taken from it is the *rendering*: photographic
basemap over displaced terrain, a physically integrated atmosphere, and aerial
perspective over distant ground. The imagery underneath is still the BlenderKit
4K set listed above.
