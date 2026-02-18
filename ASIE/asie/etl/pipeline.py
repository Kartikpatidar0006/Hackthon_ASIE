"""
Multi-source ETL Pipeline for ASIE.

Handles ingestion, cleaning, normalisation and storage of signals from:
    - Job postings
    - Patent filings
    - Research publications
    - Startup funding activity
    - Policy / regulation signals

In production these would call real APIs; here we provide a clean abstraction
with simulated data for the prototype.
"""

from __future__ import annotations

import hashlib
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger

from asie.models import DataSource, Industry, SkillSignal
from asie.taxonomy import SKILL_TAXONOMY, taxonomy_index


# ── Abstract Source Connector ──────────────────────────────────────────────

class SourceConnector(ABC):
    """Base class for all data-source connectors."""

    source: DataSource

    @abstractmethod
    def fetch_raw(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch raw records from the source."""
        ...

    @abstractmethod
    def transform(self, raw_records: List[Dict[str, Any]]) -> List[SkillSignal]:
        """Clean & normalise raw records into SkillSignal objects."""
        ...

    def ingest(self, since: Optional[datetime] = None) -> List[SkillSignal]:
        raw = self.fetch_raw(since)
        logger.info(f"[{self.source.value}] fetched {len(raw)} raw records")
        signals = self.transform(raw)
        logger.info(f"[{self.source.value}] produced {len(signals)} signals")
        return signals


# ── Concrete Connectors (simulated for prototype) ─────────────────────────

class JobPostingsConnector(SourceConnector):
    source = DataSource.JOBS

    def fetch_raw(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Simulate job posting API results."""
        records: List[Dict[str, Any]] = []
        geos = ["US", "EU", "IN", "UK", "CA", "SG", "AU"]
        industries = list(Industry)
        base_date = since or datetime(2020, 1, 1)
        for sk in SKILL_TAXONOMY:
            # Generate monthly data points
            for month_offset in range(60):  # 5 years
                dt = base_date + timedelta(days=30 * month_offset)
                if dt > datetime.utcnow():
                    break
                base_demand = random.uniform(50, 500)
                # Add growth trend
                trend = 1 + (month_offset / 60) * random.uniform(0.2, 1.5)
                # Seasonality
                seasonal = 1 + 0.1 * np.sin(2 * np.pi * month_offset / 12)
                count = int(base_demand * trend * seasonal + random.gauss(0, 20))
                count = max(0, count)
                records.append({
                    "skill": sk.canonical,
                    "date": dt.isoformat(),
                    "posting_count": count,
                    "geo": random.choice(geos),
                    "industry": random.choice(industries).value,
                    "avg_salary": random.randint(60000, 200000),
                })
        return records

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[SkillSignal]:
        if not raw_records:
            return []
        max_count = max(r["posting_count"] for r in raw_records) or 1
        signals = []
        for r in raw_records:
            canonical = taxonomy_index.resolve(r["skill"])
            if not canonical:
                continue
            sk_info = taxonomy_index.get(canonical)
            signals.append(SkillSignal(
                skill_id=canonical,
                source=DataSource.JOBS,
                timestamp=datetime.fromisoformat(r["date"]),
                value=r["posting_count"] / max_count,
                raw_count=r["posting_count"],
                geo=r["geo"],
                industry=Industry(r["industry"]),
                metadata={"avg_salary": r["avg_salary"], "category": sk_info.category if sk_info else ""},
            ))
        return signals


class PatentFilingsConnector(SourceConnector):
    source = DataSource.PATENTS

    def fetch_raw(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        tech_skills = [s for s in SKILL_TAXONOMY if s.category == "technical"]
        base_date = since or datetime(2020, 1, 1)
        for sk in tech_skills:
            for q in range(20):  # quarterly, 5 years
                dt = base_date + timedelta(days=90 * q)
                if dt > datetime.utcnow():
                    break
                filings = int(random.uniform(5, 80) * (1 + q / 20 * random.uniform(0.3, 1.2)))
                records.append({
                    "skill": sk.canonical,
                    "date": dt.isoformat(),
                    "filing_count": max(0, filings),
                    "top_assignees": random.randint(1, 10),
                })
        return records

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[SkillSignal]:
        if not raw_records:
            return []
        max_count = max(r["filing_count"] for r in raw_records) or 1
        return [
            SkillSignal(
                skill_id=r["skill"],
                source=DataSource.PATENTS,
                timestamp=datetime.fromisoformat(r["date"]),
                value=r["filing_count"] / max_count,
                raw_count=r["filing_count"],
                metadata={"top_assignees": r["top_assignees"]},
            )
            for r in raw_records
        ]


class ResearchPubsConnector(SourceConnector):
    source = DataSource.RESEARCH

    def fetch_raw(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        tech_skills = [s for s in SKILL_TAXONOMY if s.category in ("technical", "domain")]
        base_date = since or datetime(2020, 1, 1)
        for sk in tech_skills:
            for q in range(20):
                dt = base_date + timedelta(days=90 * q)
                if dt > datetime.utcnow():
                    break
                pubs = int(random.uniform(10, 200) * (1 + q / 20 * random.uniform(0.1, 1.0)))
                citations = pubs * random.randint(2, 15)
                records.append({
                    "skill": sk.canonical,
                    "date": dt.isoformat(),
                    "publication_count": max(0, pubs),
                    "citation_count": max(0, citations),
                })
        return records

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[SkillSignal]:
        if not raw_records:
            return []
        max_pub = max(r["publication_count"] for r in raw_records) or 1
        return [
            SkillSignal(
                skill_id=r["skill"],
                source=DataSource.RESEARCH,
                timestamp=datetime.fromisoformat(r["date"]),
                value=r["publication_count"] / max_pub,
                raw_count=r["publication_count"],
                metadata={"citation_count": r["citation_count"]},
            )
            for r in raw_records
        ]


class StartupFundingConnector(SourceConnector):
    source = DataSource.STARTUPS

    def fetch_raw(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        base_date = since or datetime(2020, 1, 1)
        for sk in SKILL_TAXONOMY:
            for q in range(20):
                dt = base_date + timedelta(days=90 * q)
                if dt > datetime.utcnow():
                    break
                funding_m = random.uniform(1, 50) * (1 + q / 20 * random.uniform(0.2, 1.5))
                deals = random.randint(1, 15)
                records.append({
                    "skill": sk.canonical,
                    "date": dt.isoformat(),
                    "funding_million": round(funding_m, 2),
                    "deal_count": deals,
                })
        return records

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[SkillSignal]:
        if not raw_records:
            return []
        max_funding = max(r["funding_million"] for r in raw_records) or 1
        return [
            SkillSignal(
                skill_id=r["skill"],
                source=DataSource.STARTUPS,
                timestamp=datetime.fromisoformat(r["date"]),
                value=r["funding_million"] / max_funding,
                raw_count=r["deal_count"],
                metadata={"funding_million": r["funding_million"]},
            )
            for r in raw_records
        ]


class PolicySignalsConnector(SourceConnector):
    source = DataSource.POLICY

    def fetch_raw(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        policy_relevant = [
            s for s in SKILL_TAXONOMY
            if s.domain in ("ai_ml", "security", "quantum", "web3", "emerging", "energy")
        ]
        records: List[Dict[str, Any]] = []
        base_date = since or datetime(2020, 1, 1)
        for sk in policy_relevant:
            for q in range(20):
                dt = base_date + timedelta(days=90 * q)
                if dt > datetime.utcnow():
                    break
                mentions = int(random.uniform(0, 30) * (1 + q / 20 * random.uniform(0, 0.8)))
                records.append({
                    "skill": sk.canonical,
                    "date": dt.isoformat(),
                    "policy_mentions": max(0, mentions),
                    "regulatory_sentiment": round(random.uniform(-1, 1), 2),
                })
        return records

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[SkillSignal]:
        if not raw_records:
            return []
        max_mentions = max(r["policy_mentions"] for r in raw_records) or 1
        return [
            SkillSignal(
                skill_id=r["skill"],
                source=DataSource.POLICY,
                timestamp=datetime.fromisoformat(r["date"]),
                value=r["policy_mentions"] / max_mentions,
                raw_count=r["policy_mentions"],
                metadata={"regulatory_sentiment": r["regulatory_sentiment"]},
            )
            for r in raw_records
        ]


# ── Pipeline Orchestrator ─────────────────────────────────────────────────

class ETLPipeline:
    """Orchestrates all source connectors and merges signals."""

    def __init__(self) -> None:
        self.connectors: List[SourceConnector] = [
            JobPostingsConnector(),
            PatentFilingsConnector(),
            ResearchPubsConnector(),
            StartupFundingConnector(),
            PolicySignalsConnector(),
        ]
        self._signals: List[SkillSignal] = []

    def run(self, since: Optional[datetime] = None) -> pd.DataFrame:
        """Run the full ETL pipeline and return a unified DataFrame."""
        all_signals: List[SkillSignal] = []
        for connector in self.connectors:
            try:
                signals = connector.ingest(since)
                all_signals.extend(signals)
            except Exception as e:
                logger.error(f"Connector {connector.source.value} failed: {e}")
        self._signals = all_signals
        logger.info(f"Total signals ingested: {len(all_signals)}")
        return self.to_dataframe(all_signals)

    @staticmethod
    def to_dataframe(signals: List[SkillSignal]) -> pd.DataFrame:
        if not signals:
            return pd.DataFrame()
        rows = [s.model_dump() for s in signals]
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(["skill_id", "source", "timestamp"]).reset_index(drop=True)
        return df

    def get_skill_timeseries(self, df: pd.DataFrame, skill_id: str) -> pd.DataFrame:
        """Aggregate signals across sources into a single time series for a skill."""
        skill_df = df[df["skill_id"] == skill_id].copy()
        if skill_df.empty:
            return pd.DataFrame()
        # Pivot by source and resample monthly
        skill_df["month"] = skill_df["timestamp"].dt.to_period("M").dt.to_timestamp()
        agg = skill_df.groupby(["month", "source"]).agg(
            value=("value", "mean"),
            raw_count=("raw_count", "sum"),
        ).reset_index()
        # Create composite signal (weighted average across sources)
        source_weights = {"jobs": 0.35, "patents": 0.20, "research": 0.20, "startups": 0.15, "policy": 0.10}
        pivoted = agg.pivot_table(index="month", columns="source", values="value", fill_value=0)
        composite = pd.Series(0.0, index=pivoted.index)
        for src, weight in source_weights.items():
            if src in pivoted.columns:
                composite += pivoted[src] * weight
        result = pd.DataFrame({"month": pivoted.index, "composite_signal": composite.values})
        # Also keep per-source signals
        for src in source_weights:
            result[f"signal_{src}"] = pivoted[src].values if src in pivoted.columns else 0.0
        return result
