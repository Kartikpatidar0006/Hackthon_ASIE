"""Tests for the Scoring Module."""
import pytest
import numpy as np
import pandas as pd
from asie.scoring import (
    SkillMomentumCalculator,
    BubbleDetector,
    AutomationRiskCalculator,
    ForecastReliabilityScorer,
    DisruptionAdjuster,
)


def _make_ts(n=48, trend=0.01):
    """Create a synthetic time series DataFrame."""
    months = pd.date_range("2020-01", periods=n, freq="MS")
    base = 0.3
    values = [base + trend * i + np.random.normal(0, 0.02) for i in range(n)]
    return pd.DataFrame({
        "month": months,
        "composite_signal": values,
        "signal_jobs": [v * 1.1 for v in values],
        "signal_patents": [v * 0.8 for v in values],
        "signal_research": [v * 0.9 for v in values],
        "signal_startups": [v * 0.7 for v in values],
        "signal_policy": [v * 0.3 for v in values],
    })


class TestMomentum:
    def test_positive_momentum(self):
        ts = _make_ts(trend=0.02)  # upward trend
        calc = SkillMomentumCalculator()
        momentum = calc.compute(ts)
        assert momentum > 0

    def test_flat_momentum(self):
        ts = _make_ts(trend=0.0)
        calc = SkillMomentumCalculator()
        momentum = calc.compute(ts)
        assert abs(momentum) < 0.5

    def test_spike_detection(self):
        calc = SkillMomentumCalculator()
        history = [0.1, 0.2, 0.15, 0.1, 0.18, 0.12]
        assert calc.is_spike(5.0, history) is True
        assert calc.is_spike(0.1, history) is False


class TestBubbleDetector:
    def test_low_bubble_for_stable(self):
        ts = _make_ts(trend=0.005)
        detector = BubbleDetector()
        score = detector.compute(ts, {"growth_score": 0.5})
        assert 0 <= score <= 1

    def test_empty_ts(self):
        detector = BubbleDetector()
        score = detector.compute(pd.DataFrame(), {})
        assert score == 0.0


class TestAutomationRisk:
    def test_soft_skill_lower_risk(self):
        calc = AutomationRiskCalculator()
        ts = _make_ts()
        risk_leadership = calc.compute("leadership", ts)
        risk_sql = calc.compute("sql", ts)
        assert risk_leadership < risk_sql

    def test_unknown_skill(self):
        calc = AutomationRiskCalculator()
        risk = calc.compute("unknown_skill", _make_ts())
        assert risk == 0.3  # default


class TestReliability:
    def test_high_data_reliability(self):
        scorer = ForecastReliabilityScorer()
        ts = _make_ts(n=60)
        fc = {"confidence_score": 0.8}
        score = scorer.compute(fc, ts)
        assert score > 0.5

    def test_low_data_reliability(self):
        scorer = ForecastReliabilityScorer()
        ts = _make_ts(n=6)
        fc = {"confidence_score": 0.3}
        score = scorer.compute(fc, ts)
        assert score < 0.6


class TestDisruption:
    def test_ai_breakthrough_boosts_ai_skills(self):
        adjuster = DisruptionAdjuster()
        fc = {"predicted_demand": [0.5, 0.6, 0.7]}
        adjusted = adjuster.apply_disruption(fc, "ai_breakthrough", 0.5, "machine_learning")
        # AI skills should be boosted
        assert adjusted["predicted_demand"][0] >= fc["predicted_demand"][0]
