"""
Alert & Disruption Detection System.

Detects and generates alerts for:
    - Momentum spikes (sudden demand acceleration)
    - Emerging new skills
    - Skill decline signals
    - Bubble warnings
    - Technology disruption events
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from asie.config import settings
from asie.models import Alert, AlertType, RiskLevel
from asie.scoring import bubble_detector, momentum_calculator


class AlertEngine:
    """Generate and manage skill intelligence alerts."""

    def __init__(self) -> None:
        self._alerts: List[Alert] = []
        self._momentum_history: Dict[str, List[float]] = {}

    def evaluate_skill(
        self,
        skill_id: str,
        ts: Any,  # pd.DataFrame
        forecast: Dict[str, Any],
    ) -> List[Alert]:
        """Evaluate a skill and generate any applicable alerts."""
        new_alerts: List[Alert] = []

        # 1. Momentum spike detection
        momentum = momentum_calculator.compute(ts)
        history = self._momentum_history.get(skill_id, [])
        self._momentum_history.setdefault(skill_id, []).append(momentum)

        if momentum_calculator.is_spike(momentum, history):
            alert = Alert(
                alert_type=AlertType.MOMENTUM_SPIKE,
                skill_name=skill_id,
                message=f"Significant momentum spike detected for '{skill_id.replace('_', ' ')}' "
                        f"(momentum index: {momentum:.3f}). "
                        f"Demand is accelerating rapidly across multiple signal sources.",
                severity=RiskLevel.HIGH if abs(momentum) > 0.6 else RiskLevel.MEDIUM,
                momentum_delta=momentum,
                metadata={"momentum_index": round(momentum, 4), "history_length": len(history)},
            )
            new_alerts.append(alert)

        # 2. Bubble warning
        bubble_score = bubble_detector.compute(ts, forecast)
        if bubble_score > settings.bubble_detection_threshold:
            alert = Alert(
                alert_type=AlertType.BUBBLE_WARNING,
                skill_name=skill_id,
                message=f"Potential skill bubble detected for '{skill_id.replace('_', ' ')}' "
                        f"(bubble score: {bubble_score:.3f}). "
                        f"Growth may be driven by hype rather than sustainable demand.",
                severity=RiskLevel.HIGH if bubble_score > 0.85 else RiskLevel.MEDIUM,
                metadata={"bubble_score": bubble_score},
            )
            new_alerts.append(alert)

        # 3. Emerging skill detection
        if self._is_emerging(skill_id, ts):
            alert = Alert(
                alert_type=AlertType.EMERGING_SKILL,
                skill_name=skill_id,
                message=f"'{skill_id.replace('_', ' ')}' is showing signs of rapid emergence. "
                        f"Consider early investment in this skill area.",
                severity=RiskLevel.MEDIUM,
                metadata={"growth_score": forecast.get("growth_score", 0)},
            )
            new_alerts.append(alert)

        # 4. Declining skill warning
        if self._is_declining(ts, forecast):
            alert = Alert(
                alert_type=AlertType.DECLINING_SKILL,
                skill_name=skill_id,
                message=f"Demand for '{skill_id.replace('_', ' ')}' shows sustained decline. "
                        f"Consider transitioning to related skills.",
                severity=RiskLevel.MEDIUM,
                metadata={"growth_score": forecast.get("growth_score", 0)},
            )
            new_alerts.append(alert)

        self._alerts.extend(new_alerts)
        return new_alerts

    def generate_disruption_alert(
        self,
        disruption_type: str,
        affected_skills: List[str],
        description: str,
        magnitude: float = 0.5,
    ) -> Alert:
        """Manually trigger a disruption alert."""
        alert = Alert(
            alert_type=AlertType.DISRUPTION,
            skill_name=", ".join(affected_skills[:5]),
            message=f"Disruption event: {description}. "
                    f"Affected skills: {', '.join(s.replace('_', ' ') for s in affected_skills[:10])}",
            severity=RiskLevel.CRITICAL if magnitude > 0.7 else RiskLevel.HIGH,
            metadata={
                "disruption_type": disruption_type,
                "magnitude": magnitude,
                "affected_skills": affected_skills,
            },
        )
        self._alerts.append(alert)
        return alert

    def get_active_alerts(
        self,
        alert_type: Optional[AlertType] = None,
        severity: Optional[RiskLevel] = None,
        limit: int = 50,
    ) -> List[Alert]:
        """Get active alerts with optional filtering."""
        filtered = self._alerts
        if alert_type:
            filtered = [a for a in filtered if a.alert_type == alert_type]
        if severity:
            filtered = [a for a in filtered if a.severity == severity]
        # Most recent first
        filtered.sort(key=lambda a: a.triggered_at, reverse=True)
        return filtered[:limit]

    @staticmethod
    def _is_emerging(skill_id: str, ts: Any) -> bool:
        """Detect if a skill is newly emerging."""
        if ts.empty or len(ts) < 12:
            return False
        composite = ts["composite_signal"].values
        # Emerging: low historical values but rapid recent growth
        historical_avg = np.mean(composite[:len(composite) // 2])
        recent_avg = np.mean(composite[-6:])
        if historical_avg < 0.2 and recent_avg > 0.4:
            return True
        # Strong acceleration
        growth_rate = (recent_avg - historical_avg) / max(historical_avg, 0.01)
        return growth_rate > 1.5

    @staticmethod
    def _is_declining(ts: Any, forecast: Dict[str, Any]) -> bool:
        """Detect sustained decline in skill demand.
        
        Requires multiple confirming signals to avoid false positives:
        - Low growth score (forecast predicts decline)
        - Negative momentum (currently decelerating)
        - Recent time-series below historical average
        At least 2 of 3 conditions must be true, and growth must be < 0.25.
        """
        growth_score = forecast.get("growth_score", 0.5)
        momentum = forecast.get("momentum_index", 0.0)

        # growth_score 0.5 = no growth, below 0.20 = severe decline only
        low_growth = growth_score < 0.20
        negative_momentum = momentum < -0.10

        # If growth is reasonable (>= 0.30), definitely not declining
        if growth_score >= 0.30:
            return False

        # Time-series check
        ts_declining = False
        if not (ts.empty or len(ts) < 12):
            composite = ts["composite_signal"].values
            prior_avg = np.mean(composite[:-6])
            recent_avg = np.mean(composite[-6:])
            ts_declining = recent_avg < prior_avg * 0.60  # 40% drop required

        # Need ALL three signals to confirm genuine decline
        return low_growth and negative_momentum and ts_declining


# Module-level singleton
alert_engine = AlertEngine()
