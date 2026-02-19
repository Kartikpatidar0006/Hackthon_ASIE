"""
Skill Metrics & Scoring Module.

Computes:
    - Skill Momentum Index (multi-signal weighted score)
    - Bubble Detection Score (hype vs sustainable growth)
    - Automation Risk Index per skill
    - Confidence-based Forecast Reliability Score
    - Disruption-triggered Forecasting adjustments
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger

from asie.config import settings
from asie.taxonomy import taxonomy_index


class SkillMomentumCalculator:
    """
    Skill Momentum Index = weighted combination of short-term and long-term
    growth rates across multiple signal sources.

    momentum = w1 * Δjobs_3m + w2 * Δpatents_6m + w3 * Δresearch_6m
             + w4 * Δstartups_3m + w5 * Δpolicy_12m

    A momentum > 2.0σ triggers a momentum-spike alert.
    """

    SOURCE_WEIGHTS = {
        "signal_jobs": 0.35,
        "signal_patents": 0.20,
        "signal_research": 0.20,
        "signal_startups": 0.15,
        "signal_policy": 0.10,
    }

    SHORT_WINDOW = 3   # months
    LONG_WINDOW = 12   # months

    def compute(self, ts: pd.DataFrame) -> float:
        """Compute momentum index for a skill time-series."""
        if ts.empty or len(ts) < self.LONG_WINDOW:
            return 0.0

        momentum = 0.0
        for col, weight in self.SOURCE_WEIGHTS.items():
            if col not in ts.columns:
                continue
            values = ts[col].values
            if len(values) < self.LONG_WINDOW:
                continue

            # Short-term rate of change
            short_recent = np.mean(values[-self.SHORT_WINDOW:])
            short_prev = np.mean(values[-2 * self.SHORT_WINDOW: -self.SHORT_WINDOW])
            short_roc = (short_recent - short_prev) / max(abs(short_prev), 0.01)
            short_roc = np.clip(short_roc, -2.0, 2.0)  # cap individual ROC

            # Long-term rate of change
            long_recent = np.mean(values[-self.LONG_WINDOW:])
            long_prev = np.mean(values[: self.LONG_WINDOW])
            long_roc = (long_recent - long_prev) / max(abs(long_prev), 0.01)
            long_roc = np.clip(long_roc, -2.0, 2.0)  # cap individual ROC

            # Combined with short-term weighted more
            signal_momentum = 0.6 * short_roc + 0.4 * long_roc
            momentum += weight * signal_momentum

        # Final momentum clipped to [-1, 1] range
        momentum = float(np.clip(momentum, -1.0, 1.0))
        return round(momentum, 4)

    def is_spike(self, momentum: float, history: List[float]) -> bool:
        """Detect if current momentum is a statistically significant spike.
        
        With momentum clipped to [-1, 1], use absolute thresholds:
        - |momentum| > 0.5 is a notable spike
        - Z-score check against history as secondary confirmation
        """
        if len(history) < 6:
            return abs(momentum) > 0.5
        mean_m = np.mean(history)
        std_m = np.std(history) + 1e-8
        z_score = (momentum - mean_m) / std_m
        return abs(momentum) > 0.5 or z_score > 2.0


class BubbleDetector:
    """
    Detects hype-driven skill bubbles vs. sustainable growth.

    Bubble Score = f(growth_acceleration, mention_vs_adoption_gap,
                      funding_without_revenue, citation_growth_divergence)

    Score > 0.75 → likely bubble / hype cycle
    Score < 0.30 → sustainable growth
    """

    def compute(self, ts: pd.DataFrame, forecast_result: Dict[str, Any]) -> float:
        """Compute bubble score (0-1, higher = more bubble-like)."""
        if ts.empty or len(ts) < 12:
            return 0.0

        signals = []

        # 1. Growth acceleration vs. deceleration
        composite = ts["composite_signal"].values
        if len(composite) >= 12:
            first_half = composite[: len(composite) // 2]
            second_half = composite[len(composite) // 2:]
            growth_first = (first_half[-1] - first_half[0]) / (abs(first_half[0]) + 1e-8)
            growth_second = (second_half[-1] - second_half[0]) / (abs(second_half[0]) + 1e-8)
            acceleration = growth_second - growth_first
            signals.append(np.clip(acceleration / 2, 0, 1))

        # 2. Volatility as bubble indicator
        volatility = float(np.std(composite) / (np.mean(composite) + 1e-8))
        signals.append(np.clip(volatility, 0, 1))

        # 3. Mention-adoption gap (high mentions but low sustained adoption)
        if "signal_jobs" in ts.columns and "signal_research" in ts.columns:
            jobs = ts["signal_jobs"].values
            research = ts["signal_research"].values
            if len(jobs) > 0 and len(research) > 0:
                gap = np.mean(research[-6:]) - np.mean(jobs[-6:])
                signals.append(np.clip(gap, 0, 1))

        # 4. Funding spike without proportional demand growth
        if "signal_startups" in ts.columns and "signal_jobs" in ts.columns:
            funding = ts["signal_startups"].values
            demand = ts["signal_jobs"].values
            if len(funding) > 6 and len(demand) > 6:
                funding_growth = (np.mean(funding[-3:]) - np.mean(funding[:3])) / (np.mean(funding[:3]) + 1e-8)
                demand_growth = (np.mean(demand[-3:]) - np.mean(demand[:3])) / (np.mean(demand[:3]) + 1e-8)
                divergence = max(0, funding_growth - demand_growth)
                signals.append(np.clip(divergence / 2, 0, 1))

        if not signals:
            return 0.0

        bubble_score = float(np.mean(signals))
        return round(np.clip(bubble_score, 0, 1), 4)


class AutomationRiskCalculator:
    """
    Compute per-skill automation risk index.

    Factors:
        - Base automation susceptibility from taxonomy
        - Routine-ness score (higher for well-defined, repetitive tasks)
        - AI/ML capability growth in the skill's domain
        - Historical automation replacement patterns
    """

    # Skills where AI/ML growth *increases* automation risk
    AI_AMPLIFIED = {
        "sql", "data_visualization", "project_management", "react",
        "nodejs", "flutter", "react_native", "docker",
    }

    # Skills inherently resistant to automation
    RESISTANT = {
        "leadership", "communication", "problem_solving",
        "cybersecurity", "quantum_computing", "robotics",
    }

    def compute(
        self,
        skill_id: str,
        ts: pd.DataFrame,
        ai_growth_rate: float = 0.0,
    ) -> float:
        """Compute automation risk (0-1, higher = more at risk)."""
        sk_info = taxonomy_index.get(skill_id)
        if not sk_info:
            return 0.3  # default moderate risk

        base_risk = sk_info.automation_risk_base

        # Adjustment for AI/ML capability growth
        if skill_id in self.AI_AMPLIFIED:
            base_risk = min(base_risk + 0.15 * ai_growth_rate, 0.9)
        elif skill_id in self.RESISTANT:
            base_risk = max(base_risk - 0.1, 0.05)

        # Soft skills are generally less automatable
        if sk_info.category == "soft":
            base_risk *= 0.5

        # Highly specialised / emerging skills have lower risk
        if sk_info.domain in ("quantum", "emerging"):
            base_risk *= 0.6

        # Time-based adjustment: if demand is rising fast, risk is lower
        # (market still heavily needs humans)
        if not ts.empty and len(ts) >= 6:
            recent_growth = (
                np.mean(ts["composite_signal"].values[-3:])
                - np.mean(ts["composite_signal"].values[:3])
            )
            if recent_growth > 0.1:
                base_risk *= 0.85

        return round(float(np.clip(base_risk, 0, 1)), 4)


class ForecastReliabilityScorer:
    """
    Confidence-based forecast reliability score.

    Combines:
        - Model agreement (inter-model variance)
        - Data sufficiency (number of training points)
        - Historical accuracy (backtest results if available)
        - Signal coverage (how many sources contribute data)
    """

    def compute(
        self,
        forecast_result: Dict[str, Any],
        ts: pd.DataFrame,
        backtest_mape: Optional[float] = None,
    ) -> float:
        """Compute reliability score (0-1, higher = more reliable)."""
        scores = []

        # 1. Model agreement (from ensemble confidence)
        conf = forecast_result.get("confidence_score", 0.5)
        scores.append(conf)

        # 2. Data sufficiency
        n_points = len(ts)
        data_score = min(n_points / 48, 1.0)  # 48 months = ideal
        scores.append(data_score)

        # 3. Historical accuracy
        if backtest_mape is not None:
            accuracy_score = max(0, 1 - backtest_mape / 100)
            scores.append(accuracy_score)

        # 4. Signal coverage (how many source columns have data)
        source_cols = [c for c in ts.columns if c.startswith("signal_")]
        active_sources = sum(1 for c in source_cols if ts[c].sum() > 0)
        coverage_score = active_sources / max(len(source_cols), 1)
        scores.append(coverage_score)

        reliability = float(np.mean(scores))
        return round(np.clip(reliability, 0, 1), 4)


class DisruptionAdjuster:
    """
    Adjust forecasts when disruption events are detected.

    Disruption types:
        - AI breakthrough (boosts AI-related skills, threatens routine skills)
        - Policy change (regulatory impacts on specific domains)
        - Economic shock (broad dampening or amplification)
        - Technology paradigm shift
    """

    def apply_disruption(
        self,
        forecast: Dict[str, Any],
        disruption_type: str,
        magnitude: float = 0.3,
        skill_id: str = "",
    ) -> Dict[str, Any]:
        """Apply disruption adjustment to forecasted values."""
        adjusted = forecast.copy()
        preds = np.array(forecast["predicted_demand"])

        sk_info = taxonomy_index.get(skill_id)
        domain = sk_info.domain if sk_info else "general"

        if disruption_type == "ai_breakthrough":
            # Boost AI/ML, threaten routine skills
            if domain in ("ai_ml", "data"):
                multiplier = 1 + magnitude
            elif domain in ("programming", "web"):
                multiplier = 1 - magnitude * 0.3  # slight negative
            else:
                multiplier = 1.0
            preds = preds * multiplier

        elif disruption_type == "policy_change":
            if domain in ("security", "web3", "ai_ml"):
                # Could be positive (regulation = more compliance jobs)
                # or negative (ban = skill destruction)
                preds = preds * (1 + magnitude * 0.5)
            else:
                preds = preds * (1 + magnitude * 0.1)

        elif disruption_type == "economic_shock":
            # Broad dampening
            preds = preds * (1 - magnitude * 0.4)

        elif disruption_type == "paradigm_shift":
            if domain in ("emerging", "quantum", "web3"):
                preds = preds * (1 + magnitude * 0.8)
            else:
                preds = preds * (1 - magnitude * 0.2)

        adjusted["predicted_demand"] = preds.tolist()
        adjusted["disruption_applied"] = {
            "type": disruption_type,
            "magnitude": magnitude,
        }
        return adjusted


# Module-level singletons
momentum_calculator = SkillMomentumCalculator()
bubble_detector = BubbleDetector()
automation_risk_calculator = AutomationRiskCalculator()
reliability_scorer = ForecastReliabilityScorer()
disruption_adjuster = DisruptionAdjuster()
