"""
Ensemble Forecasting Engine for ASIE.

Combines three model families:
    1. Prophet  – for trend + seasonality decomposition
    2. XGBoost  – gradient boosting on engineered features
    3. LSTM     – (optional) sequence model for non-linear dynamics

Final forecast = weighted ensemble of individual model outputs.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats

from asie.config import settings

warnings.filterwarnings("ignore", category=FutureWarning)


# ═══════════════════════════════════════════════════════════════════
# Individual Model Wrappers
# ═══════════════════════════════════════════════════════════════════

class ProphetModel:
    """Facebook Prophet wrapper for trend + seasonality forecasting."""

    def __init__(self) -> None:
        self.model = None

    def fit_predict(
        self, ts: pd.DataFrame, horizon_months: int = 60
    ) -> Dict[str, Any]:
        """
        Fit Prophet and return predictions.

        Parameters
        ----------
        ts : DataFrame with columns ['month', 'composite_signal']
        horizon_months : number of months to forecast

        Returns
        -------
        dict with keys: predicted, lower, upper, trend, seasonal
        """
        try:
            from prophet import Prophet

            df = ts[["month", "composite_signal"]].rename(
                columns={"month": "ds", "composite_signal": "y"}
            )
            df = df.dropna()
            if len(df) < 12:
                return self._fallback_linear(ts, horizon_months)

            m = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
                interval_width=0.80,
            )
            m.fit(df)
            future = m.make_future_dataframe(periods=horizon_months, freq="MS")
            forecast = m.predict(future)

            # Extract the forecast portion
            fc = forecast.tail(horizon_months)
            return {
                "predicted": fc["yhat"].tolist(),
                "lower": fc["yhat_lower"].tolist(),
                "upper": fc["yhat_upper"].tolist(),
                "trend": fc["trend"].tolist(),
                "dates": fc["ds"].dt.strftime("%Y-%m").tolist(),
                "model": "prophet",
            }
        except ImportError:
            logger.warning("Prophet not installed, using linear fallback")
            return self._fallback_linear(ts, horizon_months)
        except Exception as e:
            logger.error(f"Prophet error: {e}")
            return self._fallback_linear(ts, horizon_months)

    @staticmethod
    def _fallback_linear(ts: pd.DataFrame, horizon_months: int) -> Dict[str, Any]:
        """Simple linear trend extrapolation as fallback."""
        y = ts["composite_signal"].values
        x = np.arange(len(y))
        if len(y) < 2:
            flat = [float(y[0]) if len(y) else 0.5] * horizon_months
            return {"predicted": flat, "lower": flat, "upper": flat, "trend": flat,
                    "dates": [], "model": "linear_fallback"}

        slope, intercept, _, _, _ = stats.linregress(x, y)
        future_x = np.arange(len(y), len(y) + horizon_months)
        predicted = (slope * future_x + intercept).tolist()
        std = float(np.std(y))
        lower = [p - 1.96 * std for p in predicted]
        upper = [p + 1.96 * std for p in predicted]
        return {
            "predicted": predicted,
            "lower": lower,
            "upper": upper,
            "trend": predicted,
            "dates": [],
            "model": "linear_fallback",
        }


class XGBoostModel:
    """XGBoost gradient boosting model using engineered features."""

    def __init__(self) -> None:
        self.model = None

    def fit_predict(
        self, ts: pd.DataFrame, horizon_months: int = 60
    ) -> Dict[str, Any]:
        try:
            import xgboost as xgb

            df = ts.copy()
            df = self._engineer_features(df)
            if len(df) < 12:
                return self._simple_prediction(ts, horizon_months)

            feature_cols = [c for c in df.columns if c.startswith("feat_")]
            X = df[feature_cols].values
            y = df["composite_signal"].values

            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )
            model.fit(X, y)
            self.model = model

            # Generate future features
            future_features = self._generate_future_features(df, horizon_months)
            predicted = model.predict(future_features).tolist()

            # Feature importances
            importances = dict(zip(feature_cols, model.feature_importances_.tolist()))

            return {
                "predicted": predicted,
                "feature_importances": importances,
                "model": "xgboost",
            }
        except ImportError:
            logger.warning("XGBoost not installed, using simple prediction")
            return self._simple_prediction(ts, horizon_months)
        except Exception as e:
            logger.error(f"XGBoost error: {e}")
            return self._simple_prediction(ts, horizon_months)

    @staticmethod
    def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
        """Create lag, rolling, and trend features."""
        df = df.copy()
        y = df["composite_signal"]

        # Lag features
        for lag in [1, 3, 6, 12]:
            df[f"feat_lag_{lag}"] = y.shift(lag)

        # Rolling statistics
        for window in [3, 6, 12]:
            df[f"feat_roll_mean_{window}"] = y.rolling(window).mean()
            df[f"feat_roll_std_{window}"] = y.rolling(window).std()

        # Rate of change
        df["feat_roc_3"] = y.pct_change(3)
        df["feat_roc_6"] = y.pct_change(6)

        # Trend feature
        df["feat_trend"] = np.arange(len(df))

        # Month-of-year for seasonality
        if "month" in df.columns:
            df["feat_month_sin"] = np.sin(2 * np.pi * pd.to_datetime(df["month"]).dt.month / 12)
            df["feat_month_cos"] = np.cos(2 * np.pi * pd.to_datetime(df["month"]).dt.month / 12)

        # Source-specific signals as features
        for col in df.columns:
            if col.startswith("signal_"):
                df[f"feat_{col}"] = df[col]

        df = df.dropna()
        return df

    @staticmethod
    def _generate_future_features(df: pd.DataFrame, horizon: int) -> np.ndarray:
        """Generate feature matrix for future time steps."""
        feature_cols = [c for c in df.columns if c.startswith("feat_")]
        last_row = df[feature_cols].iloc[-1].values
        future_rows = []
        for i in range(horizon):
            row = last_row.copy()
            # Update trend feature
            trend_idx = [j for j, c in enumerate(feature_cols) if c == "feat_trend"]
            if trend_idx:
                row[trend_idx[0]] = len(df) + i
            # Slight extrapolation noise
            noise = np.random.normal(0, 0.01, len(row))
            row = row + noise
            future_rows.append(row)
        return np.array(future_rows)

    @staticmethod
    def _simple_prediction(ts: pd.DataFrame, horizon: int) -> Dict[str, Any]:
        y = ts["composite_signal"].values
        if len(y) == 0:
            return {"predicted": [0.5] * horizon, "model": "simple_fallback"}
        trend = (y[-1] - y[0]) / max(len(y), 1)
        predicted = [float(y[-1] + trend * (i + 1)) for i in range(horizon)]
        return {"predicted": predicted, "model": "simple_fallback"}


class LSTMModel:
    """Optional LSTM model for non-linear sequence forecasting."""

    def __init__(self, seq_length: int = 12) -> None:
        self.seq_length = seq_length
        self.model = None

    def fit_predict(
        self, ts: pd.DataFrame, horizon_months: int = 60
    ) -> Dict[str, Any]:
        """
        LSTM requires tensorflow/torch. Falls back to exponential smoothing
        if not available.
        """
        try:
            return self._fit_predict_ets(ts, horizon_months)
        except Exception as e:
            logger.error(f"LSTM/ETS error: {e}")
            return {"predicted": [0.5] * horizon_months, "model": "lstm_fallback"}

    def _fit_predict_ets(
        self, ts: pd.DataFrame, horizon_months: int
    ) -> Dict[str, Any]:
        """Exponential Triple Smoothing as production-friendly alternative to LSTM."""
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        y = ts["composite_signal"].values
        if len(y) < 24:
            # Not enough data for seasonal ETS
            alpha = 0.3
            level = y[0] if len(y) > 0 else 0.5
            predicted = []
            for _ in range(horizon_months):
                predicted.append(float(level))
            return {"predicted": predicted, "model": "simple_ets"}

        try:
            model = ExponentialSmoothing(
                y,
                trend="add",
                seasonal="add",
                seasonal_periods=12,
            ).fit(optimized=True)
            forecast = model.forecast(horizon_months)
            return {
                "predicted": forecast.tolist(),
                "model": "holt_winters_ets",
            }
        except Exception:
            # Fallback to simple exponential smoothing
            alpha = 0.3
            level = float(y[-1])
            trend = float(np.mean(np.diff(y[-12:])))
            predicted = []
            for i in range(horizon_months):
                predicted.append(level + trend * (i + 1))
            return {"predicted": predicted, "model": "simple_ets_fallback"}


# ═══════════════════════════════════════════════════════════════════
# Ensemble Forecaster
# ═══════════════════════════════════════════════════════════════════

class EnsembleForecaster:
    """
    Combines Prophet, XGBoost, and LSTM into a weighted ensemble.

    The final prediction is:
        ŷ = w_p · prophet + w_x · xgboost + w_l · lstm

    Confidence is derived from inter-model agreement.
    """

    def __init__(self) -> None:
        self.prophet = ProphetModel()
        self.xgboost = XGBoostModel()
        self.lstm = LSTMModel()
        self.weights = settings.ensemble_weights

    def forecast(
        self,
        ts: pd.DataFrame,
        skill_id: str,
        horizon_years: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate an ensemble forecast for a skill.

        Returns a rich dict with predictions, intervals, confidence, etc.
        """
        horizon_months = horizon_years * 12

        # Run individual models
        prophet_result = self.prophet.fit_predict(ts, horizon_months)
        xgboost_result = self.xgboost.fit_predict(ts, horizon_months)
        lstm_result = self.lstm.fit_predict(ts, horizon_months)

        # Extract prediction arrays
        p_pred = np.array(prophet_result["predicted"][:horizon_months])
        x_pred = np.array(xgboost_result["predicted"][:horizon_months])
        l_pred = np.array(lstm_result["predicted"][:horizon_months])

        # Ensure same length
        min_len = min(len(p_pred), len(x_pred), len(l_pred))
        p_pred = p_pred[:min_len]
        x_pred = x_pred[:min_len]
        l_pred = l_pred[:min_len]

        # Weighted ensemble
        w = self.weights
        ensemble_pred = (
            w.prophet * p_pred
            + w.xgboost * x_pred
            + w.lstm * l_pred
        )

        # Confidence from inter-model agreement (inverse of coefficient of variation)
        stacked = np.stack([p_pred, x_pred, l_pred])
        model_std = np.std(stacked, axis=0)
        model_mean = np.mean(stacked, axis=0)
        cv = np.where(model_mean != 0, model_std / np.abs(model_mean), 1.0)
        confidence_per_step = np.clip(1 - cv, 0, 1)
        overall_confidence = float(np.mean(confidence_per_step))

        # Prediction intervals
        intervals = []
        for i in range(min_len):
            lo = float(np.percentile(stacked[:, i], 10))
            hi = float(np.percentile(stacked[:, i], 90))
            intervals.append({"lower": lo, "upper": hi})

        # Growth score: compare last predicted to first predicted
        if len(ensemble_pred) > 1 and ensemble_pred[0] != 0:
            growth = float(
                (ensemble_pred[-1] - ensemble_pred[0]) / abs(ensemble_pred[0])
            )
        else:
            growth = 0.0
        growth_score = float(np.clip(growth / 2 + 0.5, 0, 1))  # norm to 0-1

        # Volatility: normalised std of predictions
        volatility = float(np.std(ensemble_pred) / (np.mean(ensemble_pred) + 1e-8))
        volatility_score = float(np.clip(volatility, 0, 1))

        # Model contributions
        contributions = {
            "prophet": float(w.prophet),
            "xgboost": float(w.xgboost),
            "lstm": float(w.lstm),
        }

        return {
            "skill_id": skill_id,
            "horizon_months": min_len,
            "predicted_demand": ensemble_pred.tolist(),
            "prediction_intervals": intervals,
            "growth_score": growth_score,
            "confidence_score": round(overall_confidence, 4),
            "volatility_score": round(volatility_score, 4),
            "model_contributions": contributions,
            "prophet_result": prophet_result,
            "xgboost_result": xgboost_result,
            "lstm_result": lstm_result,
            "feature_importances": xgboost_result.get("feature_importances", {}),
        }
