"""
Backtesting & Evaluation Framework.

Evaluates forecast accuracy by:
    1. Splitting historical data into train/test
    2. Training models on the train set
    3. Comparing predictions against actual test data
    4. Computing error metrics (MAPE, RMSE, MAE, directional accuracy)

Supports walk-forward validation for robust evaluation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger

from asie.forecasting.engine import EnsembleForecaster
from asie.models import BacktestResult


class BacktestEngine:
    """Walk-forward backtesting for skill forecasts."""

    def __init__(self, min_train_months: int = 24, test_months: int = 12) -> None:
        self.min_train_months = min_train_months
        self.test_months = test_months
        self.forecaster = EnsembleForecaster()

    def run(
        self,
        ts: pd.DataFrame,
        skill_id: str,
        n_splits: int = 3,
    ) -> BacktestResult:
        """
        Run walk-forward backtesting.

        Parameters
        ----------
        ts : skill time series with 'composite_signal' column
        skill_id : canonical skill identifier
        n_splits : number of walk-forward splits
        """
        n = len(ts)
        if n < self.min_train_months + self.test_months:
            logger.warning(f"Insufficient data for backtesting {skill_id} (n={n})")
            return BacktestResult(
                skill_name=skill_id,
                mape=99.9,
                rmse=1.0,
                mae=1.0,
                directional_accuracy=0.5,
                forecast_horizon=self.test_months,
                model_used="ensemble",
            )

        all_actuals: List[float] = []
        all_preds: List[float] = []

        # Walk-forward splits
        step_size = max(1, (n - self.min_train_months - self.test_months) // n_splits)
        for i in range(n_splits):
            train_end = self.min_train_months + i * step_size
            test_end = min(train_end + self.test_months, n)
            if train_end >= n or test_end <= train_end:
                continue

            train_df = ts.iloc[:train_end].copy()
            test_df = ts.iloc[train_end:test_end].copy()

            # Forecast
            try:
                forecast = self.forecaster.forecast(
                    train_df, skill_id, horizon_years=1
                )
                preds = forecast["predicted_demand"][:len(test_df)]
                actuals = test_df["composite_signal"].values[:len(preds)]

                all_actuals.extend(actuals.tolist())
                all_preds.extend(preds)
            except Exception as e:
                logger.error(f"Backtest split {i} failed for {skill_id}: {e}")
                continue

        if not all_actuals:
            return BacktestResult(
                skill_name=skill_id,
                mape=99.9,
                rmse=1.0,
                mae=1.0,
                directional_accuracy=0.5,
                forecast_horizon=self.test_months,
            )

        actuals_arr = np.array(all_actuals)
        preds_arr = np.array(all_preds)

        # Metrics
        mape = self._mape(actuals_arr, preds_arr)
        rmse = self._rmse(actuals_arr, preds_arr)
        mae = self._mae(actuals_arr, preds_arr)
        dir_acc = self._directional_accuracy(actuals_arr, preds_arr)

        return BacktestResult(
            skill_name=skill_id,
            mape=round(mape, 4),
            rmse=round(rmse, 4),
            mae=round(mae, 4),
            directional_accuracy=round(dir_acc, 4),
            forecast_horizon=self.test_months,
            model_used="ensemble",
        )

    def run_all(
        self,
        skill_timeseries: Dict[str, pd.DataFrame],
        n_splits: int = 3,
    ) -> List[BacktestResult]:
        """Run backtesting for all skills."""
        results: List[BacktestResult] = []
        for skill_id, ts in skill_timeseries.items():
            logger.info(f"Backtesting {skill_id}...")
            result = self.run(ts, skill_id, n_splits)
            results.append(result)
        results.sort(key=lambda r: r.mape)
        return results

    @staticmethod
    def _mape(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Mean Absolute Percentage Error."""
        mask = actual != 0
        if not mask.any():
            return 100.0
        return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)

    @staticmethod
    def _rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Root Mean Square Error."""
        return float(np.sqrt(np.mean((actual - predicted) ** 2)))

    @staticmethod
    def _mae(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Mean Absolute Error."""
        return float(np.mean(np.abs(actual - predicted)))

    @staticmethod
    def _directional_accuracy(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Percentage of correct direction predictions."""
        if len(actual) < 2:
            return 0.5
        actual_dir = np.diff(actual) > 0
        pred_dir = np.diff(predicted) > 0
        return float(np.mean(actual_dir == pred_dir))


# Module-level singleton
backtest_engine = BacktestEngine()
