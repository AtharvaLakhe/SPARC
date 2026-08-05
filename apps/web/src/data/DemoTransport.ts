/* Offline transport over the generated precomputed contract examples.
 *
 * This is the offline path: no server, no network, no
 * request-time processing. The fixtures are imported from their committed
 * location through the `@fixtures` alias, so there is no second copy to drift.
 *
 * It deliberately runs the *same* validation and the *same* period gate as the
 * API. An offline transport that accepts requests the server would reject is worse
 * than useless — it hides exactly the failure you need rehearsed. */

import nagpurSummary from '@fixtures/precomputed/district-nagpur-summary.json';
import bengaluruSummary from '@fixtures/precomputed/district-bengaluru-urban-summary.json';
import nagpurWater from '@fixtures/precomputed/district-nagpur-surface-water.json';
import nagpurVegetation from '@fixtures/precomputed/district-nagpur-vegetation.json';
import nagpurBuiltUp from '@fixtures/precomputed/district-nagpur-built-up.json';
import bengaluruWater from '@fixtures/precomputed/district-bengaluru-urban-surface-water.json';
import bengaluruVegetation from '@fixtures/precomputed/district-bengaluru-urban-vegetation.json';
import bengaluruBuiltUp from '@fixtures/precomputed/district-bengaluru-urban-built-up.json';
import partialData from '@fixtures/partial-data.mock.json';

import {
  cityForRegionId, comparisonForCity, summaryForCity,
} from '../demo/cities';
import type {
  ComparisonSelection,
  DistrictSummaryResponse,
  IndicatorComparisonResponse,
  RegionRef,
} from '../contract/types';
import { assertDistrictSummary, assertIndicatorComparison, ContractViolation } from '../contract/validate';
import { DataError } from './errors';
import type { Transport } from './transport';

const SUMMARIES: Record<string, unknown> = {
  'district:nagpur': nagpurSummary,
  'district:bengaluru-urban': bengaluruSummary,
};

/* Keyed by immutable region and indicator IDs, never by a caller-controlled
   path. The examples are generated from the reviewed Earth Engine packs. */
const COMPARISONS: Record<string, Record<string, unknown>> = {
  'district:nagpur': {
    'surface-water': nagpurWater,
    vegetation: nagpurVegetation,
    'built-up': nagpurBuiltUp,
  },
  'district:bengaluru-urban': {
    'surface-water': bengaluruWater,
    vegetation: bengaluruVegetation,
    'built-up': bengaluruBuiltUp,
  },
};

/* Reachable through a query flag so the partial/unavailable state can be
   rehearsed on demand. It is a real contract fixture, not a simulated failure. */
const PARTIAL_OVERRIDE: Record<string, unknown> = {
  'surface-water': partialData,
};

function periodsMatch(selection: ComparisonSelection, summary: DistrictSummaryResponse): boolean {
  const b = summary.data.baselinePeriod;
  const c = summary.data.comparisonPeriod;
  return (
    selection.baselineStart === b.startDate &&
    selection.baselineEnd === b.endDate &&
    selection.comparisonStart === c.startDate &&
    selection.comparisonEnd === c.endDate
  );
}

export class DemoTransport implements Transport {
  readonly label = 'Local analysis package';
  readonly offlineCapable = true;

  private readonly summaries: Record<string, DistrictSummaryResponse>;
  private readonly usePartial: boolean;

  constructor(opts: { usePartial?: boolean } = {}) {
    // Validate the fixtures at construction. If a committed example stops
    // satisfying the schema, that is a contract break and it should surface
    // immediately at boot, not on whichever screen happens to open it.
    this.summaries = Object.fromEntries(
      Object.entries(SUMMARIES).map(([regionId, payload]) => [regionId, assertDistrictSummary(payload)]),
    );
    this.usePartial = opts.usePartial ?? false;
  }

  async listRegions(): Promise<RegionRef[]> {
    return Object.values(this.summaries).map((summary) => summary.data.region);
  }

  async getRegionSummary(selection: ComparisonSelection): Promise<DistrictSummaryResponse> {
    const summary = this.summaries[selection.regionId];
    const city = cityForRegionId(selection.regionId);
    const fallbackCity = city?.processingPack.status === 'NOT_AVAILABLE' ? city : null;
    if (!summary && !fallbackCity) {
      throw new DataError('not-found', 'No precomputed output exists for the requested region.');
    }
    if (summary && !periodsMatch(selection, summary)) {
      throw new DataError(
        'invalid-input',
        'The offline analysis package only contains the frozen comparison for the selected district.',
      );
    }
    // Keep generated fixtures available only for internal test callers; they
    // are not returned by listRegions and cannot enter the primary picker.
    if (fallbackCity) {
      try {
        return assertDistrictSummary(summaryForCity(fallbackCity));
      } catch (err) {
        if (err instanceof ContractViolation) {
          throw new DataError('contract', err.message, { detail: err.errors });
        }
        throw err;
      }
    }
    return summary as DistrictSummaryResponse;
  }

  async getIndicatorComparison(
    selection: ComparisonSelection,
    indicatorId: string,
  ): Promise<IndicatorComparisonResponse> {
    // Resolve the summary first so region and period are gated identically for
    // every indicator, rather than each branch inventing its own check.
    await this.getRegionSummary(selection);

    const city = cityForRegionId(selection.regionId);
    const fallbackCity = city?.processingPack.status === 'NOT_AVAILABLE' ? city : null;
    const source = fallbackCity
      ? comparisonForCity(fallbackCity, indicatorId)
      : this.usePartial && PARTIAL_OVERRIDE[indicatorId]
        ? PARTIAL_OVERRIDE[indicatorId]
        : COMPARISONS[selection.regionId]?.[indicatorId];

    if (!source) {
      throw new DataError('not-found', `No precomputed result is packaged for "${indicatorId}".`);
    }

    try {
      return assertIndicatorComparison(source);
    } catch (err) {
      if (err instanceof ContractViolation) {
        throw new DataError('contract', err.message, { detail: err.errors });
      }
      throw err;
    }
  }
}
