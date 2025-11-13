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


from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field


# ---------- Core submodels ----------

class UserProfile(BaseModel):
    current_age: float = Field(..., description="User's current age in years.")
    currency: str = Field(..., description="Primary currency code, e.g. USD, INR.")
    annual_income: Optional[float] = Field(
        None, description="Estimated gross annual income."
    )
    monthly_expenses: Optional[float] = Field(
        None, description="Estimated current monthly living expenses."
    )
    current_investments: Optional[float] = Field(
        None, description="Total current investable assets used in projections."
    )
    risk_tolerance: Literal["low", "moderate", "high", "unspecified"] = Field(
        "unspecified", description="User's stated risk tolerance."
    )


class OverallAssessment(BaseModel):
    summary: str = Field(..., description="Plain English overall summary.")
    overall_health_score: Optional[float] = Field(
        None,
        description="0–100 score representing overall financial goal health.",
        ge=0,
        le=100,
    )
    key_strengths: List[str] = Field(
        default_factory=list, description="Main positives in the user's plan."
    )
    key_risks: List[str] = Field(
        default_factory=list, description="Main risks or weaknesses in the plan."
    )


class GoalAssumptions(BaseModel):
    expected_return: Optional[float] = Field(
        None, description="Expected annualized return as decimal (e.g. 0.08 for 8%)."
    )
    inflation_rate: Optional[float] = Field(
        None, description="Expected annual inflation rate as decimal."
    )
    retirement_duration_years: Optional[float] = Field(
        None,
        description="For retirement goals, assumed number of years of withdrawals.",
    )
    property_price_inflation: Optional[float] = Field(
        None, description="For home goals, expected property price inflation."
    )
    mortgage_rate: Optional[float] = Field(
        None, description="For home goals, assumed mortgage interest rate."
    )
    loan_tenure_years: Optional[float] = Field(
        None, description="For debt or mortgage, assumed tenure in years."
    )


class GoalSpecific(BaseModel):
    # Home purchase
    house_cost_future: Optional[float] = Field(
        None, description="Estimated total house cost at purchase date."
    )
    down_payment_pct: Optional[float] = Field(
        None, description="Target down payment ratio for home purchase."
    )
    target_down_payment: Optional[float] = Field(
        None, description="Target down payment absolute amount."
    )
    current_down_payment_savings: Optional[float] = Field(
        None, description="Current savings earmarked for down payment."
    )

    # Debt
    outstanding_balance: Optional[float] = Field(
        None, description="Outstanding loan or debt balance."
    )
    interest_rate: Optional[float] = Field(
        None, description="Annual interest rate on the debt as a decimal."
    )
    recommended_monthly_payment: Optional[float] = Field(
        None, description="Suggested monthly payment to hit payoff target."
    )
    current_monthly_payment: Optional[float] = Field(
        None, description="Current monthly payment amount toward this debt."
    )


class ProjectionRow(BaseModel):
    year: Optional[int] = Field(
        None, description="Calendar year for this row, if applicable."
    )
    age: Optional[float] = Field(
        None, description="User age at this step, if applicable."
    )
    month_label: Optional[str] = Field(
        None, description="Optional YYYY-MM label for monthly projections."
    )
    starting_balance: Optional[float] = Field(
        None, description="Balance at beginning of the period."
    )
    contributions: Optional[float] = Field(
        None, description="Total contributions during the period."
    )
    growth: Optional[float] = Field(
        None, description="Investment growth during the period."
    )
    withdrawals: Optional[float] = Field(
        None, description="Total withdrawals during the period."
    )
    ending_balance: Optional[float] = Field(
        None, description="Balance at end of the period."
    )
    goal_progress_pct: Optional[float] = Field(
        None,
        description="Ending balance as a percentage of required future goal amount (0–100).",
    )


class Projection(BaseModel):
    frequency: Literal["monthly", "annual"] = Field(
        "annual", description="Projection time step granularity."
    )
    rows: List[ProjectionRow] = Field(
        default_factory=list,
        description="Each row is a point-in-time snapshot in the projection.",
    )


class ActionRecommendation(BaseModel):
    priority: Literal["high", "medium", "low"] = Field(
        ..., description="How urgent or impactful this action is."
    )
    recommendation: str = Field(
        ..., description="Human-readable recommendation text."
    )
    estimated_impact: Optional[str] = Field(
        None, description="Optional description of expected impact."
    )


# ---------- Goal & scenarios ----------

class Goal(BaseModel):
    goal_id: str = Field(..., description="Internal identifier for the goal.")
    name: str = Field(..., description="Human-readable name of the goal.")
    type: Literal[
        "retirement",
        "early_retirement",
        "home_purchase",
        "debt_payoff",
        "education",
        "emergency_fund",
        "travel",
        "business",
        "other",
    ] = Field(..., description="Type of goal.")

    priority: Optional[Literal["low", "medium", "high"]] = Field(
        None, description="Relative importance of this goal."
    )

    target_age: Optional[float] = Field(
        None, description="Target age by which this goal should be achieved."
    )
    target_year: Optional[int] = Field(
        None, description="Target calendar year for the goal."
    )
    time_horizon_years: Optional[float] = Field(
        None, description="Approximate number of years until goal."
    )

    target_amount_today: Optional[float] = Field(
        None, description="Required amount in today's money (real terms)."
    )
    target_amount_future: Optional[float] = Field(
        None, description="Required amount at goal date after inflation."
    )

    status: Literal["on_track", "slightly_behind", "behind", "ahead", "unknown"] = Field(
        ..., description="Current tracking status relative to projections."
    )
    probability_of_success: Optional[float] = Field(
        None,
        description="0–1 probability of fully funding this goal based on simulations.",
        ge=0,
        le=1,
    )

    required_monthly_savings: Optional[float] = Field(
        None, description="Monthly savings needed going forward to reach the goal."
    )
    current_monthly_savings: Optional[float] = Field(
        None, description="Current monthly savings allocated to this goal."
    )
    gap_to_close: Optional[float] = Field(
        None,
        description="Difference between required and current monthly savings (can be negative if ahead).",
    )

    assumptions: Optional[GoalAssumptions] = Field(
        None, description="Key numeric assumptions used for this goal's projections."
    )
    goal_specific: Optional[GoalSpecific] = Field(
        None, description="Optional goal-type-specific fields."
    )
    projection: Optional[Projection] = Field(
        None, description="Projected balances over time."
    )
    action_recommendations: List[ActionRecommendation] = Field(
        default_factory=list,
        description="Concrete suggestions specifically for this goal.",
    )


class ScenarioChanges(BaseModel):
    expected_return: Optional[float] = Field(
        None, description="Adjusted expected return, if applicable."
    )
    inflation_rate: Optional[float] = Field(
        None, description="Adjusted inflation rate, if applicable."
    )
    additional_monthly_savings: Optional[float] = Field(
        None, description="Change in monthly savings compared to base case."
    )
    retirement_age_shift: Optional[float] = Field(
        None, description="Change in retirement age (e.g., +2 years)."
    )


class Scenario(BaseModel):
    scenario_id: str = Field(..., description="Internal identifier for the scenario.")
    name: str = Field(..., description="Human-readable scenario name.")
    changes: ScenarioChanges = Field(
        default_factory=ScenarioChanges,
        description="Key parameter tweaks for this scenario.",
    )
    impact_summary: str = Field(
        ..., description="Plain language summary of how this scenario affects goals."
    )
    suggested_adjustments: List[str] = Field(
        default_factory=list,
        description="Suggested user actions in response to this scenario.",
    )


class Explanations(BaseModel):
    key_terms: Optional[Dict[str, str]] = Field(
        None, description="Optional mapping of technical term -> explanation."
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Limitations and caveats of the projections.",
    )


# ---------- Root result model ----------

class GoalPlanResult(BaseModel):
    """
    Computed financial plan summary and projections for one or more goals.
    """

    user_profile: UserProfile
    overall_assessment: OverallAssessment
    goals: List[Goal] = Field(
        default_factory=list, description="Detailed information per financial goal."
    )
    scenario_analysis: List[Scenario] = Field(
        default_factory=list,
        description="What-if scenarios and their impact on goals.",
    )
    explanations: Optional[Explanations] = Field(
        None, description="Definitions and caveats to help interpret the results."
    )
    natural_language_summary: Optional[str] = Field(
        None, description="Short human-readable summary of the entire plan."
    )

class Overview(BaseModel):
    companyName: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    currentPrice: Optional[float]
    oneYearChange: Optional[float]
    compareToSP500: Optional[float]
    summary: str

class Valuation(BaseModel):
    trailingPE: Optional[float]
    forwardPE: Optional[float]
    priceToBook: Optional[float]
    enterpriseToRevenue: Optional[float]
    enterpriseToEbitda: Optional[float]
    marketCap: Optional[float]
    analysis: str

class Momentum(BaseModel):
    fiftyTwoWeekHigh: Optional[float]
    fiftyTwoWeekLow: Optional[float]
    dayHigh: Optional[float]
    dayLow: Optional[float]
    trendSummary: str
    volumeAnalysis: str

class Fundamentals(BaseModel):
    revenueGrowth: Optional[float]
    earningsGrowth: Optional[float]
    profitMargins: Optional[float]
    operatingMargins: Optional[float]
    grossMargins: Optional[float]
    totalCash: Optional[float]
    totalDebt: Optional[float]
    freeCashflow: Optional[float]
    analysis: str

class Dividends(BaseModel):
    dividendYield: Optional[float]
    payoutRatio: Optional[float]
    lastDividendValue: Optional[float]
    dividendSummary: str

class Risks(BaseModel):
    beta: Optional[float]
    valuationRisk: str
    balanceSheetRisk: str
    earningsRisk: str
    macroRisk: str

class MarketInsightsResult(BaseModel):
    ticker: str
    overview: Overview
    valuation: Valuation
    momentum: Momentum
    fundamentals: Fundamentals
    dividends: Dividends
    risks: Risks
    summaryInsight: str

