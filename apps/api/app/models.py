"""Request models and domain validation for the public comparison lookup."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


OPAQUE_ID_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*(?::[a-z0-9]+(?:-[a-z0-9]+)*)*$"
OpaqueRegionId = Annotated[
    str,
    StringConstraints(min_length=1, max_length=128, pattern=OPAQUE_ID_PATTERN),
]
IndicatorId = Literal["surface-water", "vegetation", "built-up", "lst", "suhi"]

MAX_COMPOSITE_DAYS = 366


class PeriodInput(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")

    @model_validator(mode="after")
    def validate_range(self) -> "PeriodInput":
        if self.start_date > self.end_date:
            raise ValueError("startDate must be on or before endDate")
        if (self.end_date - self.start_date).days > MAX_COMPOSITE_DAYS:
            raise ValueError(f"period cannot exceed {MAX_COMPOSITE_DAYS} days")
        if self.end_date > date.today():
            raise ValueError("period cannot end in the future")
        return self


class ComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    region_id: OpaqueRegionId = Field(alias="regionId")
    baseline_period: PeriodInput = Field(alias="baselinePeriod")
    comparison_period: PeriodInput = Field(alias="comparisonPeriod")
    indicator_ids: list[IndicatorId] = Field(alias="indicatorIds", min_length=1, max_length=5)
    mode_preference: Literal["auto", "demo", "live"] = Field(alias="modePreference")

    @model_validator(mode="after")
    def validate_comparison(self) -> "ComparisonRequest":
        if len(set(self.indicator_ids)) != len(self.indicator_ids):
            raise ValueError("indicatorIds must contain unique values")
        if self.baseline_period.end_date >= self.comparison_period.start_date:
            raise ValueError("baselinePeriod must end before comparisonPeriod starts")
        baseline_season = (
            self.baseline_period.start_date.month,
            self.baseline_period.start_date.day,
            self.baseline_period.end_date.month,
            self.baseline_period.end_date.day,
        )
        comparison_season = (
            self.comparison_period.start_date.month,
            self.comparison_period.start_date.day,
            self.comparison_period.end_date.month,
            self.comparison_period.end_date.day,
        )
        if baseline_season != comparison_season:
            raise ValueError("baseline and comparison periods must use the same seasonal window")
        return self


def validate_period_pair(baseline: PeriodInput, comparison: PeriodInput) -> None:
    """Reuse ComparisonRequest's cross-period rules for GET query parameters."""
    ComparisonRequest(
        regionId="validation:region",
        baselinePeriod=baseline.model_dump(by_alias=True),
        comparisonPeriod=comparison.model_dump(by_alias=True),
        indicatorIds=["surface-water"],
        modePreference="demo",
    )

