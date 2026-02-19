# `tests/` — Test Suite

> Comprehensive pytest test suite covering all ASIE modules.

## Overview

The test suite validates the entire ASIE pipeline — ETL ingestion, NLP extraction, forecasting engine, scoring algorithms, taxonomy/graph, and REST API endpoints. Tests use synthetic data and can run without external dependencies.

## Files

| File | Tests | What It Validates |
|---|---|---|
| `test_etl.py` | 4 tests | ETL pipeline execution, multi-source ingestion, skill time-series generation, value normalisation |
| `test_nlp.py` | 6 tests | Skill extraction (exact, alias, fuzzy), confidence scoring, resume proficiency estimation, false positive prevention |
| `test_forecasting.py` | 5 tests | Prophet fallback, XGBoost fit/predict, ETS fallback, ensemble forecast (growth/confidence/volatility), model contribution weights |
| `test_scoring.py` | 8 tests | Momentum calculation, spike detection, bubble scoring, automation risk (soft vs hard skills), reliability scoring, disruption adjustments |
| `test_taxonomy_graph.py` | 12 tests | Taxonomy resolution (canonical + alias), fuzzy matching, domain filtering, graph construction, neighbor queries, prerequisites, complementary skills, industry mapping, centrality, serialization |
| `test_api.py` | 9 tests | All REST endpoints — skills, trending, emerging, at-risk, alerts, resume analysis, dashboard summary, error handling (404) |

## Running Tests

```bash
cd ASIE

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_forecasting.py -v

# Run with coverage
pytest tests/ -v --cov=asie --cov-report=term-missing

# Run only NLP tests
pytest tests/test_nlp.py -v
```

> **Note:** `test_api.py` requires seed data to be present (`python -m asie.seed`). Tests will skip gracefully with `pytest.skip()` if data is missing (HTTP 503).

## Test Details

### `test_etl.py` — ETL Pipeline

| Test | Validates |
|---|---|
| `test_run_pipeline` | Pipeline produces non-empty DataFrame with required columns (`skill_id`, `source`, `value`, `timestamp`) |
| `test_multiple_sources` | At least 4 data sources are present in the output |
| `test_get_skill_timeseries` | Per-skill time-series has `composite_signal` and `month` columns |
| `test_values_normalised` | All signal values are in [0, 1] range |

### `test_nlp.py` — NLP Skill Extraction

| Test | Validates |
|---|---|
| `test_extract_basic_skills` | Extracts "python", "machine_learning", "aws" from plain text |
| `test_extract_aliases` | Maps aliases: "ML" → machine_learning, "k8s" → kubernetes, "NLP" → natural_language_processing |
| `test_extract_empty_text` | Returns empty list for blank/whitespace input |
| `test_extract_with_confidence` | Confidence scores are in [0, 1] range |
| `test_extract_from_resume` | Expert-level skills get higher proficiency than basic-level |
| `test_no_false_positives` | Non-skill text produces zero matches |

### `test_forecasting.py` — Forecasting Engine

| Test | Validates |
|---|---|
| `test_fallback` (Prophet) | Falls back to linear regression with < 12 data points |
| `test_fit_predict` (XGBoost) | Produces 24-month predictions from 48-month training data |
| `test_ets_fallback` (LSTM/ETS) | ETS model produces predictions from 36-month data |
| `test_forecast` (Ensemble) | Output has all required keys; growth/confidence scores in [0, 1] |
| `test_model_contributions` | Ensemble weights sum to 1.0 |

### `test_scoring.py` — Scoring Algorithms

| Test | Validates |
|---|---|
| `test_positive_momentum` | Upward trend → positive momentum |
| `test_flat_momentum` | Flat trend → near-zero momentum |
| `test_spike_detection` | High momentum detected as spike; normal values not |
| `test_low_bubble_for_stable` | Stable growth → low bubble score in [0, 1] |
| `test_soft_skill_lower_risk` | "leadership" has lower automation risk than "sql" |
| `test_unknown_skill` | Unknown skill returns default risk (0.3) |
| `test_high_data_reliability` | 60 months + high confidence → reliability > 0.5 |
| `test_ai_breakthrough_boosts_ai_skills` | Disruption adjustment increases AI skill demand |

### `test_taxonomy_graph.py` — Taxonomy & Knowledge Graph

| Test | Validates |
|---|---|
| `test_resolve_canonical` | "python" resolves to "python" |
| `test_resolve_alias` | "ML" → "machine_learning", "k8s" → "kubernetes" |
| `test_resolve_unknown` | Unknown skills return None |
| `test_fuzzy_match` | "machin learning" → "machine_learning" |
| `test_all_skills_nonempty` | Taxonomy has > 30 skills |
| `test_graph_built` | Graph has nodes and edges after build |
| `test_get_neighbors` | machine_learning has at least 1 neighbor |
| `test_get_prerequisites` | prompt_engineering requires generative_ai |
| `test_get_complementary` | mlops has complementary skills |
| `test_get_skills_for_industry` | "technology" maps to > 5 skills |
| `test_centrality` | PageRank values are positive |
| `test_to_serializable` | Export has nodes + edges arrays |

### `test_api.py` — REST API Endpoints

| Test | Validates |
|---|---|
| `test_root` | `GET /` returns 200 with "ASIE" in name |
| `test_list_skills` | `GET /api/v1/skills` returns skills array |
| `test_trending` | `GET /api/v1/skills/trending` returns 200 |
| `test_emerging` | `GET /api/v1/skills/emerging` returns 200 |
| `test_at_risk` | `GET /api/v1/skills/at-risk` returns 200 |
| `test_alerts` | `GET /api/v1/alerts` returns 200 |
| `test_resume_analyze` | `POST /api/v1/resume/analyze` returns extracted_skills + skill_gaps |
| `test_skill_not_found` | Unknown skill returns 404 |
| `test_dashboard_summary` | `GET /api/v1/dashboard/summary` returns total_skills_tracked |

## Fixtures

- **`test_api.py`** uses `TestClient` from FastAPI (module-scoped)
- **`test_forecasting.py`** and **`test_scoring.py`** use a shared `_make_ts()` helper that generates a synthetic 48-month time-series with trend, per-source signals, and random noise (seed=42 for reproducibility)
