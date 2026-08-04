/* Offline transport over the committed synthetic fixtures.
 *
 * This is the path the demo actually runs on: no server, no network, no
 * request-time processing. The fixtures are imported from their committed
 * location through the `@fixtures` alias, so there is no second copy to drift.
 *
 * It deliberately runs the *same* validation and the *same* period gate as the
 * API. A demo transport that accepts requests the server would reject is worse
 * than useless — it hides exactly the failure you need rehearsed. */

import districtSummary from '@fixtures/district-summary.mock.json';
import waterComparison from '@fixtures/water-comparison.mock.json';
import vegetationComparison from '@fixtures/vegetation-comparison.mock.json';
import builtUpComparison from '@fixtures/built-up-comparison.mock.json';
import lstComparison from '@fixtures/lst-comparison.mock.json';
import partialData from '@fixtures/partial-data.mock.json';

import {
  cityForRegionId, comparisonForCity, demoRegions, summaryForCity,
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

/* Mirrors apps/api/app/repository.py COMPARISON_FILES. Keyed by indicator id,
   never by anything a caller supplies — a request value must not select a file. */
const COMPARISONS: Record<string, unknown> = {
  'surface-water': waterComparison,
  vegetation: vegetationComparison,
  'built-up': builtUpComparison,
  lst: lstComparison,
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
  readonly label = 'Offline demo pack';
  readonly offlineCapable = true;

  private readonly summary: DistrictSummaryResponse;
  private readonly usePartial: boolean;

  constructor(opts: { usePartial?: boolean } = {}) {
    // Validate the fixtures at construction. If a committed example stops
    // satisfying the schema, that is a contract break and it should surface
    // immediately at boot, not on whichever screen happens to open it.
    this.summary = assertDistrictSummary(districtSummary);
    this.usePartial = opts.usePartial ?? false;
  }

  async listRegions(): Promise<RegionRef[]> {
    // The committed Nagpur fixture leads, followed by generated fixtures.
    // Every entry in this transport is synthetic and must stay mock-labelled.
    return [this.summary.data.region, ...demoRegions()];
  }

  async getRegionSummary(selection: ComparisonSelection): Promise<DistrictSummaryResponse> {
    const city = cityForRegionId(selection.regionId);
    if (!city && selection.regionId !== this.summary.data.region.id) {
      throw new DataError('not-found', 'No demo pack exists for the requested region.');
    }
    if (!periodsMatch(selection, this.summary)) {
      throw new DataError(
        'invalid-input',
        'The demo pack only contains the frozen post-monsoon 2019 to 2024 comparison.',
      );
    }
    // Generated districts are validated exactly like the committed fixtures.
    // If the generator ever drifts from the schema this throws here rather than
    // rendering something the contract does not allow.
    if (city) {
      try {
        return assertDistrictSummary(summaryForCity(city));
      } catch (err) {
        if (err instanceof ContractViolation) {
          throw new DataError('contract', err.message, { detail: err.errors });
        }
        throw err;
      }
    }
    return this.summary;
  }

  async getIndicatorComparison(
    selection: ComparisonSelection,
    indicatorId: string,
  ): Promise<IndicatorComparisonResponse> {
    // Resolve the summary first so region and period are gated identically for
    // every indicator, rather than each branch inventing its own check.
    await this.getRegionSummary(selection);

    const city = cityForRegionId(selection.regionId);
    const source = city
      ? comparisonForCity(city, indicatorId)
      : this.usePartial && PARTIAL_OVERRIDE[indicatorId]
        ? PARTIAL_OVERRIDE[indicatorId]
        : COMPARISONS[indicatorId];

    if (!source) {
      throw new DataError('not-found', `No demo result is packaged for "${indicatorId}".`);
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
