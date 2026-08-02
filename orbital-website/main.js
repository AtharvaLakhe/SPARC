/* ── Orbital ─────────────────────────────────────────────────────────────
   Earth at centre of a deep starfield, with the Blender-built comms satellite
   in a tilted orbit. Hover the globe for live coordinates; click the satellite
   to target a place by name or lat/lon.
   ──────────────────────────────────────────────────────────────────────── */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { PLACES, findPlaces, nearestPlace } from './places.js';
import { latLonToVec3 as latLonXYZ, vec3ToLatLon, parseQuery, fmtLat, fmtLon } from './geo.js';

const EARTH_R = 1;
const CLOUD_R = EARTH_R * 1.006;
const ATMO_R = EARTH_R * 1.055;
const ORBIT_R = EARTH_R * 1.46;
const ORBIT_TILT = THREE.MathUtils.degToRad(28);
const AXIAL_TILT = THREE.MathUtils.degToRad(23.4);
const SAT_SPAN = 0.26;            // largest dimension, same ratio as the blender scene
const SPIN = 0.0135;              // earth radians/second
// angled toward the default camera so the opening view lands on the day side,
// with the terminator sweeping across the left limb
const SUN_DIR = new THREE.Vector3(-0.52, 0.26, 0.81).normalize();

const $ = (id) => document.getElementById(id);
const DEBUG = new URLSearchParams(location.search).has('debug');

// Readers who ask for reduced motion get the target snapped into place instead of
// a long slew. (It also makes the headless smoke test converge in a few frames.)
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const SLEW_DUR = REDUCED ? 0.12 : 2.2;
const CAM_DUR = REDUCED ? 0.12 : 2.0;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

/* ── renderer / scene ───────────────────────────────────────────────────── */
const canvas = $('stage');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.01, 5000);
camera.position.set(0, 0.62, 3.05);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.055;
controls.rotateSpeed = 0.42;
controls.zoomSpeed = 0.7;
controls.enablePan = false;
controls.minDistance = 1.35;
controls.maxDistance = 9;

scene.add(new THREE.AmbientLight(0x16202e, 1.0));

const sunLight = new THREE.DirectionalLight(0xfff4e6, 3.2);
sunLight.position.copy(SUN_DIR).multiplyScalar(60);
scene.add(sunLight);

/* Post: a high-threshold bloom so only genuinely bright things glow - city lights,
   the limb arc, the sun glint - rather than hazing the whole daylit disc.
   Rendering through a composer also means the passes work in linear space and
   OutputPass does tone mapping once, at the end. */
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloomPass = new UnrealBloomPass(
  new THREE.Vector2(innerWidth, innerHeight),
  0.55,   // strength
  0.40,   // radius
  // Threshold is luminance in the linear HDR buffer, so it is meaningful above 1.
  // Sunlit cloud tops sit right at ~1.0; anything lower blooms the entire daylit
  // disc into a white haze. This keeps it to city lights, the limb and the glint.
  1.20,
);
composer.addPass(bloomPass);
composer.addPass(new OutputPass());

/* ── loading ────────────────────────────────────────────────────────────── */
const manager = new THREE.LoadingManager();
const bar = document.querySelector('.loader-bar i');
manager.onProgress = (_u, loaded, total) => { bar.style.width = `${(loaded / total) * 92}%`; };
manager.onLoad = () => {
  bar.style.width = '100%';
  setTimeout(() => {
    $('loader').classList.add('done');
    document.body.classList.add('ready');
    setTimeout(() => $('loader').remove(), 800);
  }, 220);
};
manager.onError = (url) => console.error('[orbital] failed to load', url);

const texLoader = new THREE.TextureLoader(manager);
const MAX_ANISO = renderer.capabilities.getMaxAnisotropy();
const tex = (file) => {
  const t = texLoader.load(`assets/${file}`);
  t.colorSpace = THREE.NoColorSpace;   // shaders below decode explicitly
  t.anisotropy = MAX_ANISO;            // the limb is all grazing angles
  t.wrapS = THREE.RepeatWrapping;      // seamless across the antimeridian
  t.wrapT = THREE.ClampToEdgeWrapping;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.magFilter = THREE.LinearFilter;
  t.generateMipmaps = true;
  return t;
};

const dayMap = tex('earth_day.jpg');
const nightMap = tex('earth_night.jpg');
const cloudMap = tex('earth_clouds.jpg');
const oceanMap = tex('earth_ocean.jpg');
const topoMap = tex('earth_topo.jpg');

/* ── starfield: three shells so parallax reads as real depth ────────────── */
function makeStarLayer({ count, near, far, size, brightness }) {
  const pos = new Float32Array(count * 3);
  const col = new Float32Array(count * 3);
  const siz = new Float32Array(count);
  const pha = new Float32Array(count);
  const c = new THREE.Color();

  for (let i = 0; i < count; i++) {
    // uniform direction on the sphere, radius spread across the shell
    const u = Math.random() * 2 - 1;
    const th = Math.random() * Math.PI * 2;
    const s = Math.sqrt(1 - u * u);
    const r = near + Math.pow(Math.random(), 0.6) * (far - near);
    pos[i * 3] = s * Math.cos(th) * r;
    pos[i * 3 + 1] = u * r;
    pos[i * 3 + 2] = s * Math.sin(th) * r;

    // mostly white, a few warm and a few blue giants
    const roll = Math.random();
    const hue = roll > 0.94 ? 0.07 : roll > 0.86 ? 0.58 : 0.6;
    const sat = roll > 0.86 ? 0.45 : 0.06;
    c.setHSL(hue, sat, brightness * (0.62 + Math.random() * 0.38));
    col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;

    siz[i] = size * (0.45 + Math.pow(Math.random(), 2.2) * 1.5);
    pha[i] = Math.random() * Math.PI * 2;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aColor', new THREE.BufferAttribute(col, 3));
  geo.setAttribute('aSize', new THREE.BufferAttribute(siz, 1));
  geo.setAttribute('aPhase', new THREE.BufferAttribute(pha, 1));

  const mat = new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 }, uScale: { value: innerHeight / 2 } },
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    vertexShader: /* glsl */`
      attribute vec3 aColor; attribute float aSize; attribute float aPhase;
      uniform float uTime, uScale;
      varying vec3 vColor; varying float vTwinkle;
      void main() {
        vColor = aColor;
        vTwinkle = 0.75 + 0.25 * sin(uTime * 1.4 + aPhase);
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        // clamp or near-shell stars balloon into blobs a few dozen px across
        gl_PointSize = clamp(aSize * uScale / max(-mv.z, 0.001), 0.6, 3.0);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */`
      varying vec3 vColor; varying float vTwinkle;
      void main() {
        vec2 d = gl_PointCoord - 0.5;
        float r2 = dot(d, d);
        if (r2 > 0.25) discard;
        float core = smoothstep(0.25, 0.0, r2);
        float halo = smoothstep(0.25, 0.02, r2) * 0.35;
        gl_FragColor = vec4(vColor * vTwinkle, core + halo);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });

  return new THREE.Points(geo, mat);
}

const starLayers = [
  makeStarLayer({ count: 16000, near: 420, far: 1400, size: 1.1, brightness: 0.5 }),
  makeStarLayer({ count: 5400, near: 170, far: 420, size: 1.0, brightness: 0.68 }),
  makeStarLayer({ count: 1200, near: 55, far: 170, size: 0.9, brightness: 0.92 }),
];
starLayers.forEach((l) => scene.add(l));

/* ── earth ──────────────────────────────────────────────────────────────── */
const earthGroup = new THREE.Group();
earthGroup.rotation.z = AXIAL_TILT;
scene.add(earthGroup);

const earthSpin = new THREE.Group();     // everything that turns with the surface
earthGroup.add(earthSpin);

const SRGB_DECODE = /* glsl */`
  vec3 decode(vec3 c) { return pow(c, vec3(2.2)); }
`;

const earthMat = new THREE.ShaderMaterial({
  uniforms: {
    uDay: { value: dayMap },
    uNight: { value: nightMap },
    uOcean: { value: oceanMap },
    uTopo: { value: topoMap },
    uClouds: { value: cloudMap },
    uSun: { value: SUN_DIR.clone() },
    uCloudOffset: { value: 0 },
    uTexel: { value: new THREE.Vector2(1 / 4096, 1 / 2048) },
    uBump: { value: 9.0 },
  },
  vertexShader: /* glsl */`
    varying vec2 vUv; varying vec3 vN; varying vec3 vWorld;
    varying vec3 vT; varying vec3 vB;
    void main() {
      vUv = uv;
      vec3 nObj = normalize(normal);
      // Build the tangent frame in object space, where the pole is always +Y.
      // Deriving it from world +Y instead would skew once the axial tilt is applied.
      vec3 eastObj = normalize(cross(vec3(0.0, 1.0, 0.0), nObj));   // +u direction
      vec3 northObj = cross(nObj, eastObj);                          // +v direction
      vN = normalize(mat3(modelMatrix) * nObj);
      vT = normalize(mat3(modelMatrix) * eastObj);
      vB = normalize(mat3(modelMatrix) * northObj);
      vec4 wp = modelMatrix * vec4(position, 1.0);
      vWorld = wp.xyz;
      gl_Position = projectionMatrix * viewMatrix * wp;
    }`,
  fragmentShader: /* glsl */`
    uniform sampler2D uDay, uNight, uOcean, uTopo, uClouds;
    uniform vec3 uSun; uniform float uCloudOffset, uBump;
    uniform vec2 uTexel;
    varying vec2 vUv; varying vec3 vN; varying vec3 vWorld;
    varying vec3 vT; varying vec3 vB;
    ${SRGB_DECODE}

    void main() {
      vec3 N = normalize(vN);
      vec3 L = normalize(uSun);
      vec3 V = normalize(cameraPosition - vWorld);
      mat3 TBN = mat3(normalize(vT), normalize(vB), N);

      vec3 day = decode(texture2D(uDay, vUv).rgb);
      vec3 night = decode(texture2D(uNight, vUv).rgb);
      float ocean = texture2D(uOcean, vUv).r;
      float land = 1.0 - ocean;

      // ── relief: perturb the normal from the height field, land only ──────
      float h  = texture2D(uTopo, vUv).r;
      float hx = texture2D(uTopo, vUv + vec2(uTexel.x, 0.0)).r;
      float hy = texture2D(uTopo, vUv + vec2(0.0, uTexel.y)).r;
      float s = uBump * land;
      vec3 Np = normalize(TBN * normalize(vec3((h - hx) * s, (h - hy) * s, 1.0)));

      float ndl = dot(Np, L);        // shading uses the bumped normal
      float ndlGeo = dot(N, L);      // day/night split uses the true sphere normal
      float lit = smoothstep(-0.16, 0.26, ndlGeo);

      // cloud shadow, displaced away from the sun across the surface
      vec2 sunUv = normalize(vec2(dot(L, normalize(vT)), dot(L, normalize(vB))) + 1e-6);
      vec2 cloudUv = vec2(vUv.x + uCloudOffset, vUv.y);
      float cl = texture2D(uClouds, cloudUv).r;
      float clShadow = texture2D(uClouds, cloudUv - sunUv * 0.0032).r;

      // ── surface ──────────────────────────────────────────────────────────
      vec3 albedo = day;
      // deepen the open ocean a touch so it doesn't read flat grey-blue
      albedo = mix(albedo, albedo * vec3(0.72, 0.86, 1.12), ocean * 0.55);

      float diffuse = clamp(ndl, 0.0, 1.0);
      vec3 surface = albedo * (0.035 + 1.08 * diffuse);
      surface *= 1.0 - clShadow * 0.42 * lit;

      // ── sun glint, water only, blocked by cloud ──────────────────────────
      vec3 H = normalize(L + V);
      float ndh = max(dot(N, H), 0.0);
      float fres = 0.02 + 0.98 * pow(1.0 - max(dot(V, H), 0.0), 5.0);
      float spec = pow(ndh, 620.0) * ocean * lit * fres * 1.6;
      spec *= 1.0 - cl * 0.85;

      // ── warm scattering through the terminator ───────────────────────────
      // Keep this narrow. Spread wide it stops reading as dusk and just smears a
      // brown band down the limb.
      float twilight = exp(-ndlGeo * ndlGeo * 190.0);
      vec3 dusk = vec3(1.0, 0.46, 0.18) * twilight * 0.14 * (0.35 + 0.65 * land);

      // ── city lights, deep night only, dimmed under cloud ─────────────────
      float nightMask = smoothstep(0.08, -0.22, ndlGeo);
      vec3 city = night * vec3(1.0, 0.80, 0.52) * 2.9 * nightMask * (1.0 - cl * 0.55);

      // ── atmospheric rim over the surface ─────────────────────────────────
      float rim = pow(1.0 - max(dot(N, V), 0.0), 3.6);
      vec3 rimCol = vec3(0.26, 0.52, 1.0) * rim * lit * 0.42;

      vec3 color = surface + spec + dusk + city + rimCol;
      gl_FragColor = vec4(color, 1.0);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
});

const earth = new THREE.Mesh(new THREE.SphereGeometry(EARTH_R, 256, 160), earthMat);
earthSpin.add(earth);

/* clouds on their own shell, drifting slightly faster than the ground */
const cloudMat = new THREE.ShaderMaterial({
  uniforms: {
    uClouds: { value: cloudMap },
    uSun: { value: SUN_DIR.clone() },
    uTexel: { value: new THREE.Vector2(1 / 2048, 1 / 1024) },
  },
  transparent: true,
  depthWrite: false,
  vertexShader: /* glsl */`
    varying vec2 vUv; varying vec3 vN; varying vec3 vWorld;
    void main() {
      vUv = uv;
      vN = normalize(mat3(modelMatrix) * normal);
      vec4 wp = modelMatrix * vec4(position, 1.0);
      vWorld = wp.xyz;
      gl_Position = projectionMatrix * viewMatrix * wp;
    }`,
  fragmentShader: /* glsl */`
    uniform sampler2D uClouds; uniform vec3 uSun; uniform vec2 uTexel;
    varying vec2 vUv; varying vec3 vN; varying vec3 vWorld;
    void main() {
      float d = texture2D(uClouds, vUv).r;
      float a = smoothstep(0.13, 0.66, d);
      if (a < 0.004) discard;

      vec3 N = normalize(vN);
      vec3 L = normalize(uSun);
      vec3 V = normalize(cameraPosition - vWorld);
      float ndl = dot(N, L);
      float lit = smoothstep(-0.20, 0.32, ndl);

      // Fake thickness: sample the density field toward the sun. Where cloud sits
      // sunward of this fragment it is self-shadowed, which gives the tops relief
      // instead of a flat white sheet.
      vec3 T = normalize(cross(vec3(0.0, 1.0, 0.0), N));
      vec3 B = cross(N, T);
      vec2 sunUv = normalize(vec2(dot(L, T), dot(L, B)) + 1e-6);
      float toward = texture2D(uClouds, vUv + sunUv * 0.0026).r;
      float selfShade = 1.0 - clamp((toward - d) * 1.5, 0.0, 0.55);

      vec3 sunlit = vec3(1.0, 0.985, 0.96) * selfShade;
      vec3 dusk = vec3(1.0, 0.55, 0.30);
      float twilight = exp(-ndl * ndl * 30.0);
      vec3 col = mix(vec3(0.015, 0.022, 0.038), sunlit, lit);
      col = mix(col, dusk * selfShade, twilight * 0.55);

      // fade the shell at the silhouette so it doesn't ring the planet
      float edge = smoothstep(0.0, 0.30, dot(N, V));
      gl_FragColor = vec4(col, a * (0.16 + 0.84 * lit) * edge);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
});
const clouds = new THREE.Mesh(new THREE.SphereGeometry(CLOUD_R, 160, 96), cloudMat);
earthSpin.add(clouds);

/* atmosphere: back-facing shell, additive fresnel */
const atmoMat = new THREE.ShaderMaterial({
  uniforms: { uSun: { value: SUN_DIR.clone() } },
  side: THREE.BackSide,
  transparent: true,
  depthWrite: false,
  blending: THREE.AdditiveBlending,
  vertexShader: /* glsl */`
    varying vec3 vN; varying vec3 vWorld;
    void main() {
      vN = normalize(mat3(modelMatrix) * normal);
      vec4 wp = modelMatrix * vec4(position, 1.0);
      vWorld = wp.xyz;
      gl_Position = projectionMatrix * viewMatrix * wp;
    }`,
  fragmentShader: /* glsl */`
    uniform vec3 uSun;
    varying vec3 vN; varying vec3 vWorld;
    void main() {
      vec3 N = normalize(-vN);
      vec3 V = normalize(cameraPosition - vWorld);
      vec3 L = normalize(uSun);
      float ndl = dot(N, L);

      // two lobes: a tight bright band right at the limb over a faint outer haze
      float grazing = 1.0 - max(dot(N, V), 0.0);
      float tight = pow(grazing, 7.5);
      float broad = pow(grazing, 3.6);

      float lit = smoothstep(-0.35, 0.40, ndl);
      // Rayleigh-ish: blue where the sun is high, reddening as it grazes, because
      // that light has taken the longest path through the atmosphere
      float sunset = exp(-ndl * ndl * 34.0);
      vec3 blue = vec3(0.24, 0.52, 1.0);
      vec3 warm = vec3(1.0, 0.47, 0.22);
      vec3 col = mix(vec3(0.015, 0.05, 0.16), blue, lit);
      col = mix(col, warm, sunset * 0.5);

      float intensity = (broad * 0.22 + tight * 1.7) * (0.04 + 1.7 * lit);
      gl_FragColor = vec4(col * intensity, 1.0);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
});
const atmosphere = new THREE.Mesh(new THREE.SphereGeometry(ATMO_R, 64, 48), atmoMat);
earthGroup.add(atmosphere);

/* lat/lon -> world position (geo.js does the maths, three.js gets the vector) */
function latLonToVec3(lat, lon, radius = EARTH_R) {
  const p = latLonXYZ(lat, lon, radius);
  return new THREE.Vector3(p.x, p.y, p.z);
}

/* ── satellite ──────────────────────────────────────────────────────────── */
const satAnchor = new THREE.Group();     // holds the craft at the orbit point
scene.add(satAnchor);

let satellite = null;
let wingAxle = null;

new GLTFLoader(manager).load('assets/satellite.glb', (gltf) => {
  const model = gltf.scene;

  // normalise: centre on origin and scale so the wingspan is SAT_SPAN
  const box = new THREE.Box3().setFromObject(model);
  const size = new THREE.Vector3();
  const centre = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(centre);
  model.position.sub(centre);
  const holder = new THREE.Group();
  holder.add(model);
  holder.scale.setScalar(SAT_SPAN / Math.max(size.x, size.y, size.z));

  // wings onto their own axle so they can rotate on the spar toward the sun
  wingAxle = new THREE.Group();
  model.add(wingAxle);
  model.children.filter((c) => /SolarWing/i.test(c.name)).forEach((w) => wingAxle.add(w));

  satellite = holder;
  satAnchor.add(holder);
});

/* Blender exports the craft y-up: the dish points +Z, the wing spar runs along X.
   Build the orientation from an explicit basis rather than eulers - dish onto the
   nadir, spar onto the orbit normal so the single-axis array never stalls. */
const _z = new THREE.Vector3(), _x = new THREE.Vector3(), _y = new THREE.Vector3();
const _basis = new THREE.Matrix4();
function aimSatellite(position, orbitNormal) {
  _z.copy(position).negate().normalize();               // dish -> earth centre
  _x.copy(orbitNormal).normalize();
  _x.sub(_z.clone().multiplyScalar(_x.dot(_z))).normalize();   // orthogonalise
  _y.crossVectors(_z, _x).normalize();
  _basis.makeBasis(_x, _y, _z);
  satAnchor.position.copy(position);
  satAnchor.quaternion.setFromRotationMatrix(_basis);
}

/* ── target marker ──────────────────────────────────────────────────────── */
const marker = new THREE.Group();
marker.visible = false;
earthSpin.add(marker);

const pinMat = new THREE.MeshBasicMaterial({ color: 0xffb454, transparent: true, opacity: 0.95 });
const pinDot = new THREE.Mesh(new THREE.SphereGeometry(0.012, 16, 12), pinMat);
marker.add(pinDot);

const ringMat = new THREE.MeshBasicMaterial({
  color: 0xffb454, transparent: true, opacity: 0.7, side: THREE.DoubleSide, depthWrite: false,
});
const ring = new THREE.Mesh(new THREE.RingGeometry(0.026, 0.032, 48), ringMat);
marker.add(ring);
const ring2 = new THREE.Mesh(new THREE.RingGeometry(0.05, 0.054, 48), ringMat.clone());
marker.add(ring2);

const beamMat = new THREE.MeshBasicMaterial({
  color: 0xffb454, transparent: true, opacity: 0.18, depthWrite: false, side: THREE.DoubleSide,
});
const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.05, 1, 20, 1, true), beamMat);
beam.visible = false;
scene.add(beam);

/* ── hover reticle on the globe ─────────────────────────────────────────── */
const reticle = new THREE.Group();
reticle.visible = false;
scene.add(reticle);
const retMat = new THREE.MeshBasicMaterial({
  color: 0x58b7ff, transparent: true, opacity: 0.85, side: THREE.DoubleSide, depthWrite: false,
});
reticle.add(new THREE.Mesh(new THREE.RingGeometry(0.018, 0.021, 40), retMat));
const retDot = new THREE.Mesh(new THREE.CircleGeometry(0.004, 16), retMat);
reticle.add(retDot);

/* ── interaction state ──────────────────────────────────────────────────── */
const state = {
  mode: 'orbit',            // orbit | slewing | holding
  orbitAngle: 0,
  slew: null,
  target: null,             // { lat, lon, name, localDir }
  camTween: null,
  hoverLatLon: null,
  satHovered: false,
  pointer: new THREE.Vector2(-10, -10),
  pointerActive: false,
  parallax: new THREE.Vector2(),
  dragging: false,
};

const raycaster = new THREE.Raycaster();
raycaster.params.Points.threshold = 0.01;

function orbitPosition(angle) {
  const p = new THREE.Vector3(Math.cos(angle) * ORBIT_R, 0, -Math.sin(angle) * ORBIT_R);
  p.applyAxisAngle(new THREE.Vector3(1, 0, 0), ORBIT_TILT);
  return p;
}
const ORBIT_NORMAL = new THREE.Vector3(0, 1, 0).applyAxisAngle(new THREE.Vector3(1, 0, 0), ORBIT_TILT);

/* ── pointer handling ───────────────────────────────────────────────────── */
canvas.addEventListener('pointermove', (e) => {
  state.pointer.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  state.pointerActive = true;
  state.clientX = e.clientX;
  state.clientY = e.clientY;
});
canvas.addEventListener('pointerleave', () => {
  state.pointerActive = false;
  $('cursor-readout').hidden = true;
  $('sat-tip').hidden = true;
  reticle.visible = false;
});
canvas.addEventListener('pointerdown', () => { state.dragging = true; canvas.classList.add('grabbing'); });
addEventListener('pointerup', () => { state.dragging = false; canvas.classList.remove('grabbing'); });

canvas.addEventListener('click', () => {
  if (state.satHovered) openConsole();
});

/* ── console ────────────────────────────────────────────────────────────── */
const consoleEl = $('console');
const queryEl = $('query');

function openConsole() {
  consoleEl.hidden = false;
  consoleEl.setAttribute('aria-hidden', 'false');
  $('console-error').hidden = true;
  queryEl.value = '';
  renderSuggestions('');
  setTimeout(() => queryEl.focus(), 40);
}
function closeConsole() {
  consoleEl.hidden = true;
  consoleEl.setAttribute('aria-hidden', 'true');
}
$('console-close').addEventListener('click', closeConsole);
consoleEl.addEventListener('click', (e) => { if (e.target === consoleEl) closeConsole(); });
addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (!consoleEl.hidden) closeConsole();
    else if (state.target) releaseTarget();
  }
});

const QUICK = ['Tokyo', 'New York', 'London', 'Cairo', 'Sydney', 'Rio de Janeiro', 'Reykjavik', 'Mumbai'];
$('chips').innerHTML = QUICK.map((q) => `<button type="button">${q}</button>`).join('');
$('chips').addEventListener('click', (e) => {
  if (e.target.tagName === 'BUTTON') { queryEl.value = e.target.textContent; submit(); }
});

function renderSuggestions(q) {
  const list = $('suggestions');
  const hits = q.trim() ? findPlaces(q, 6) : [];
  list.innerHTML = hits.map((p) => {
    const i = p.name.toLowerCase().indexOf(q.trim().toLowerCase());
    const marked = i < 0 ? p.name
      : `${p.name.slice(0, i)}<em>${p.name.slice(i, i + q.trim().length)}</em>${p.name.slice(i + q.trim().length)}`;
    return `<li data-lat="${p.lat}" data-lon="${p.lon}" data-name="${p.name}">${marked}, ${p.country}<span>${fmtLat(p.lat)} ${fmtLon(p.lon)}</span></li>`;
  }).join('');
}
queryEl.addEventListener('input', () => renderSuggestions(queryEl.value));
$('suggestions').addEventListener('click', (e) => {
  const li = e.target.closest('li');
  if (!li) return;
  goTo(+li.dataset.lat, +li.dataset.lon, li.dataset.name);
  closeConsole();
});

$('console-form').addEventListener('submit', (e) => { e.preventDefault(); submit(); });

function submit() {
  const raw = queryEl.value.trim();
  if (!raw) return;
  const parsed = parseQuery(raw);
  if (!parsed) {
    const err = $('console-error');
    err.textContent = `No match for "${raw}". Try a city name, or coordinates like 35.68, 139.69`;
    err.hidden = false;
    return;
  }
  goTo(parsed.lat, parsed.lon, parsed.name);
  closeConsole();
}

/* ── targeting ──────────────────────────────────────────────────────────── */
function goTo(lat, lon, name, { instant = false } = {}) {
  const localDir = latLonToVec3(lat, lon, 1).normalize();
  state.target = { lat, lon, name, localDir };

  marker.position.copy(localDir).multiplyScalar(EARTH_R * 1.002);
  marker.lookAt(marker.position.clone().multiplyScalar(2));
  marker.visible = true;

  // satellite slews from wherever it is onto the point above the target
  const from = satAnchor.position.clone().normalize();
  const to = localDir.clone().applyQuaternion(worldSpinQuat());
  const camDir = to.clone();
  const dist = clamp(camera.position.length(), 1.9, 3.1);

  if (instant) {
    // shared links arrive already on target rather than flying in from the default view
    aimSatellite(to.clone().multiplyScalar(ORBIT_R), ORBIT_NORMAL);
    camera.position.copy(camDir.multiplyScalar(dist));
    controls.update();
    state.slew = null;
    state.camTween = null;
    state.mode = 'holding';
  } else {
    state.slew = { from, to, t: 0, dur: SLEW_DUR };
    state.mode = 'slewing';
    state.camTween = { from: camera.position.clone(), to: camDir.multiplyScalar(dist), t: 0, dur: CAM_DUR };
  }

  $('target-name').textContent = name.toUpperCase();
  $('target-coords').textContent = `${fmtLat(lat)}  ${fmtLon(lon)}`;
  $('hint').innerHTML = 'Tracking target · <b>ESC</b> to resume free orbit';
}

function releaseTarget() {
  state.target = null;
  state.mode = 'orbit';
  state.slew = null;
  marker.visible = false;
  beam.visible = false;
  $('target-label').hidden = true;
  $('hint').innerHTML = 'Drag to orbit · scroll to zoom · <b>click the satellite</b> to target a location';
}

/* quaternion taking earth-local directions into world space */
function worldSpinQuat() {
  earthSpin.updateWorldMatrix(true, false);
  return new THREE.Quaternion().setFromRotationMatrix(earthSpin.matrixWorld);
}

/* ── resize ─────────────────────────────────────────────────────────────── */
function onResize() {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  composer.setSize(innerWidth, innerHeight);
  composer.setPixelRatio(Math.min(devicePixelRatio, 2));
  starLayers.forEach((l) => { l.material.uniforms.uScale.value = innerHeight / 2; });
}
addEventListener('resize', onResize);

/* ── frame loop ─────────────────────────────────────────────────────────── */
const clock = new THREE.Clock();
let fpsAcc = performance.now(), fpsFrames = 0;
const tmpV = new THREE.Vector3();
const AXIS = new THREE.Vector3(0, 1, 0).applyAxisAngle(new THREE.Vector3(0, 0, 1), AXIAL_TILT);

function tick() {
  requestAnimationFrame(tick);
  const dt = Math.min(clock.getDelta(), 0.05);
  const t = clock.elapsedTime;

  /* earth + clouds */
  const spinDelta = SPIN * dt;
  earthSpin.rotation.y += spinDelta;
  clouds.rotation.y += spinDelta * 0.28;
  earthMat.uniforms.uCloudOffset.value = (clouds.rotation.y - earthSpin.rotation.y) / (Math.PI * 2);

  /* while tracking, carry the camera round with the planet so the target stays framed */
  if (state.mode === 'holding' && !state.dragging) {
    camera.position.applyAxisAngle(AXIS, spinDelta);
  }

  /* satellite placement */
  if (state.mode === 'orbit') {
    state.orbitAngle += dt * 0.16;
    aimSatellite(orbitPosition(state.orbitAngle), ORBIT_NORMAL);
  } else if (state.mode === 'slewing' && state.slew) {
    const s = state.slew;
    s.t = Math.min(1, s.t + dt / s.dur);
    const k = easeInOut(s.t);
    // slerp along the great circle, easing the altitude up and back down
    const dir = s.from.clone().lerp(s.to, k).normalize();
    const lift = 1 + Math.sin(Math.PI * s.t) * 0.16;
    aimSatellite(dir.multiplyScalar(ORBIT_R * lift), ORBIT_NORMAL);
    if (s.t >= 1) { state.mode = 'holding'; state.slew = null; }
  } else if (state.mode === 'holding' && state.target) {
    const dir = state.target.localDir.clone().applyQuaternion(worldSpinQuat());
    aimSatellite(dir.multiplyScalar(ORBIT_R), ORBIT_NORMAL);
  }

  /* wings track the sun about the spar */
  if (satellite && wingAxle) {
    satellite.updateWorldMatrix(true, false);
    const inv = new THREE.Matrix4().copy(satellite.matrixWorld).invert();
    const sunLocal = SUN_DIR.clone().transformDirection(inv);
    wingAxle.rotation.x = Math.atan2(sunLocal.z, sunLocal.y);
  }

  /* camera tween after targeting */
  if (state.camTween) {
    const c = state.camTween;
    c.t = Math.min(1, c.t + dt / c.dur);
    const k = easeInOut(c.t);
    camera.position.copy(c.from).lerp(c.to, k);
    // keep the radius steady instead of cutting through the chord
    camera.position.normalize().multiplyScalar(THREE.MathUtils.lerp(c.from.length(), c.to.length(), k));
    if (c.t >= 1) state.camTween = null;
  }

  /* beam from satellite down to the marker */
  if (state.target && (state.mode === 'holding' || state.mode === 'slewing')) {
    const a = satAnchor.position;
    marker.updateWorldMatrix(true, false);
    const b = new THREE.Vector3().setFromMatrixPosition(marker.matrixWorld);
    const mid = a.clone().add(b).multiplyScalar(0.5);
    const len = a.distanceTo(b);
    beam.position.copy(mid);
    beam.scale.set(1, len, 1);
    beam.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    beam.visible = true;
    beamMat.opacity = 0.10 + 0.07 * Math.sin(t * 3.2);
    ring2.scale.setScalar(1 + 0.14 * Math.sin(t * 2.4));
    ringMat.opacity = 0.55 + 0.25 * Math.sin(t * 2.4);
  }

  /* pointer picking */
  updatePointer();

  /* subtle parallax: the whole starfield leans away from the cursor */
  const px = state.pointerActive && !state.dragging ? state.pointer.x : 0;
  const py = state.pointerActive && !state.dragging ? state.pointer.y : 0;
  state.parallax.x += (px * 0.028 - state.parallax.x) * 0.045;
  state.parallax.y += (py * 0.020 - state.parallax.y) * 0.045;
  starLayers.forEach((l, i) => {
    const depth = 1 - i * 0.28;
    l.rotation.y = state.parallax.x * depth;
    l.rotation.x = -state.parallax.y * depth;
    l.material.uniforms.uTime.value = t;
  });

  controls.update();
  composer.render();

  if (DEBUG) {
    let el = $('debug');
    if (!el) { el = document.createElement('pre'); el.id = 'debug'; document.body.appendChild(el); }
    el.textContent = JSON.stringify({
      mode: state.mode,
      t: +t.toFixed(2),
      cam: camera.position.toArray().map((v) => +v.toFixed(3)),
      camLen: +camera.position.length().toFixed(3),
      tween: state.camTween ? +state.camTween.t.toFixed(3) : null,
      tweenTo: state.camTween ? state.camTween.to.toArray().map((v) => +v.toFixed(3)) : null,
      sat: satAnchor.position.toArray().map((v) => +v.toFixed(3)),
      target: state.target ? { name: state.target.name, lat: +state.target.lat.toFixed(2) } : null,
    });
  }

  /* telemetry */
  // measured off wall time, not the clamped simulation dt
  const now = performance.now();
  fpsFrames++;
  if (now - fpsAcc >= 500) {
    $('tel-fps').textContent = Math.min(999, Math.round((fpsFrames * 1000) / (now - fpsAcc)));
    fpsAcc = now; fpsFrames = 0;
    const altKm = Math.round((camera.position.length() - EARTH_R) * 6371);
    $('tel-alt').textContent = `${altKm.toLocaleString()} km`;
  }

  /* pinned target label */
  if (state.target && marker.visible) {
    marker.updateWorldMatrix(true, false);
    tmpV.setFromMatrixPosition(marker.matrixWorld);
    const facing = tmpV.clone().normalize().dot(camera.position.clone().normalize());
    tmpV.project(camera);
    const label = $('target-label');
    if (facing > 0.02 && tmpV.z < 1) {
      label.hidden = false;
      label.style.left = `${(tmpV.x * 0.5 + 0.5) * innerWidth}px`;
      label.style.top = `${(-tmpV.y * 0.5 + 0.5) * innerHeight}px`;
    } else {
      label.hidden = true;
    }
  }
}

function updatePointer() {
  if (!state.pointerActive) return;
  raycaster.setFromCamera(state.pointer, camera);

  // satellite first: it sits in front of the globe
  let satHit = false;
  if (satellite) {
    satHit = raycaster.intersectObject(satellite, true).length > 0;
  }
  state.satHovered = satHit;
  const tip = $('sat-tip');
  if (satHit) {
    tip.hidden = false;
    tip.style.left = `${state.clientX}px`;
    tip.style.top = `${state.clientY}px`;
    canvas.classList.add('targetable');
  } else {
    tip.hidden = true;
    canvas.classList.remove('targetable');
  }

  const hits = satHit ? [] : raycaster.intersectObject(earth, false);
  const readout = $('cursor-readout');
  if (hits.length) {
    const hit = hits[0];
    const local = earthSpin.worldToLocal(hit.point.clone());
    const { lat, lon } = vec3ToLatLon(local);
    state.hoverLatLon = { lat, lon };

    readout.hidden = false;
    readout.style.left = `${state.clientX}px`;
    readout.style.top = `${state.clientY}px`;
    $('cursor-coords').textContent = `${fmtLat(lat)}  ${fmtLon(lon)}`;
    $('cursor-place').textContent = nearestPlace(lat, lon) || 'open water';
    $('tel-lat').textContent = fmtLat(lat);
    $('tel-lon').textContent = fmtLon(lon);

    reticle.visible = true;
    reticle.position.copy(hit.point);
    reticle.lookAt(hit.point.clone().add(hit.face.normal.clone().transformDirection(earth.matrixWorld)));
    canvas.classList.add('pointing');
  } else {
    readout.hidden = true;
    reticle.visible = false;
    canvas.classList.remove('pointing');
    if (!state.target) { $('tel-lat').textContent = '—'; $('tel-lon').textContent = '—'; }
  }
}

/* ── deep link: ?target=Tokyo  or  ?lat=35.68&lon=139.69 ────────────────── */
function applyDeepLink() {
  const q = new URLSearchParams(location.search);
  const lat = parseFloat(q.get('lat'));
  const lon = parseFloat(q.get('lon'));
  if (Number.isFinite(lat) && Number.isFinite(lon)) {
    const hit = parseQuery(`${lat}, ${lon}`);
    if (hit) goTo(hit.lat, hit.lon, hit.name, { instant: true });
    return;
  }
  const term = q.get('target');
  if (term) {
    const hit = parseQuery(term);
    if (hit) goTo(hit.lat, hit.lon, hit.name, { instant: true });
  }
}

/* ── boot ───────────────────────────────────────────────────────────────── */
onResize();
aimSatellite(orbitPosition(0), ORBIT_NORMAL);
tick();

const bootedAt = manager.onLoad;
manager.onLoad = () => { bootedAt(); applyDeepLink(); };

// expose a little surface for the smoke test
window.__orbital = {
  state, latLonToVec3, vec3ToLatLon, parseQuery, PLACES, THREE,
  scene, camera, controls, satAnchor, goTo, releaseTarget,
  get satellite() { return satellite; },
};
