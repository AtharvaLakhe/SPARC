/* Synthetic demo districts for the quick-target cities.
 *
 * ── READ THIS BEFORE USING ANY NUMBER FROM HERE ─────────────────────────────
 * Every value in this file is INVENTED. These are not observations, not
 * measurements, and not findings. They exist so the interface can be exercised
 * and demonstrated over a handful of recognisable places rather than a single
 * district.
 *
 * They sit at exactly the same evidence grade as the committed
 * `contracts/examples/*.mock.json` fixtures — `meta.mock: true`, `mock:` region
 * ids — which is what makes them safe to ship: the view model reads that flag
 * and the UI labels the whole session "Synthetic demo data".
 *
 * The one real district (Nagpur) keeps its own pre-publication pack and is NOT
 * generated here. Confusing the two is the failure this project exists to
 * avoid, so they are deliberately kept in separate files with separate ids.
 * ────────────────────────────────────────────────────────────────────────────
 *
 * Construction: clone a committed fixture and substitute. Building payloads
 * from scratch would drift from the schema the moment the contract moved;
 * patching a real fixture means these inherit its shape for free, and the
 * transport's Ajv check still runs over every one of them. */

import summaryTemplate from '@fixtures/district-summary.mock.json';
import waterTemplate from '@fixtures/water-comparison.mock.json';
import vegetationTemplate from '@fixtures/vegetation-comparison.mock.json';
import builtTemplate from '@fixtures/built-up-comparison.mock.json';
import type {
  DistrictSummaryResponse,
  IndicatorComparisonResponse,
  RegionRef,
} from '../contract/types';

export interface DemoCity {
  slug: string;
  name: string;
  country: string;
  lat: number;
  lon: number;
  /** Half-width of the synthetic district box, in degrees. */
  span: number;
  /** One-line reason this place is interesting, shown on the card. */
  story: string;
}

/* The eight quick targets from the globe's own console, plus Nagpur's
   neighbours are deliberately absent — Nagpur is real and lives elsewhere. */
export const DEMO_CITIES: DemoCity[] = [
  { slug: 'tokyo', name: 'Tokyo', country: 'Japan', lat: 35.6762, lon: 139.6503, span: 0.55, story: 'Dense coastal megacity; reclaimed land and bay water' },
  { slug: 'new-york', name: 'New York', country: 'United States', lat: 40.7128, lon: -74.006, span: 0.5, story: 'Estuary city; heavy built surface against tidal water' },
  { slug: 'london', name: 'London', country: 'United Kingdom', lat: 51.5074, lon: -0.1278, span: 0.45, story: 'Temperate river basin with substantial urban green' },
  { slug: 'cairo', name: 'Cairo', country: 'Egypt', lat: 30.0444, lon: 31.2357, span: 0.5, story: 'Desert margin; vegetation confined to the Nile corridor' },
  { slug: 'sydney', name: 'Sydney', country: 'Australia', lat: -33.8688, lon: 151.2093, span: 0.5, story: 'Harbour city bounded by bushland and drought cycles' },
  { slug: 'rio-de-janeiro', name: 'Rio de Janeiro', country: 'Brazil', lat: -22.9068, lon: -43.1729, span: 0.5, story: 'Forested massifs inside a dense coastal metropolis' },
  { slug: 'reykjavik', name: 'Reykjavik', country: 'Iceland', lat: 64.1466, lon: -21.9426, span: 0.45, story: 'Sub-arctic; short growing season and low built density' },
  { slug: 'mumbai', name: 'Mumbai', country: 'India', lat: 19.076, lon: 72.8777, span: 0.4, story: 'Monsoon coast; creeks, mangrove and rapid built growth' },
];

/* ── deterministic pseudo-randomness ─────────────────────────────────────────
   Seeded from the slug so a city always shows the same numbers. Random values
   that changed per reload would make the demo look broken and would make any
   screenshot unreproducible. */
function seedFrom(text: string): number {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function makeRng(seed: number): () => number {
  let s = seed || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

const round = (n: number, dp = 2) => Number(n.toFixed(dp));

interface CityFigures {
  water: { baseline: number; comparison: number };
  vegetation: { baseline: number; comparison: number };
  built: { baseline: number; comparison: number };
  coverage: number;
  cloud: number;
  scenesBaseline: number;
  scenesComparison: number;
  sensitivity: number;
}

/* Ranges are chosen to be *plausible* rather than accurate — a synthetic value
   that is wildly impossible undermines the demo, and one that looks precise
   invites belief. These are the middle path, and every screen says they are
   invented. */
function figuresFor(city: DemoCity): CityFigures {
  const rng = makeRng(seedFrom(city.slug));
  const area = (city.span * 111) ** 2 * 1.2;          // rough km² of the box

  const waterShare = 0.02 + rng() * 0.10;
  const waterBase = area * waterShare;
  const waterDrift = (rng() - 0.55) * 0.14;            // slight bias to loss

  const vegBase = 0.22 + rng() * 0.42;                 // NDVI
  const vegDrift = (rng() - 0.55) * 0.10;

  const builtShare = 0.10 + rng() * 0.35;
  const builtBase = area * builtShare;
  const builtDrift = rng() * 0.16;                     // built-up trends up

  return {
    water: { baseline: round(waterBase, 1), comparison: round(waterBase * (1 + waterDrift), 1) },
    vegetation: { baseline: round(vegBase, 2), comparison: round(vegBase * (1 + vegDrift), 2) },
    built: { baseline: round(builtBase, 1), comparison: round(builtBase * (1 + builtDrift), 1) },
    coverage: round(78 + rng() * 20, 1),
    cloud: round(rng() * 22, 1),
    scenesBaseline: 4 + Math.floor(rng() * 6),
    scenesComparison: 4 + Math.floor(rng() * 6),
    sensitivity: round(3 + rng() * 22, 1),
  };
}

export function regionIdFor(city: DemoCity): string {
  return `mock:district:${city.slug}`;
}

function regionFor(city: DemoCity): RegionRef {
  return {
    id: regionIdFor(city),
    name: `${city.name} — DEMO`,
    type: 'district',
    parentId: null,
    bbox: [
      round(city.lon - city.span, 4), round(city.lat - city.span, 4),
      round(city.lon + city.span, 4), round(city.lat + city.span, 4),
    ],
    centroid: [round(city.lon, 4), round(city.lat, 4)],
    geometryUrl: null,
    indicatorIds: ['surface-water', 'vegetation', 'built-up'],
  };
}

function metric(baseline: number, comparison: number, unit: string) {
  const abs = round(comparison - baseline, unit === 'NDVI' ? 3 : 2);
  return {
    baselineValue: baseline,
    comparisonValue: comparison,
    absoluteChange: abs,
    percentChange: baseline === 0 ? null : round((abs / baseline) * 100, 2),
    unit,
    unavailableReason: null,
  };
}

const clone = <T,>(v: T): T => JSON.parse(JSON.stringify(v)) as T;

export function summaryForCity(city: DemoCity): DistrictSummaryResponse {
  const f = figuresFor(city);
  const out = clone(summaryTemplate) as unknown as DistrictSummaryResponse;
  const region = regionFor(city);

  out.data.region = region;
  out.data.baselinePeriod.sceneCount = f.scenesBaseline;
  out.data.comparisonPeriod.sceneCount = f.scenesComparison;

  const byId: Record<string, ReturnType<typeof metric>> = {
    'surface-water': metric(f.water.baseline, f.water.comparison, 'km2'),
    vegetation: metric(f.vegetation.baseline, f.vegetation.comparison, 'NDVI'),
    'built-up': metric(f.built.baseline, f.built.comparison, 'km2'),
  };

  out.data.indicators = out.data.indicators
    .filter((i) => byId[i.indicator.id])
    .map((i) => ({
      ...i,
      indicator: { ...i.indicator, name: `${i.indicator.name.replace(' — MOCK', '')} — DEMO` },
      metric: byId[i.indicator.id]!,
      // Synthetic data cannot have earned a quality grade. Saying "unknown" is
      // the only honest option and it is also what the real Nagpur vegetation
      // result reports, so the UI path is the same one the real data uses.
      qualityLevel: 'unknown',
      comparisonUrl: `/api/v1/comparisons/${regionIdFor(city)}:${i.indicator.id}`,
    }));

  out.meta = {
    ...out.meta,
    requestId: `mock:request:${city.slug}-summary`,
    mock: true,
    warnings: [
      'SYNTHETIC DEMO VALUES — invented to exercise the interface, not observations',
      `${city.name} has no processed satellite pack; these numbers are generated`,
    ],
  };
  out.links = {
    self: `/api/v1/regions/${regionIdFor(city)}/summary`,
    related: [`/api/v1/regions/${regionIdFor(city)}/indicators`],
  };
  return out;
}

const TEMPLATES: Record<string, unknown> = {
  'surface-water': waterTemplate,
  vegetation: vegetationTemplate,
  'built-up': builtTemplate,
};

export function comparisonForCity(
  city: DemoCity,
  indicatorId: string,
): IndicatorComparisonResponse | null {
  const template = TEMPLATES[indicatorId];
  if (!template) return null;

  const f = figuresFor(city);
  const out = clone(template) as unknown as IndicatorComparisonResponse;
  const region = regionFor(city);

  const m = indicatorId === 'surface-water' ? metric(f.water.baseline, f.water.comparison, 'km2')
    : indicatorId === 'vegetation' ? metric(f.vegetation.baseline, f.vegetation.comparison, 'NDVI')
      : metric(f.built.baseline, f.built.comparison, 'km2');

  out.data.comparisonId = `${regionIdFor(city)}:${indicatorId}`;
  out.data.region = region;
  out.data.indicator = { ...out.data.indicator, name: `${out.data.indicator.name.replace(' — MOCK', '')} — DEMO` };
  out.data.metric = m;
  out.data.baselinePeriod.sceneCount = f.scenesBaseline;
  out.data.comparisonPeriod.sceneCount = f.scenesComparison;

  out.data.quality = {
    ...out.data.quality,
    level: 'unknown',
    /* `basis` is a closed enum in the contract — validated | heuristic |
       unavailable. "synthetic" was not one of them, and the transport's Ajv
       check correctly refused the whole payload rather than rendering it.
       "unavailable" is the honest member of that set: no assessment was
       performed, because no processing was. The synthetic nature of the data is
       carried by meta.mock and by the warnings, which is where the UI reads it
       from anyway. */
    basis: 'unavailable',
    reasons: ['Values are generated for demonstration; no processing has been run for this district'],
    warnings: ['Not an observation. No scene was read and no threshold was applied.'],
    evidence: {
      ...out.data.quality.evidence,
      commonValidPercent: f.coverage,
      cloudPercent: f.cloud,
      nodataPercent: round(Math.max(0, 100 - f.coverage - f.cloud) / 4, 1),
      coveragePercent: round(Math.min(99.9, f.coverage + 4), 1),
      sceneCountBaseline: f.scenesBaseline,
      sceneCountComparison: f.scenesComparison,
      thresholdSensitivityPercent: f.sensitivity,
      independentValidationComplete: false,
      usersAccuracy: null,
      producersAccuracy: null,
    },
  };

  out.data.interpretation = {
    ...out.data.interpretation,
    summary: `DEMO: ${city.name} — ${city.story}. `
      + `The generated ${indicatorId.replace('-', ' ')} proxy is `
      + `${(m.absoluteChange ?? 0) >= 0 ? 'higher' : 'lower'} in the comparison window.`,
    caveats: [
      'This district has not been processed. Every figure here is generated.',
      ...out.data.interpretation.caveats,
    ],
  };

  // No layer exists for a district that was never processed. Claiming one would
  // point at an image that cannot be produced.
  out.data.layers = [];
  out.data.status = 'complete';

  out.meta = {
    ...out.meta,
    requestId: `mock:request:${city.slug}-${indicatorId}`,
    mock: true,
    warnings: [
      'SYNTHETIC DEMO VALUES — invented to exercise the interface, not observations',
      `${city.name} has no processed satellite pack; these numbers are generated`,
    ],
  };
  out.links = {
    self: `/api/v1/regions/${regionIdFor(city)}/indicators/${indicatorId}`,
    related: [],
  };
  return out;
}

export function demoRegions(): RegionRef[] {
  return DEMO_CITIES.map(regionFor);
}

export function cityForRegionId(regionId: string): DemoCity | null {
  return DEMO_CITIES.find((c) => regionIdFor(c) === regionId) ?? null;
}

/** Headline figures for the picker cards, without going through the transport. */
export function previewFor(city: DemoCity) {
  const f = figuresFor(city);
  const pct = (a: number, b: number) => (a === 0 ? 0 : ((b - a) / a) * 100);
  return {
    water: pct(f.water.baseline, f.water.comparison),
    vegetation: pct(f.vegetation.baseline, f.vegetation.comparison),
    built: pct(f.built.baseline, f.built.comparison),
    coverage: f.coverage,
  };
}
