# `asie/` — Core Intelligence Engine

> The main Python package powering the Adaptive Skill Intelligence Engine.

## Overview

This package contains all backend logic: data ingestion, NLP extraction, ML forecasting, scoring, knowledge graph, resume analysis, alerting, and the REST API. It is structured as a modular Python package runnable via `python -m asie.seed`.

## Module Map

| Module | Purpose | Key Classes / Functions |
|---|---|---|
| `__init__.py` | Package marker, exposes `__version__` | — |
| `__main__.py` | Entry point for `python -m asie.seed` | Calls `run_seed()` |
| `config.py` | Centralised configuration via `.env` / environment variables | `Settings`, `EnsembleWeights` |
| `models.py` | Pydantic data models used across the system | `Skill`, `SkillSignal`, `SkillForecast`, `Alert`, `BacktestResult`, `ResumeAnalysis`, `SkillGap`, `RoleFitResult` |
| `taxonomy.py` | Canonical skill registry (70+ skills), job role profiles (20+ roles), relationship ontology, fuzzy matching | `SKILL_TAXONOMY`, `JOB_ROLE_PROFILES`, `taxonomy_index` |
| `seed.py` | Data generation & pre-computation orchestrator | `run_seed()` |
| `scoring.py` | Multi-dimensional skill scoring algorithms | `SkillMomentumCalculator`, `BubbleDetector`, `AutomationRiskCalculator`, `ForecastReliabilityScorer`, `DisruptionAdjuster` |
| `explainability.py` | SHAP-style forecast explanations | `SHAPExplainer` |
| `alerts.py` | Disruption & momentum alert engine | `AlertEngine` |
| `graph.py` | NetworkX-backed knowledge graph | `SkillKnowledgeGraph` |
| `resume.py` | Privacy-preserving resume gap analysis | `ResumeAnalyzer`, `PrivacyGuard` |
| `backtesting.py` | Walk-forward forecast evaluation framework | `BacktestEngine` |

## Sub-packages

| Sub-package | Description |
|---|---|
| [`api/`](api/README.md) | FastAPI REST layer (15+ endpoints) |
| [`etl/`](etl/README.md) | Multi-source ETL pipeline (5 data connectors) |
| [`forecasting/`](forecasting/README.md) | Ensemble forecasting engine (Prophet + XGBoost + ETS) |
| [`nlp/`](nlp/README.md) | NLP-based skill extraction from unstructured text |

## Configuration (`config.py`)

All settings are loaded from environment variables or a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `API_HOST` | `0.0.0.0` | API bind host |
| `API_PORT` | `8000` | API bind port |
| `API_PREFIX` | `/api/v1` | API route prefix |
| `FORECAST_HORIZON_YEARS` | `5` | Default forecast horizon |
| `CONFIDENCE_THRESHOLD` | `0.6` | Minimum confidence for reliable forecasts |
| `ENSEMBLE_WEIGHTS_PROPHET` | `0.4` | Prophet model weight in ensemble |
| `ENSEMBLE_WEIGHTS_XGBOOST` | `0.4` | XGBoost model weight in ensemble |
| `ENSEMBLE_WEIGHTS_LSTM` | `0.2` | ETS/LSTM model weight in ensemble |
| `HASH_SALT` | `change_me` | Salt for PII hashing in resume analysis |
| `ANONYMIZE_RESUMES` | `true` | Strip PII from resumes before processing |
| `MOMENTUM_SPIKE_THRESHOLD` | `2.0` | Z-score threshold for momentum spike alerts |
| `BUBBLE_DETECTION_THRESHOLD` | `0.75` | Score threshold for bubble warnings |

## Data Models (`models.py`)

### Enums
- **`DataSource`** — `jobs`, `patents`, `research`, `startups`, `policy`, `social`
- **`SkillCategory`** — `technical`, `soft`, `domain`, `tool`, `methodology`, `certification`
- **`RiskLevel`** — `low`, `medium`, `high`, `critical`
- **`AlertType`** — `momentum_spike`, `disruption`, `bubble_warning`, `emerging_skill`, `declining_skill`
- **`Industry`** — `technology`, `finance`, `healthcare`, `manufacturing`, `energy`, `education`, `retail`, `government`

### Core Models
- **`Skill`** — Canonical skill entity with aliases and metadata
- **`SkillSignal`** — Single data point from any source (normalised 0–1)
- **`SkillForecast`** — Forecast output with 7 scoring dimensions
- **`SkillGap`** — Gap between user skills and market demand
- **`RoleFitResult`** — How well a candidate fits a specific job role
- **`ResumeAnalysis`** — Full resume analysis output
- **`Alert`** — Skill intelligence alert
- **`BacktestResult`** — Backtesting evaluation metrics (MAPE, RMSE, MAE, directional accuracy)

## Taxonomy (`taxonomy.py`)

- **70+ canonical skills** organized across 15 domains (AI/ML, Cloud, Security, Data, Web, etc.)
- **200+ aliases** for fuzzy matching (e.g., "ML" → `machine_learning`, "k8s" → `kubernetes`)
- **20+ job role profiles** across 8 industries with weighted skill requirements
- **Skill relationship ontology** — prerequisite, complementary, specialization edges
- **`taxonomy_index`** — singleton providing `resolve()`, `fuzzy_match()`, `skills_by_domain()`, `all_skills()`

## Scoring (`scoring.py`)

Seven scoring dimensions computed per skill:

| Score | Class | Algorithm |
|---|---|---|
| **Growth Score** | `EnsembleForecaster` | Normalized ratio of last vs first predicted demand |
| **Confidence Score** | `EnsembleForecaster` | Inverse coefficient of variation across 3 models |
| **Volatility Score** | `EnsembleForecaster` | Normalized std of predicted demand |
| **Momentum Index** | `SkillMomentumCalculator` | Weighted short+long-term ROC across 5 signal sources |
| **Bubble Score** | `BubbleDetector` | Mean of growth acceleration, volatility, mention-adoption gap, funding-demand divergence |
| **Automation Risk** | `AutomationRiskCalculator` | Base risk × domain/category adjustments × demand growth |
| **Reliability Score** | `ForecastReliabilityScorer` | Mean of model agreement, data sufficiency, signal coverage |

## Seed Process (`seed.py`)

Running `python -m asie.seed` executes:

1. **ETL Pipeline** → generates synthetic signals from 5 sources → saves `data/signals.parquet`
2. **Time-series construction** → per-skill monthly composite signals
3. **Ensemble forecasts** → Prophet + XGBoost + ETS for each skill + scoring + SHAP explanations
4. **Alert generation** → momentum spikes, bubble warnings, emerging/declining detections
5. **Knowledge graph** → builds NetworkX graph from taxonomy → saves `data/graph.json`

Output: `data/forecasts.json`, `data/alerts.json`, `data/graph.json`
