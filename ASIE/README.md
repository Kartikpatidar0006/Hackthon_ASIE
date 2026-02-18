# Adaptive Skill Intelligence Engine (ASIE)

> Predict high-demand skills for the next 3–5 years using multi-source signals.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    ASIE – System Architecture                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Job Boards  │  │  Patents    │  │ Research │  │ Startups │  │
│  │  (APIs)     │  │  (USPTO)   │  │ (ArXiv)  │  │ (Crunch) │  │
│  └──────┬──────┘  └──────┬──────┘  └────┬─────┘  └────┬─────┘  │
│         └────────────────┼──────────────┼──────────────┘        │
│                          ▼                                       │
│              ┌───────────────────────┐                           │
│              │   ETL Pipeline        │                           │
│              │  (Ingestion+Clean)    │                           │
│              └──────────┬────────────┘                           │
│                         ▼                                        │
│              ┌───────────────────────┐                           │
│              │  NLP Skill Extractor  │                           │
│              │  (spaCy + Taxonomy)   │                           │
│              └──────────┬────────────┘                           │
│                         ▼                                        │
│   ┌──────────────────────────────────────────────┐               │
│   │          Knowledge Graph (NetworkX)          │               │
│   │   Skills ↔ Domains ↔ Technologies ↔ Roles   │               │
│   └──────────────────┬───────────────────────────┘               │
│                      ▼                                           │
│   ┌──────────────────────────────────────────────┐               │
│   │        Ensemble Forecasting Engine           │               │
│   │  ┌──────────┬───────────┬────────────┐       │               │
│   │  │ Prophet  │  XGBoost  │   LSTM     │       │               │
│   │  └──────────┴───────────┴────────────┘       │               │
│   │         + SHAP Explainability                 │               │
│   └──────────────────┬───────────────────────────┘               │
│                      ▼                                           │
│   ┌──────────────────────────────────────────────┐               │
│   │           Scoring & Analytics                │               │
│   │  Growth · Confidence · Volatility · Momentum │               │
│   │  Bubble Detection · Automation Risk          │               │
│   └──────────────────┬───────────────────────────┘               │
│                      ▼                                           │
│   ┌──────────────────────────────────────────────┐               │
│   │          FastAPI REST Layer                   │               │
│   │  /forecast  /gaps  /alerts  /graph  /trends  │               │
│   └──────────────────┬───────────────────────────┘               │
│                      ▼                                           │
│   ┌──────────────────────────────────────────────┐               │
│   │       React Dashboard (Recharts)             │               │
│   │  Trend Lines · Heatmaps · Skill Radar       │               │
│   └──────────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Backend
cd ASIE
pip install -r requirements.txt
python -m asie.seed          # Generate synthetic data
uvicorn asie.api.main:app --reload

# Frontend
cd dashboard
npm install && npm run dev
```

## Key Features

- **Multi-Source Ingestion**: Jobs, patents, research, startups, policy signals
- **NLP Skill Extraction**: spaCy-based extraction with canonical taxonomy mapping
- **Knowledge Graph**: Skill relationship graph with domain/technology linkage
- **Ensemble Forecasting**: Prophet + XGBoost + optional LSTM with SHAP explainability
- **Skill Metrics**: Growth, confidence, volatility, momentum index, bubble score
- **Resume Gap Analysis**: Privacy-preserving skill gap identification
- **Disruption Detection**: Momentum spike and technology disruption alerts
- **Automation Risk**: Per-skill automation susceptibility scoring
- **Backtesting**: Historical evaluation framework with MAPE/RMSE metrics
- **Interactive Dashboard**: Real-time trend visualizations with filtering

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/skills` | GET | List all skills with current scores |
| `/api/v1/skills/{id}/forecast` | GET | 3-5 year forecast for a skill |
| `/api/v1/skills/trending` | GET | Top trending skills by momentum |
| `/api/v1/skills/emerging` | GET | Newly emerging skills |
| `/api/v1/resume/analyze` | POST | Resume-based skill gap analysis |
| `/api/v1/alerts` | GET | Active disruption & momentum alerts |
| `/api/v1/graph/neighbors/{skill}` | GET | Knowledge graph neighbors |
| `/api/v1/filters/geo` | GET | Geo-based skill filtering |
| `/api/v1/filters/industry` | GET | Industry-based skill filtering |
| `/api/v1/backtest` | POST | Run backtesting evaluation |

## License

MIT
