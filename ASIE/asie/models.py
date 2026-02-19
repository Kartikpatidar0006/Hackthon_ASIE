"""Pydantic data models used across the ASIE system."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────

class DataSource(str, Enum):
    JOBS = "jobs"
    PATENTS = "patents"
    RESEARCH = "research"
    STARTUPS = "startups"
    POLICY = "policy"
    SOCIAL = "social"


class SkillCategory(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    DOMAIN = "domain"
    TOOL = "tool"
    METHODOLOGY = "methodology"
    CERTIFICATION = "certification"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    MOMENTUM_SPIKE = "momentum_spike"
    DISRUPTION = "disruption"
    BUBBLE_WARNING = "bubble_warning"
    EMERGING_SKILL = "emerging_skill"
    DECLINING_SKILL = "declining_skill"


class Industry(str, Enum):
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    ENERGY = "energy"
    EDUCATION = "education"
    RETAIL = "retail"
    GOVERNMENT = "government"


# ── Core Models ────────────────────────────────────────────────────────────

class Skill(BaseModel):
    """Canonical skill entity."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    canonical_name: str  # normalised form
    category: SkillCategory
    aliases: List[str] = Field(default_factory=list)
    parent_domain: Optional[str] = None
    related_skills: List[str] = Field(default_factory=list)
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SkillSignal(BaseModel):
    """A single data-point / signal for a skill from any source."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_id: str
    source: DataSource
    timestamp: datetime
    value: float  # normalised demand signal (0-1)
    raw_count: int = 0
    geo: Optional[str] = None
    industry: Optional[Industry] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SkillForecast(BaseModel):
    """Forecasted metrics for a skill."""
    skill_id: str
    skill_name: str
    horizon_years: int = 5
    growth_score: float = Field(ge=0, le=1)
    confidence_score: float = Field(ge=0, le=1)
    volatility_score: float = Field(ge=0, le=1)
    momentum_index: float = 0.0
    bubble_score: float = Field(ge=0, le=1, default=0.0)
    automation_risk: float = Field(ge=0, le=1, default=0.0)
    predicted_demand: List[float] = Field(default_factory=list)
    prediction_intervals: List[Dict[str, float]] = Field(default_factory=list)
    model_contributions: Dict[str, float] = Field(default_factory=dict)
    shap_explanations: Dict[str, float] = Field(default_factory=dict)
    geo: Optional[str] = None
    industry: Optional[Industry] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SkillGap(BaseModel):
    """A gap between a user's current skills and market demand."""
    skill_name: str
    current_level: float = Field(ge=0, le=1, default=0.0)
    market_demand: float = Field(ge=0, le=1)
    gap_score: float = Field(ge=0, le=1)
    priority: RiskLevel = RiskLevel.MEDIUM
    recommended_resources: List[str] = Field(default_factory=list)
    growth_forecast: float = 0.0
    future_trend: str = ""  # e.g. "↑ High demand in 3-5 yrs"


class RoleFitResult(BaseModel):
    """How well a candidate fits a specific job role."""
    role_id: str
    role_name: str
    readiness_score: float = Field(ge=0, le=1, default=0.0)
    matched_skills: List[str] = Field(default_factory=list)
    missing_required: List[str] = Field(default_factory=list)
    missing_preferred: List[str] = Field(default_factory=list)
    trend_outlook: str = "stable"
    future_demand_multiplier: float = 1.0


class ResumeAnalysis(BaseModel):
    """Result of a privacy-preserving resume analysis."""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    extracted_skills: List[str] = Field(default_factory=list)
    skill_gaps: List[SkillGap] = Field(default_factory=list)
    overall_readiness_score: float = Field(ge=0, le=1, default=0.0)
    top_recommended_skills: List[str] = Field(default_factory=list)
    industry_fit: Dict[str, float] = Field(default_factory=dict)
    # ── Role-based analysis fields ────────────────────
    target_role: Optional[str] = None
    role_readiness_score: Optional[float] = Field(default=None, ge=0, le=1)
    role_fit_results: List[RoleFitResult] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(BaseModel):
    """Emerging-skill / disruption alert."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: AlertType
    skill_name: str
    message: str
    severity: RiskLevel = RiskLevel.MEDIUM
    momentum_delta: float = 0.0
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BacktestResult(BaseModel):
    """Evaluation metrics from a back-testing run."""
    skill_name: str
    mape: float  # Mean Absolute Percentage Error
    rmse: float  # Root Mean Square Error
    mae: float  # Mean Absolute Error
    directional_accuracy: float  # % of correct direction predictions
    forecast_horizon: int = 5
    model_used: str = "ensemble"
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Graph Models ───────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    category: str
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str  # e.g. "prerequisite", "complementary", "parent"
    weight: float = 1.0
