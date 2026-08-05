import rawCatalog from '@citycatalog/supported-cities.json';
import type { Bbox, RegionRef } from '../contract/types';

export type AnalyticsCoverage = 'FULLY_SUPPORTED' | 'REPORT_GENERATION_ONLY';
export type RoutingCoverage = 'FULLY_SUPPORTED' | 'REPORT_GENERATION_ONLY' | 'UNSUPPORTED_JURISDICTION';

export interface CityBoundaryDefinition {
  kind: 'validated-adm2' | 'catalog-envelope';
  status: 'VALIDATED' | 'CATALOG_ONLY';
  sourceName: string;
  sourceUrl: string;
  license: string;
  attribution: string;
  sha256: string;
  crs: string;
  definition: string;
  geometryAsset: string | null;
}

export interface CityProcessingPack {
  status: 'VALIDATED' | 'NOT_AVAILABLE';
  packId: string | null;
  manifest: string | null;
  files: Record<string, string>;
  checksums: Record<string, string>;
  boundarySha256: string | null;
}

export interface CityCatalogEntry {
  slug: string;
  regionId: string;
  name: string;
  countryCode: string;
  country: string;
  administrativeAreas: string[];
  district: string | null;
  municipality: string | null;
  centroid: [number, number];
  bbox: Bbox;
  story: string;
  analyticsCoverage: AnalyticsCoverage;
  routingCoverage: RoutingCoverage;
  processingPack: CityProcessingPack;
  boundary: CityBoundaryDefinition;
  jurisdiction: { pack: string; authorityIds: string[] };
}

export const CITY_CATALOG_VERSION = rawCatalog.catalogVersion;
export const CITY_CATALOG_CONTRACT_VERSION = rawCatalog.contractVersion;
export const CITY_BOUNDARY_DISCLAIMER = rawCatalog.boundaryDisclaimer;

/* The JSON file is the shared catalogue source. The cast is deliberately kept
 * at this boundary; every consumer receives the narrower, immutable shape
 * below rather than indexing an unvalidated JSON object. The Python validator
 * in scripts/validate_city_catalog.py applies the same checks before release. */
export const CITY_CATALOG: CityCatalogEntry[] = rawCatalog.cities.map((city) => ({
  ...city,
  administrativeAreas: [...city.administrativeAreas],
  centroid: [city.centroid[0], city.centroid[1]],
  bbox: [city.bbox[0], city.bbox[1], city.bbox[2], city.bbox[3]],
  processingPack: {
    ...city.processingPack,
    files: { ...city.processingPack.files },
    checksums: { ...city.processingPack.checksums },
  },
  jurisdiction: { ...city.jurisdiction, authorityIds: [...city.jurisdiction.authorityIds] },
})) as CityCatalogEntry[];

export function cityForRegionId(regionId: string): CityCatalogEntry | null {
  return CITY_CATALOG.find((city) => city.regionId === regionId) ?? null;
}

export function cityForSlug(slug: string): CityCatalogEntry | null {
  return CITY_CATALOG.find((city) => city.slug === slug) ?? null;
}

export function cityForCoordinate(latitude: number, longitude: number): CityCatalogEntry | null {
  return CITY_CATALOG.find((city) => {
    const [west, south, east, north] = city.bbox;
    return longitude >= west && longitude <= east && latitude >= south && latitude <= north;
  }) ?? null;
}

export function catalogRegion(city: CityCatalogEntry): RegionRef {
  return {
    id: city.regionId,
    name: city.name,
    type: 'district',
    parentId: null,
    bbox: city.bbox,
    centroid: city.centroid,
    geometryUrl: null,
    indicatorIds: ['surface-water', 'vegetation', 'built-up'],
  };
}

export function catalogRegions(): RegionRef[] {
  return CITY_CATALOG.map(catalogRegion);
}

/** Deterministic WGS84 envelope used only for report/export fallback records. */
export function catalogEnvelopeGeometry(city: CityCatalogEntry): Record<string, unknown> {
  const [west, south, east, north] = city.bbox;
  return {
    type: 'Polygon',
    coordinates: [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
  };
}

export function isValidatedCity(city: CityCatalogEntry | null): boolean {
  return city?.analyticsCoverage === 'FULLY_SUPPORTED' && city.processingPack.status === 'VALIDATED';
}
