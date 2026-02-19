# `asie/etl/` — Multi-Source ETL Pipeline

> Ingests, cleans, and normalises signals from 5 data sources into a unified skill time-series.

## Overview

The ETL (Extract–Transform–Load) pipeline orchestrates data ingestion from multiple real-world signal sources. In the prototype, each connector generates realistic **synthetic data**; in production, they would connect to real APIs (LinkedIn Jobs, USPTO, ArXiv, Crunchbase, government feeds).

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Package marker |
| `pipeline.py` | All source connectors + pipeline orchestrator |

## Architecture

```
┌───────────────────────────────────────────────────┐
│               ETLPipeline.run()                   │
│                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ JobPostings │  │ PatentFiling │  │ Research │ │
│  │ Connector   │  │ Connector    │  │ Pubs     │ │
│  └──────┬──────┘  └──────┬───────┘  └────┬─────┘ │
│         │                │               │        │
│  ┌──────┴──────┐  ┌──────┴───────┐              │
│  │ Startup     │  │ Policy       │              │
│  │ Funding     │  │ Signals      │              │
│  └──────┬──────┘  └──────┬───────┘              │
│         └────────────────┼──────────────┘        │
│                          ▼                        │
│              Unified DataFrame                    │
│         (skill_id, source, value, timestamp)      │
└───────────────────────────────────────────────────┘
```

## Source Connectors

Each connector extends the abstract `SourceConnector` class with `fetch_raw()` and `transform()` methods:

| Connector | Source | Data Generated | Time Span | Granularity |
|---|---|---|---|---|
| `JobPostingsConnector` | Job postings (LinkedIn, Indeed) | Posting counts, salary, geo, industry | 5 years | Monthly |
| `PatentFilingsConnector` | Patent filings (USPTO) | Filing counts, top assignees | 5 years | Quarterly |
| `ResearchPubsConnector` | Research papers (ArXiv, Semantic Scholar) | Publication counts, citation counts | 5 years | Quarterly |
| `StartupFundingConnector` | Startup funding (Crunchbase) | Funding amounts ($M), deal counts | 5 years | Quarterly |
| `PolicySignalsConnector` | Government policy (regulation feeds) | Policy mentions, regulatory sentiment | 5 years | Quarterly |

## Signal Normalisation

All raw counts are normalised to **0–1 range** per source using max-scaling:
```
normalised_value = raw_count / max_count_in_source
```

Each signal is wrapped in a `SkillSignal` Pydantic model with:
- `skill_id` — canonical skill identifier
- `source` — data source enum
- `timestamp` — observation date
- `value` — normalised signal (0–1)
- `raw_count` — original count
- `geo`, `industry`, `metadata` — optional context

## Composite Time-Series

`ETLPipeline.get_skill_timeseries()` aggregates signals across sources into a single monthly time-series:

```python
# Weighted average across sources
source_weights = {
    "jobs":      0.35,   # Strongest demand signal
    "patents":   0.20,   # Innovation signal
    "research":  0.20,   # Discovery signal
    "startups":  0.15,   # Funding signal
    "policy":    0.10,   # Regulatory signal
}

composite_signal = Σ (source_value × weight)
```

Output columns: `month`, `composite_signal`, `signal_jobs`, `signal_patents`, `signal_research`, `signal_startups`, `signal_policy`

## Usage

```python
from asie.etl.pipeline import ETLPipeline

pipeline = ETLPipeline()
df = pipeline.run()                                    # Full signal DataFrame
ts = pipeline.get_skill_timeseries(df, "python")       # Per-skill time-series

print(df.shape)        # (~50,000+ rows)
print(ts.columns)      # month, composite_signal, signal_jobs, ...
```

## Production Roadmap

| Prototype (Current) | Production (Future) |
|---|---|
| Synthetic data generation | Real API integrations |
| In-memory processing | Apache Airflow / Prefect DAGs |
| Single-run pipeline | Scheduled incremental ingestion |
| File-based output | PostgreSQL + Redis cache |
| Max-scaling normalisation | Statistical z-score normalisation |
