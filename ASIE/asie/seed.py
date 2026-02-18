"""
Seed Module – generates synthetic data and pre-computes forecasts.

Run via:  python -m asie.seed
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

# Fix random seeds for reproducibility
random.seed(42)
np.random.seed(42)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def run_seed() -> None:
    logger.info("═" * 60)
    logger.info("  ASIE Data Seed – Generating Synthetic Dataset")
    logger.info("═" * 60)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Run ETL pipeline
    logger.info("[1/5] Running ETL pipeline...")
    from asie.etl.pipeline import ETLPipeline
    pipeline = ETLPipeline()
    df = pipeline.run()
    df.to_parquet(DATA_DIR / "signals.parquet", index=False)
    logger.info(f"  → Saved {len(df)} signals to data/signals.parquet")

    # 2. Build skill time-series
    logger.info("[2/5] Building skill time-series...")
    from asie.taxonomy import SKILL_TAXONOMY
    skill_ts = {}
    for sk in SKILL_TAXONOMY:
        ts = pipeline.get_skill_timeseries(df, sk.canonical)
        if not ts.empty:
            skill_ts[sk.canonical] = ts
    logger.info(f"  → Built time-series for {len(skill_ts)} skills")

    # 3. Run forecasts
    logger.info("[3/5] Running ensemble forecasts...")
    from asie.forecasting.engine import EnsembleForecaster
    from asie.scoring import (
        automation_risk_calculator,
        bubble_detector,
        momentum_calculator,
        reliability_scorer,
    )
    from asie.explainability import shap_explainer
    from asie.alerts import alert_engine

    forecaster = EnsembleForecaster()
    forecasts = {}
    alerts_list = []

    for skill_id, ts in skill_ts.items():
        try:
            fc = forecaster.forecast(ts, skill_id, horizon_years=5)

            # Compute additional metrics
            momentum = momentum_calculator.compute(ts)
            bubble = bubble_detector.compute(ts, fc)
            auto_risk = automation_risk_calculator.compute(skill_id, ts)
            reliability = reliability_scorer.compute(fc, ts)
            explanations = shap_explainer.explain_forecast(fc)

            fc["momentum_index"] = momentum
            fc["bubble_score"] = bubble
            fc["automation_risk"] = auto_risk
            fc["reliability_score"] = reliability
            fc["explanations"] = explanations

            forecasts[skill_id] = fc

            # Generate alerts
            skill_alerts = alert_engine.evaluate_skill(skill_id, ts, fc)
            alerts_list.extend([a.model_dump(mode="json") for a in skill_alerts])

        except Exception as e:
            logger.error(f"  ✗ Forecast failed for {skill_id}: {e}")

    logger.info(f"  → Generated forecasts for {len(forecasts)} skills")

    # 4. Save forecasts
    logger.info("[4/5] Saving forecasts and alerts...")

    # Convert forecasts to serializable format
    serializable_forecasts = {}
    for skill_id, fc in forecasts.items():
        sfc = {}
        for k, v in fc.items():
            if isinstance(v, (np.integer,)):
                sfc[k] = int(v)
            elif isinstance(v, (np.floating,)):
                sfc[k] = float(v)
            elif isinstance(v, np.ndarray):
                sfc[k] = v.tolist()
            elif isinstance(v, dict):
                sfc[k] = {
                    str(dk): (float(dv) if isinstance(dv, (np.floating, np.integer)) else dv)
                    for dk, dv in v.items()
                }
            else:
                sfc[k] = v
        serializable_forecasts[skill_id] = sfc

    with open(DATA_DIR / "forecasts.json", "w") as f:
        json.dump(serializable_forecasts, f, indent=2, default=str)
    with open(DATA_DIR / "alerts.json", "w") as f:
        json.dump(alerts_list, f, indent=2, default=str)
    logger.info(f"  → Saved {len(alerts_list)} alerts")

    # 5. Build knowledge graph
    logger.info("[5/5] Building knowledge graph...")
    from asie.graph import skill_graph
    skill_graph.build()
    graph_data = skill_graph.to_serializable()
    with open(DATA_DIR / "graph.json", "w") as f:
        json.dump(graph_data, f, indent=2, default=str)
    logger.info(
        f"  → Graph: {len(graph_data['nodes'])} nodes, "
        f"{len(graph_data['edges'])} edges"
    )

    logger.info("═" * 60)
    logger.info("  Seed complete! Data saved to ./data/")
    logger.info("═" * 60)


if __name__ == "__main__":
    run_seed()
