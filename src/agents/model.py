from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AllocationItem(BaseModel):
    category: str = Field(
        description="Name of the bucket (e.g. 'Equity', 'Bonds', 'US', 'International Developed', 'Technology')"
    )
    weight_percent: float = Field(
        description="Approximate share of total portfolio, 0–100"
    )
    comment: Optional[str] = Field(
        default=None,
        description="Short comment explaining why this bucket matters, if relevant",
    )


class ConcentrationFlag(BaseModel):
    label: str = Field(
        description="What is concentrated (e.g. 'AAPL', 'US Tech sector', 'Home country bias')"
    )
    weight_percent: float = Field(
        description="Approximate percent of total portfolio for this concentration"
    )
    concern_level: Literal["low", "moderate", "high"] = Field(
        description="How concerning this concentration might be from a diversification standpoint"
    )
    explanation: str = Field(
        description="Plain-language explanation of why this concentration could matter"
    )


class GapOrIssue(BaseModel):
    topic: str = Field(
        description="Short label, e.g. 'No bond exposure', 'No international equities', 'Overweight tech'"
    )
    explanation: str = Field(
        description="Why this could be a gap or issue"
    )
    potential_impact: Optional[str] = Field(
        default=None,
        description="How this might affect volatility, risk, or long-term behavior of the portfolio",
    )


class FeeComment(BaseModel):
    overall_fee_level: Optional[Literal["unknown", "low", "average", "high"]] = Field(
        default="unknown",
        description="Qualitative judgment of overall fees if data is available",
    )
    observations: List[str] = Field(
        default_factory=list,
        description="Short bullet-style observations about fees and cost efficiency",
    )


class SuitabilityComment(BaseModel):
    assumed_horizon_years: Optional[int] = Field(
        default=None,
        description="User-provided or assumed investment horizon in years",
    )
    assumed_risk_tolerance: Optional[str] = Field(
        default=None,
        description="User-provided or assumed risk tolerance (e.g. 'low', 'moderate', 'high')",
    )
    qualitative_fit: Literal["poor", "mixed", "reasonable", "good", "unclear"] = Field(
        description="Overall judgment of how well the portfolio fits the horizon and risk tolerance",
    )
    explanation: str = Field(
        description="Plain-language explanation backing up the qualitative_fit"
    )


class PortfolioInsights(BaseModel):
    summary: str = Field(
        description="1–3 sentences summarizing the portfolio in plain language"
    )

    allocation_overview_asset_class: List[AllocationItem] = Field(
        description="Breakdown by asset class (equity, bonds, cash, alternatives, etc.)"
    )
    allocation_overview_region: List[AllocationItem] = Field(
        description="Breakdown by region (US, international developed, emerging markets, etc.)"
    )
    allocation_overview_sector: List[AllocationItem] = Field(
        description="Breakdown by sector if possible; can be empty if not enough data"
    )

    risk_level: Literal["low", "moderate", "high", "unclear"] = Field(
        description="Overall qualitative risk level of the portfolio"
    )
    concentration_flags: List[ConcentrationFlag] = Field(
        description="List of notable concentrations; can be empty if none are significant"
    )

    diversification_and_gaps: List[GapOrIssue] = Field(
        description="Key observations about diversification, missing exposures, or overexposed areas"
    )

    fees_and_efficiency: FeeComment = Field(
        description="Comments on fee levels and cost efficiency, if any fee data is available"
    )

    suitability_vs_time_horizon: SuitabilityComment = Field(
        description="Cautious views on whether the portfolio seems aligned with the user's time horizon and risk tolerance"
    )

    questions_and_next_steps: List[str] = Field(
        description="List of reflective questions or next-step ideas for the user to discuss with a professional"
    )

    disclaimer: str = Field(
        description="A brief disclaimer about this being educational only, not financial advice"
    )
