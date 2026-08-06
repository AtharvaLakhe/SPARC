/* District geometry for the globe overlay.
 *
 * ── Why a uniform tint and not a false-colour raster ─────────────────────────
 * The result behind every card is *one zonal statistic per district* — a single
 * number computed over the whole polygon. Painting a varying raster inside that
 * polygon would show sub-district structure that the data does not contain, and
 * a viewer would read the texture as information. So the patch is flat: one
 * district, one value, one tint. The shape carries where; the colour carries
 * which indicator; the opacity carries how much it moved.
 *
 * That is not a compromise, it is the faithful rendering. A prettier lie would
 * be easy and would be exactly the failure this project is built to avoid.
 * ────────────────────────────────────────────────────────────────────────────
 *
 * Real districts contribute their validated boundary. Generated demo districts
 * only have a bounding box, and they are flagged so the globe can draw them
 * differently — an approximate rectangle must not pass for a surveyed outline. */

import nagpurGeo from '@validated/nagpur.geojson?raw';
import bengaluruGeo from '@validated/bengaluru-urban.geojson?raw';
import mumbaiCityGeo from '@validated/mumbai-city.geojson?raw';
import mumbaiCombinedGeo from '@global-boundaries/mumbai.geojson?raw';
import { cityForRegionId } from '../catalog/cities';

/** [lon, lat] */
export type LonLat = [number, number];

export interface DistrictShape {
  /** Outer ring first, then holes. */
  rings: LonLat[][];
  /** Every polygon in the validated feature, including detached district parts. */
  polygons: LonLat[][][];
  /** True when the outline is a bounding box, not a surveyed boundary. */
  approximate: boolean;
  label: string;
}

interface GeoFeature {
  type: string;
  properties: Record<string, unknown>;
  geometry: { type: string; coordinates: unknown };
}

/* Parsed once. `?raw` rather than a JSON import because these files carry the
   .geojson extension, which Vite's JSON plugin does not claim. */
function parse(raw: string): GeoFeature | null {
  try { return JSON.parse(raw) as GeoFeature; } catch { return null; }
}

const REAL: Record<string, GeoFeature | null> = {
  nagpur: parse(nagpurGeo),
  'bengaluru-urban': parse(bengaluruGeo),
  'mumbai-city': parse(mumbaiCityGeo),
  mumbai: parse(mumbaiCombinedGeo),
};

function polygonsFromFeature(f: GeoFeature): LonLat[][][] {
  if (f.geometry.type === 'Polygon') return [f.geometry.coordinates as LonLat[][]];
  if (f.geometry.type === 'MultiPolygon') return f.geometry.coordinates as LonLat[][][];
  return [];
}

function ringsFromFeature(f: GeoFeature): LonLat[][] {
  const polys = polygonsFromFeature(f);
  if (polys.length > 1) {
    // Largest part only. The globe patch is an orientation cue, not a cadastral
    // rendering, and stitching every island in adds vertices for no legibility.
    return polys.reduce((best, p) => ((p[0]?.length ?? 0) > (best[0]?.length ?? 0) ? p : best), polys[0] ?? []);
  }
  return polys[0] ?? [];
}

function boxRings(bbox: [number, number, number, number]): LonLat[][] {
  const [w, s, e, n] = bbox;
  return [[[w, s], [e, s], [e, n], [w, n], [w, s]]];
}

/**
 * Resolve a region id to something the globe can draw.
 * Returns null when the region is unknown — the globe then draws nothing, which
 * is correct: an absent district is not an empty district.
 */
export function shapeForRegion(
  regionId: string,
  bbox?: [number, number, number, number],
): DistrictShape | null {
  // Real, gated geometry.
  for (const [key, feature] of Object.entries(REAL)) {
    if (!feature) continue;
    const sparcId = feature.properties.sparcRegionId as string | undefined;
    if (regionId.includes(key) || (sparcId && sparcId === regionId)) {
      const rings = ringsFromFeature(feature);
      const polygons = polygonsFromFeature(feature);
      if (rings.length) {
        return {
          rings,
          polygons,
          approximate: false,
          label: (feature.properties.sparcDisplayName as string)
            ?? (feature.properties.sparcScope as string)
            ?? key,
        };
      }
    }
  }

  // Catalog city envelope — bounding box only and explicitly approximate.
  const city = cityForRegionId(regionId);
  if (city) {
    const rings = boxRings(city.bbox);
    return {
      rings,
      polygons: [rings],
      approximate: true,
      label: city.name,
    };
  }

  if (bbox) {
    const rings = boxRings(bbox);
    return { rings, polygons: [rings], approximate: true, label: regionId };
  }
  return null;
}

/**
 * Intensity for the patch, 0..1, from the percentage change.
 * Log-compressed for the same reason the picker dials are: district-scale
 * change is usually a few percent, and a linear map renders everything
 * identically faint.
 */
export function intensityFor(percentChange: number | null): number {
  if (percentChange === null || !Number.isFinite(percentChange)) return 0.18;
  const mag = Math.min(1, Math.log10(1 + Math.abs(percentChange)) / Math.log10(31));
  return 0.2 + mag * 0.55;
}
