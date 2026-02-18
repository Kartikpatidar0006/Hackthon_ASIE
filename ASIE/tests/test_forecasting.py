"""Tests for the Forecasting Engine."""
import pytest
import numpy as np
import pandas as pd
from asie.forecasting.engine import EnsembleForecaster, ProphetModel, XGBoostModel, LSTMModel


def _make_ts(n=48):
    months = pd.date_range("2020-01", periods=n, freq="MS")
    np.random.seed(42)
    values = 0.3 + 0.01 * np.arange(n) + np.random.normal(0, 0.02, n)
    return pd.DataFrame({
        "month": months,
        "composite_signal": values,
        "signal_jobs": values * 1.1,
        "signal_patents": values * 0.8,
        "signal_research": values * 0.9,
        "signal_startups": values * 0.7,
        "signal_policy": values * 0.3,
    })


class TestProphetModel:
    def test_fallback(self):
        model = ProphetModel()
        ts = _make_ts(n=6)  # too few for Prophet
        result = model.fit_predict(ts, 12)
        assert "predicted" in result
        assert len(result["predicted"]) == 12


class TestXGBoostModel:
    def test_fit_predict(self):
        model = XGBoostModel()
        ts = _make_ts(n=48)
        result = model.fit_predict(ts, 24)
        assert "predicted" in result
        assert len(result["predicted"]) == 24


class TestLSTMModel:
    def test_ets_fallback(self):
        model = LSTMModel()
        ts = _make_ts(n=36)
        result = model.fit_predict(ts, 12)
        assert "predicted" in result


class TestEnsembleForecaster:
    def test_forecast(self):
        forecaster = EnsembleForecaster()
        ts = _make_ts(n=48)
        result = forecaster.forecast(ts, "python", horizon_years=3)
        assert "predicted_demand" in result
        assert "growth_score" in result
        assert "confidence_score" in result
        assert "volatility_score" in result
        assert 0 <= result["growth_score"] <= 1
        assert 0 <= result["confidence_score"] <= 1

    def test_model_contributions(self):
        forecaster = EnsembleForecaster()
        ts = _make_ts(n=48)
        result = forecaster.forecast(ts, "python")
        contribs = result["model_contributions"]
        assert abs(sum(contribs.values()) - 1.0) < 0.01
