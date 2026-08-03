/* Transport interface.
 *
 * Both implementations take the same canonical selection and return the same
 * validated contract shapes. That symmetry is the requirement from
 * docs/project-status.md — "both transports yield one validated view model for
 * the same supported request" — and it is what lets the demo fall back to
 * offline files mid-presentation without changing a single component. */

import type {
  ComparisonSelection,
  DistrictSummaryResponse,
  IndicatorComparisonResponse,
  RegionRef,
} from '../contract/types';

export interface Transport {
  /** Human-readable name, shown in the disclosure panel. */
  readonly label: string;
  /** True when this transport needs no network at all. */
  readonly offlineCapable: boolean;

  listRegions(signal?: AbortSignal): Promise<RegionRef[]>;
  getRegionSummary(
    selection: ComparisonSelection,
    signal?: AbortSignal,
  ): Promise<DistrictSummaryResponse>;
  getIndicatorComparison(
    selection: ComparisonSelection,
    indicatorId: string,
    signal?: AbortSignal,
  ): Promise<IndicatorComparisonResponse>;
}
