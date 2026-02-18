"""ASIE – centralised configuration loaded from .env / environment."""

from __future__ import annotations
import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_FILE)


def _float(key: str, default: float = 0.0) -> float:
    return float(os.getenv(key, str(default)))


def _int(key: str, default: int = 0) -> int:
    return int(os.getenv(key, str(default)))


def _bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")


class EnsembleWeights(BaseModel):
    prophet: float = Field(default_factory=lambda: _float("ENSEMBLE_WEIGHTS_PROPHET", 0.4))
    xgboost: float = Field(default_factory=lambda: _float("ENSEMBLE_WEIGHTS_XGBOOST", 0.4))
    lstm: float = Field(default_factory=lambda: _float("ENSEMBLE_WEIGHTS_LSTM", 0.2))


class Settings(BaseModel):
    app_name: str = "ASIE"
    app_version: str = "1.0.0"
    debug: bool = Field(default_factory=lambda: _bool("DEBUG", False))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    api_host: str = Field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = Field(default_factory=lambda: _int("API_PORT", 8000))
    api_prefix: str = Field(default_factory=lambda: os.getenv("API_PREFIX", "/api/v1"))

    forecast_horizon_years: int = Field(default_factory=lambda: _int("FORECAST_HORIZON_YEARS", 5))
    confidence_threshold: float = Field(default_factory=lambda: _float("CONFIDENCE_THRESHOLD", 0.6))

    ensemble_weights: EnsembleWeights = Field(default_factory=EnsembleWeights)

    hash_salt: str = Field(default_factory=lambda: os.getenv("HASH_SALT", "change_me"))
    anonymize_resumes: bool = Field(default_factory=lambda: _bool("ANONYMIZE_RESUMES", True))

    momentum_spike_threshold: float = Field(default_factory=lambda: _float("MOMENTUM_SPIKE_THRESHOLD", 2.0))
    bubble_detection_threshold: float = Field(default_factory=lambda: _float("BUBBLE_DETECTION_THRESHOLD", 0.75))


settings = Settings()
