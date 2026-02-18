"""Tests for the ETL Pipeline."""
import pytest
from asie.etl.pipeline import ETLPipeline


class TestETLPipeline:
    def setup_method(self):
        self.pipeline = ETLPipeline()

    def test_run_pipeline(self):
        df = self.pipeline.run()
        assert not df.empty
        assert "skill_id" in df.columns
        assert "source" in df.columns
        assert "value" in df.columns
        assert "timestamp" in df.columns

    def test_multiple_sources(self):
        df = self.pipeline.run()
        sources = df["source"].unique()
        assert len(sources) >= 4  # jobs, patents, research, startups

    def test_get_skill_timeseries(self):
        df = self.pipeline.run()
        ts = self.pipeline.get_skill_timeseries(df, "python")
        assert not ts.empty
        assert "composite_signal" in ts.columns
        assert "month" in ts.columns

    def test_values_normalised(self):
        df = self.pipeline.run()
        assert df["value"].min() >= 0
        assert df["value"].max() <= 1.0
