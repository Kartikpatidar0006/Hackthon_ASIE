"""
ASIE – FastAPI Application Entry Point.

Serves the REST API and static dashboard assets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel

from asie.config import settings

# ── App Setup ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Adaptive Skill Intelligence Engine",
    description="Predict high-demand skills for the next 3–5 years",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# ── Data Loading Helpers ───────────────────────────────────────────────────

def _load_json(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Data file '{filename}' not found. Run `python -m asie.seed` first.",
        )
    with open(path) as f:
        return json.load(f)


def _load_forecasts() -> Dict[str, Any]:
    return _load_json("forecasts.json")


def _load_alerts() -> List[Dict[str, Any]]:
    return _load_json("alerts.json")


def _load_graph() -> Dict[str, Any]:
    return _load_json("graph.json")


# ── Request / Response Models ──────────────────────────────────────────────

class ResumeRequest(BaseModel):
    resume_text: str
    target_industry: Optional[str] = None
    target_geo: Optional[str] = None


class BacktestRequest(BaseModel):
    skill_ids: Optional[List[str]] = None
    n_splits: int = 3


class DisruptionRequest(BaseModel):
    disruption_type: str  # ai_breakthrough, policy_change, economic_shock, paradigm_shift
    affected_skills: List[str]
    description: str
    magnitude: float = 0.5


# ── API Routes ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "Adaptive Skill Intelligence Engine (ASIE)",
        "version": settings.app_version,
        "docs": "/docs",
    }


# ── Skills ─────────────────────────────────────────────────────────────────

@app.get(f"{settings.api_prefix}/skills")
def list_skills(
    category: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """List all skills with current forecast scores."""
    forecasts = _load_forecasts()
    from asie.taxonomy import SKILL_TAXONOMY

    results = []
    for sk in SKILL_TAXONOMY:
        if category and sk.category != category:
            continue
        if domain and sk.domain != domain:
            continue
        fc = forecasts.get(sk.canonical, {})
        results.append({
            "skill_id": sk.canonical,
            "name": sk.canonical.replace("_", " ").title(),
            "category": sk.category,
            "domain": sk.domain,
            "growth_score": fc.get("growth_score", 0.5),
            "confidence_score": fc.get("confidence_score", 0.5),
            "volatility_score": fc.get("volatility_score", 0.3),
            "momentum_index": fc.get("momentum_index", 0.0),
            "bubble_score": fc.get("bubble_score", 0.0),
            "automation_risk": fc.get("automation_risk", 0.3),
            "reliability_score": fc.get("reliability_score", 0.5),
        })

    results.sort(key=lambda x: x["growth_score"], reverse=True)
    return {"skills": results[:limit], "total": len(results)}


@app.get(f"{settings.api_prefix}/skills/{{skill_id}}/forecast")
def get_skill_forecast(skill_id: str):
    """Get detailed forecast for a specific skill."""
    forecasts = _load_forecasts()
    fc = forecasts.get(skill_id)
    if not fc:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")

    from asie.taxonomy import taxonomy_index
    sk_info = taxonomy_index.get(skill_id)

    return {
        "skill_id": skill_id,
        "name": skill_id.replace("_", " ").title(),
        "category": sk_info.category if sk_info else "unknown",
        "domain": sk_info.domain if sk_info else "unknown",
        "forecast": {
            "horizon_months": fc.get("horizon_months", 60),
            "predicted_demand": fc.get("predicted_demand", []),
            "prediction_intervals": fc.get("prediction_intervals", []),
            "growth_score": fc.get("growth_score", 0.5),
            "confidence_score": fc.get("confidence_score", 0.5),
            "volatility_score": fc.get("volatility_score", 0.3),
            "momentum_index": fc.get("momentum_index", 0.0),
            "bubble_score": fc.get("bubble_score", 0.0),
            "automation_risk": fc.get("automation_risk", 0.3),
            "reliability_score": fc.get("reliability_score", 0.5),
        },
        "explanations": fc.get("explanations", {}),
        "model_contributions": fc.get("model_contributions", {}),
    }


@app.get(f"{settings.api_prefix}/skills/trending")
def get_trending_skills(limit: int = Query(default=15, le=50)):
    """Top trending skills by momentum index."""
    forecasts = _load_forecasts()
    items = [
        {
            "skill_id": sid,
            "name": sid.replace("_", " ").title(),
            "momentum_index": fc.get("momentum_index", 0),
            "growth_score": fc.get("growth_score", 0.5),
            "confidence_score": fc.get("confidence_score", 0.5),
        }
        for sid, fc in forecasts.items()
    ]
    items.sort(key=lambda x: abs(x["momentum_index"]), reverse=True)
    return {"trending": items[:limit]}


@app.get(f"{settings.api_prefix}/skills/emerging")
def get_emerging_skills(limit: int = Query(default=10, le=30)):
    """Skills showing signs of rapid emergence."""
    forecasts = _load_forecasts()
    items = []
    for sid, fc in forecasts.items():
        growth = fc.get("growth_score", 0.5)
        momentum = fc.get("momentum_index", 0)
        bubble = fc.get("bubble_score", 0)
        # Emerging = high growth + high momentum + low bubble
        emergence_score = growth * 0.4 + min(abs(momentum), 1) * 0.4 + (1 - bubble) * 0.2
        items.append({
            "skill_id": sid,
            "name": sid.replace("_", " ").title(),
            "emergence_score": round(emergence_score, 4),
            "growth_score": growth,
            "momentum_index": momentum,
            "bubble_score": bubble,
        })
    items.sort(key=lambda x: x["emergence_score"], reverse=True)
    return {"emerging": items[:limit]}


@app.get(f"{settings.api_prefix}/skills/at-risk")
def get_at_risk_skills(limit: int = Query(default=15, le=50)):
    """Skills with highest automation risk."""
    forecasts = _load_forecasts()
    items = [
        {
            "skill_id": sid,
            "name": sid.replace("_", " ").title(),
            "automation_risk": fc.get("automation_risk", 0.3),
            "growth_score": fc.get("growth_score", 0.5),
        }
        for sid, fc in forecasts.items()
    ]
    items.sort(key=lambda x: x["automation_risk"], reverse=True)
    return {"at_risk": items[:limit]}


# ── Resume Analysis ────────────────────────────────────────────────────────

@app.post(f"{settings.api_prefix}/resume/analyze")
def analyze_resume(req: ResumeRequest):
    """Privacy-preserving resume skill gap analysis."""
    from asie.resume import resume_analyzer

    # Build market demand from forecasts
    forecasts = _load_forecasts()
    market_demand = {
        sid: fc.get("growth_score", 0.5)
        for sid, fc in forecasts.items()
    }

    result = resume_analyzer.analyze(
        resume_text=req.resume_text,
        target_industry=req.target_industry,
        target_geo=req.target_geo,
        market_demand=market_demand,
    )
    return result.model_dump(mode="json")


# ── Alerts ─────────────────────────────────────────────────────────────────

@app.get(f"{settings.api_prefix}/alerts")
def get_alerts(
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=30, le=100),
):
    """Get active skill intelligence alerts."""
    alerts = _load_alerts()
    if alert_type:
        alerts = [a for a in alerts if a.get("alert_type") == alert_type]
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    return {"alerts": alerts[:limit], "total": len(alerts)}


@app.post(f"{settings.api_prefix}/disruption")
def trigger_disruption(req: DisruptionRequest):
    """Trigger a disruption event and see adjusted forecasts."""
    from asie.scoring import disruption_adjuster

    forecasts = _load_forecasts()
    adjusted = {}
    for sid in req.affected_skills:
        fc = forecasts.get(sid)
        if fc:
            adj = disruption_adjuster.apply_disruption(
                fc, req.disruption_type, req.magnitude, sid
            )
            adjusted[sid] = {
                "skill_id": sid,
                "original_growth": fc.get("growth_score", 0.5),
                "disruption_applied": adj.get("disruption_applied"),
            }
    return {
        "disruption_type": req.disruption_type,
        "magnitude": req.magnitude,
        "affected_skills": adjusted,
    }


# ── Knowledge Graph ────────────────────────────────────────────────────────

@app.get(f"{settings.api_prefix}/graph")
def get_full_graph():
    """Get the full skill knowledge graph."""
    return _load_graph()


@app.get(f"{settings.api_prefix}/graph/neighbors/{{skill_id}}")
def get_graph_neighbors(
    skill_id: str,
    depth: int = Query(default=1, le=3),
    relationship: Optional[str] = None,
):
    """Get knowledge graph neighbors for a skill."""
    from asie.graph import skill_graph
    neighbors = skill_graph.get_neighbors(skill_id, depth, relationship)
    return {"skill_id": skill_id, "neighbors": neighbors}


@app.get(f"{settings.api_prefix}/graph/learning-path")
def get_learning_path(
    from_skill: str = Query(...),
    to_skill: str = Query(...),
):
    """Find the learning path between two skills."""
    from asie.graph import skill_graph
    path = skill_graph.get_learning_path(from_skill, to_skill)
    return {"from": from_skill, "to": to_skill, "path": path}


# ── Filters ────────────────────────────────────────────────────────────────

@app.get(f"{settings.api_prefix}/filters/geo")
def filter_by_geo(
    geo: str = Query(..., description="Country code (US, EU, IN, UK, etc.)"),
    limit: int = Query(default=20, le=50),
):
    """Filter skills by geographic region."""
    # In production this would query geo-tagged signals
    # For prototype, return all skills with mock geo relevance
    forecasts = _load_forecasts()
    geo_weights = {
        "US": {"generative_ai": 1.2, "cloud_computing": 1.1, "cybersecurity": 1.15},
        "EU": {"cybersecurity": 1.2, "green_tech": 1.3, "data_engineering": 1.1},
        "IN": {"python": 1.15, "data_science": 1.2, "react": 1.1},
        "UK": {"fintech": 1.2, "cybersecurity": 1.15, "data_science": 1.1},
        "SG": {"cloud_computing": 1.15, "blockchain": 1.2, "fintech": 1.15},
    }
    weights = geo_weights.get(geo, {})
    items = []
    for sid, fc in forecasts.items():
        growth = fc.get("growth_score", 0.5) * weights.get(sid, 1.0)
        items.append({
            "skill_id": sid,
            "name": sid.replace("_", " ").title(),
            "growth_score": round(min(growth, 1.0), 4),
            "geo": geo,
        })
    items.sort(key=lambda x: x["growth_score"], reverse=True)
    return {"geo": geo, "skills": items[:limit]}


@app.get(f"{settings.api_prefix}/filters/industry")
def filter_by_industry(
    industry: str = Query(..., description="Industry name"),
    limit: int = Query(default=20, le=50),
):
    """Filter skills by industry."""
    from asie.graph import skill_graph
    industry_skills = skill_graph.get_skills_for_industry(industry)
    forecasts = _load_forecasts()
    items = []
    for sid in industry_skills:
        fc = forecasts.get(sid, {})
        items.append({
            "skill_id": sid,
            "name": sid.replace("_", " ").title(),
            "growth_score": fc.get("growth_score", 0.5),
            "automation_risk": fc.get("automation_risk", 0.3),
            "industry": industry,
        })
    items.sort(key=lambda x: x["growth_score"], reverse=True)
    return {"industry": industry, "skills": items[:limit]}


# ── Backtest ───────────────────────────────────────────────────────────────

@app.post(f"{settings.api_prefix}/backtest")
def run_backtest(req: BacktestRequest):
    """Run backtesting evaluation."""
    import pandas as pd
    from asie.backtesting import backtest_engine
    from asie.etl.pipeline import ETLPipeline
    from asie.taxonomy import SKILL_TAXONOMY

    pipeline = ETLPipeline()
    df = pipeline.run()

    skill_ids = req.skill_ids or [s.canonical for s in SKILL_TAXONOMY[:5]]
    skill_ts = {}
    for sid in skill_ids:
        ts = pipeline.get_skill_timeseries(df, sid)
        if not ts.empty:
            skill_ts[sid] = ts

    results = backtest_engine.run_all(skill_ts, req.n_splits)
    return {
        "results": [r.model_dump(mode="json") for r in results],
        "average_mape": round(
            sum(r.mape for r in results) / max(len(results), 1), 4
        ),
    }


# ── Dashboard Data ─────────────────────────────────────────────────────────

@app.get(f"{settings.api_prefix}/dashboard/summary")
def dashboard_summary():
    """Aggregated dashboard data."""
    forecasts = _load_forecasts()
    alerts = _load_alerts()

    all_growth = [fc.get("growth_score", 0.5) for fc in forecasts.values()]
    all_risk = [fc.get("automation_risk", 0.3) for fc in forecasts.values()]

    return {
        "total_skills_tracked": len(forecasts),
        "active_alerts": len(alerts),
        "avg_growth_score": round(sum(all_growth) / max(len(all_growth), 1), 4),
        "avg_automation_risk": round(sum(all_risk) / max(len(all_risk), 1), 4),
        "top_growing": sorted(
            [
                {"id": sid, "name": sid.replace("_", " ").title(), "growth": fc.get("growth_score", 0)}
                for sid, fc in forecasts.items()
            ],
            key=lambda x: x["growth"],
            reverse=True,
        )[:5],
        "highest_risk": sorted(
            [
                {"id": sid, "name": sid.replace("_", " ").title(), "risk": fc.get("automation_risk", 0)}
                for sid, fc in forecasts.items()
            ],
            key=lambda x: x["risk"],
            reverse=True,
        )[:5],
        "alert_breakdown": {
            t: len([a for a in alerts if a.get("alert_type") == t])
            for t in ["momentum_spike", "bubble_warning", "emerging_skill", "declining_skill", "disruption"]
        },
    }


# ── Mount static dashboard (if built) ─────────────────────────────────────

DASHBOARD_DIR = Path(__file__).resolve().parents[2] / "dashboard" / "dist"
if DASHBOARD_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")
