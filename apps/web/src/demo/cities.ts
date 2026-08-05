/* Compatibility exports for older offline transport callers.
 *
 * The previous module generated plausible-looking numbers from a seeded random
 * function. That was unsafe: a number in an analytical card can be mistaken
 * for a satellite result. The city catalogue now contains explicit coverage
 * and provenance state, and fallback responses contain null metrics only. */

import summaryTemplate from '@fixtures/district-summary.mock.json';
import waterTemplate from '@fixtures/water-comparison.mock.json';
import vegetationTemplate from '@fixtures/vegetation-comparison.mock.json';
import builtTemplate from '@fixtures/built-up-comparison.mock.json';
import type { DistrictSummaryResponse, IndicatorComparisonResponse } from '../contract/types';
import {
  CITY_CATALOG,
  catalogRegion,
  cityForRegionId,
  type CityCatalogEntry,
} from '../catalog/cities';

export type DemoCity = CityCatalogEntry;
export const DEMO_CITIES = CITY_CATALOG;

export function regionIdFor(city: DemoCity): string { return city.regionId; }

const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

function unavailableMetric() {
  return {
    baselineValue: null,
    comparisonValue: null,
    absoluteChange: null,
    percentChange: null,
    unit: 'not available',
    unavailableReason: 'No validated Earth Engine pack is available for this city; report and export remain available.',
  };
}

function unavailableQuality() {
  return {
    level: 'unknown' as const,
    basis: 'unavailable',
    methodVersion: '0.0.0',
    reasons: ['No processing pack has been published for this city.'],
    warnings: ['This fallback contains no satellite measurement.'],
    evidence: {
      commonValidPercent: null,
      cloudPercent: null,
      nodataPercent: null,
      coveragePercent: null,
      sceneCountBaseline: null,
      sceneCountComparison: null,
      thresholdSensitivityPercent: null,
      independentValidationComplete: false,
      usersAccuracy: null,
      producersAccuracy: null,
    },
  };
}

export function summaryForCity(city: DemoCity): DistrictSummaryResponse {
  const out = clone(summaryTemplate) as unknown as DistrictSummaryResponse;
  out.data.region = catalogRegion(city);
  out.data.indicators = out.data.indicators.map((item) => ({
    ...item,
    metric: unavailableMetric(),
    qualityLevel: 'unknown' as const,
    status: 'unavailable' as const,
    comparisonUrl: `/api/v1/regions/${city.regionId}/indicators/${item.indicator.id}`,
  }));
  out.meta = {
    ...out.meta,
    requestId: `catalog:fallback:${city.slug}:summary`,
    mock: true,
    warnings: ['No validated Earth Engine pack is available for this city; report/export scope only.'],
  };
  out.links = { self: `/api/v1/regions/${city.regionId}/summary`, related: [] };
  return out;
}

export function comparisonForCity(city: DemoCity, indicatorId: string): IndicatorComparisonResponse | null {
  if (!['surface-water', 'vegetation', 'built-up'].includes(indicatorId)) return null;
  const template = indicatorId === 'surface-water' ? waterTemplate
    : indicatorId === 'vegetation' ? vegetationTemplate : builtTemplate;
  const out = clone(template) as unknown as IndicatorComparisonResponse;
  out.data.region = catalogRegion(city);
  out.data.comparisonId = `${city.regionId}:${indicatorId}`;
  out.data.metric = unavailableMetric();
  out.data.quality = unavailableQuality();
  out.data.status = 'unavailable';
  out.data.layers = [];
  out.data.interpretation = {
    ...out.data.interpretation,
    summary: 'No satellite-derived estimate is available for this city.',
    caveats: ['Report generation and evidence export are available without a validated processing pack.'],
  };
  out.meta = {
    ...out.meta,
    requestId: `catalog:fallback:${city.slug}:${indicatorId}`,
    mock: true,
    warnings: ['No validated Earth Engine pack is available for this city; report/export scope only.'],
  };
  out.links = { self: `/api/v1/regions/${city.regionId}/indicators/${indicatorId}`, related: [] };
  return out;
}

/** Legacy picker preview shape. Fallback cities intentionally have no numeric preview. */
export function previewFor(_city: DemoCity) {
  return { water: null, vegetation: null, built: null, coverage: null };
}

export function demoRegions() {
  return CITY_CATALOG.map(catalogRegion);
}

export { CITY_CATALOG, cityForRegionId };
