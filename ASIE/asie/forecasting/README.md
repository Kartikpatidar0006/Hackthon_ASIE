# `asie/forecasting/` — Ensemble Forecasting Engine

> Predicts skill demand 3–5 years ahead using a weighted ensemble of 3 ML models.

## Overview

The forecasting engine combines three complementary model families into a single ensemble prediction. Each model captures different aspects of the time-series signal, and their weighted combination produces more robust forecasts than any individual model.

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Package marker |
| `engine.py` | All model wrappers + ensemble forecaster |

## Model Architecture

```
Input: Monthly skill time-series (composite_signal + per-source signals)
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌───────────┐   ┌──────────────┐
    │ Prophet  │   │  XGBoost  │   │ Holt-Winters │
    │  (40%)   │   │   (40%)   │   │  ETS (20%)   │
    └────┬─────┘   └─────┬─────┘   └──────┬───────┘
         └───────────────┼────────────────┘
                         ▼
              Weighted Ensemble Prediction
              + Confidence from inter-model agreement
              + Prediction intervals (10th–90th percentile)
```

## Individual Models

### 1. Prophet (`ProphetModel`)
- **Purpose:** Trend decomposition + seasonality capture
- **Library:** Facebook Prophet
- **Config:** Yearly seasonality, changepoint prior = 0.05, 80% intervals
- **Fallback:** Linear regression extrapolation (if Prophet unavailable or < 12 data points)

### 2. XGBoost (`XGBoostModel`)
- **Purpose:** Non-linear gradient boosting on engineered features
- **Library:** XGBoost
- **Config:** 100 estimators, max depth 4, learning rate 0.1, subsample 0.8
- **Engineered Features:**
  - Lag features: 1, 3, 6, 12 months
  - Rolling statistics: mean and std for 3, 6, 12-month windows
  - Rate of change: 3-month and 6-month
  - Trend (linear index)
  - Seasonal encoding: sin/cos month-of-year
  - Per-source signal values (`signal_jobs`, `signal_patents`, etc.)
- **Output:** Predictions + feature importances (used for SHAP explanations)
- **Fallback:** Simple trend extrapolation

### 3. Holt-Winters ETS (`LSTMModel`)
- **Purpose:** Exponential smoothing for non-linear seasonal patterns
- **Library:** statsmodels `ExponentialSmoothing`
- **Config:** Additive trend + additive seasonality (period = 12 months)
- **Note:** Named `LSTMModel` in code — acts as the LSTM slot but uses ETS as a production-friendly alternative. Easily swappable with a real LSTM/Transformer model.
- **Fallback:** Simple exponential smoothing (if < 24 data points)

## Ensemble Logic

### Weighting
```python
weights = {"prophet": 0.4, "xgboost": 0.4, "lstm": 0.2}
ensemble = w_prophet * prophet_pred + w_xgboost * xgb_pred + w_lstm * ets_pred
```

Weights are configurable via environment variables:
- `ENSEMBLE_WEIGHTS_PROPHET` (default: 0.4)
- `ENSEMBLE_WEIGHTS_XGBOOST` (default: 0.4)
- `ENSEMBLE_WEIGHTS_LSTM` (default: 0.2)

### Confidence Score
Derived from **inter-model agreement** — how much the 3 models agree:

```
CV = std(models) / |mean(models)|    # Coefficient of Variation per timestep
confidence = mean(1 - CV)             # Clamped to [0, 1]
```

High confidence (> 0.8) = all three models predict similar values.
Low confidence (< 0.4) = models disagree significantly.

### Prediction Intervals
Computed as 10th and 90th percentile across the 3 model outputs at each timestep.

### Growth Score
```
growth = (last_predicted - first_predicted) / |first_predicted|
growth_score = clip(growth / 2 + 0.5, 0, 1)
```

### Volatility Score
```
volatility = std(ensemble_predictions) / mean(ensemble_predictions)
volatility_score = clip(volatility, 0, 1)
```

## Usage

```python
from asie.forecasting.engine import EnsembleForecaster

forecaster = EnsembleForecaster()
result = forecaster.forecast(time_series_df, "generative_ai", horizon_years=5)

print(result["growth_score"])        # 0.82
print(result["confidence_score"])    # 0.76
print(result["predicted_demand"])    # [0.45, 0.47, ...]  (60 monthly values)
print(result["prediction_intervals"])# [{"lower": 0.38, "upper": 0.52}, ...]
print(result["model_contributions"]) # {"prophet": 0.4, "xgboost": 0.4, "lstm": 0.2}
```

## Output Schema

| Key | Type | Description |
|---|---|---|
| `skill_id` | `str` | Canonical skill name |
| `horizon_months` | `int` | Number of months forecasted |
| `predicted_demand` | `List[float]` | Monthly demand predictions |
| `prediction_intervals` | `List[{lower, upper}]` | Per-month confidence bounds |
| `growth_score` | `float` | Normalised growth (0–1) |
| `confidence_score` | `float` | Inter-model agreement (0–1) |
| `volatility_score` | `float` | Prediction volatility (0–1) |
| `model_contributions` | `Dict[str, float]` | Ensemble weights used |
| `prophet_result` | `Dict` | Raw Prophet output |
| `xgboost_result` | `Dict` | Raw XGBoost output + feature importances |
| `lstm_result` | `Dict` | Raw ETS output |
| `feature_importances` | `Dict[str, float]` | XGBoost feature importance scores |
