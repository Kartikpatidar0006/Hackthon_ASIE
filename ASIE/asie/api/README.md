# `asie/api/` — FastAPI REST Layer

> Serves the ASIE intelligence as a RESTful API with 15+ endpoints.

## Overview

This sub-package contains the FastAPI application that exposes all ASIE capabilities — skill listings, forecasts, trending/emerging analysis, resume gap analysis, alerts, knowledge graph queries, backtesting, and dashboard data aggregation.

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Package marker |
| `main.py` | FastAPI app definition, all route handlers, CORS setup, static file serving |

## Quick Start

```bash
# Generate data first (one-time)
python -m asie.seed

# Start the API server
uvicorn asie.api.main:app --reload --port 8000

# Open interactive docs
# http://localhost:8000/docs
```

## API Endpoints

### Skills

| Method | Endpoint | Description | Query Params |
|---|---|---|---|
| `GET` | `/api/v1/skills` | List all skills with current scores | `category`, `domain`, `limit` (max 200) |
| `GET` | `/api/v1/skills/{skill_id}/forecast` | Detailed 5-year forecast for a skill | — |
| `GET` | `/api/v1/skills/trending` | Top skills by momentum index | `limit` (max 50) |
| `GET` | `/api/v1/skills/emerging` | Skills showing rapid emergence | `limit` (max 30) |
| `GET` | `/api/v1/skills/at-risk` | Skills with highest automation risk | `limit` (max 50) |

### Resume Analysis

| Method | Endpoint | Description | Body |
|---|---|---|---|
| `POST` | `/api/v1/resume/analyze` | Privacy-preserving skill gap analysis | `{ resume_text, target_industry?, target_geo?, target_role? }` |

### Alerts

| Method | Endpoint | Description | Query Params |
|---|---|---|---|
| `GET` | `/api/v1/alerts` | Active intelligence alerts | `alert_type`, `severity`, `limit` |

### Knowledge Graph

| Method | Endpoint | Description | Query Params |
|---|---|---|---|
| `GET` | `/api/v1/graph` | Full graph (nodes + edges) | — |
| `GET` | `/api/v1/graph/neighbors/{skill_id}` | Neighboring nodes | `depth`, `relationship` |
| `GET` | `/api/v1/graph/learning-path` | Shortest skill-acquisition path | `from_skill`, `to_skill` |

### Filters

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/filters/geo?geo={geo}` | Geo-filtered skill scores |
| `GET` | `/api/v1/filters/industry?industry={ind}` | Industry-filtered skill scores |

### Job Roles

| Method | Endpoint | Description | Query Params |
|---|---|---|---|
| `GET` | `/api/v1/roles` | List all job role profiles | `industry` |

### Backtesting

| Method | Endpoint | Description | Body |
|---|---|---|---|
| `POST` | `/api/v1/backtest` | Run walk-forward backtesting | `{ skill_ids?, n_splits? }` |

### Disruption Simulation

| Method | Endpoint | Description | Body |
|---|---|---|---|
| `POST` | `/api/v1/disruption/simulate` | Simulate what-if disruption scenarios | `{ disruption_type, affected_skills, description, magnitude? }` |

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/dashboard/summary` | Aggregated KPIs, top growing, highest risk, alert breakdown |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check / version info |

## Data Loading

The API reads pre-computed data from `data/` directory:
- `forecasts.json` — All skill forecasts with scores
- `alerts.json` — Generated alerts
- `graph.json` — Knowledge graph nodes and edges

If data files are missing, endpoints return HTTP 503 with a message to run `python -m asie.seed`.

## CORS

All origins are allowed (`allow_origins=["*"]`) for development. Restrict in production.

## Static Dashboard

If `dashboard/dist/` exists (after `npm run build`), it is mounted at `/app` for serving the built React dashboard.

## Response Examples

### `GET /api/v1/skills/{skill_id}/forecast`
```json
{
  "skill_id": "generative_ai",
  "name": "Generative Ai",
  "category": "technical",
  "domain": "ai_ml",
  "forecast": {
    "horizon_months": 60,
    "predicted_demand": [0.45, 0.47, ...],
    "prediction_intervals": [{"lower": 0.38, "upper": 0.52}, ...],
    "growth_score": 0.82,
    "confidence_score": 0.76,
    "volatility_score": 0.18,
    "momentum_index": 1.24,
    "bubble_score": 0.35,
    "automation_risk": 0.08,
    "reliability_score": 0.71
  },
  "explanations": {
    "feature_impacts": {"Job Market Signal": 0.32, ...},
    "top_drivers": ["Job Market Signal", "Research Publication Signal"],
    "narrative": "The forecasted growth is primarily driven by..."
  }
}
```
