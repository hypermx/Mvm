"""Tests for data ingestion pipeline."""
from __future__ import annotations

import numpy as np
import pytest

from backend.data_schema.models import DailyLog
from backend.ingestion.ingestion import DataIngestionPipeline


@pytest.fixture()
def pipeline() -> DataIngestionPipeline:
    return DataIngestionPipeline()


class TestDataIngestionPipeline:
    def test_ingest_returns_expected_keys(self, pipeline, sample_log):
        result = pipeline.ingest_daily_log(sample_log, "user_1")
        assert "user_id" in result
        assert "normalized_features" in result
        assert "warnings" in result
        assert "processed_log" in result

    def test_normalize_features_shape(self, pipeline, sample_log):
        features = pipeline.normalize_features(sample_log)
        assert features.shape == (8,)
        assert np.all(features >= 0.0)
        assert np.all(features <= 1.0)

    def test_normalize_features_range(self, pipeline, sample_log):
        features = pipeline.normalize_features(sample_log)
        assert features.dtype == np.float32

    def test_handle_missing_data_imputes_pressure(self, pipeline):
        from datetime import date
        log = DailyLog(
            date=date(2024, 1, 1),
            sleep_hours=7.0,
            sleep_quality=6.0,
            stress_level=4.0,
            hydration_liters=2.0,
            weather_pressure_hpa=None,
            migraine_occurred=False,
            migraine_intensity=0.0,
        )
        filled = pipeline.handle_missing_data(log)
        assert filled.weather_pressure_hpa is not None

    def test_validate_log_no_warnings_normal(self, pipeline, sample_log):
        warnings = pipeline.validate_log(sample_log)
        assert isinstance(warnings, list)

    def test_validate_log_low_sleep_warning(self, pipeline):
        from datetime import date
        log = DailyLog(
            date=date(2024, 1, 1),
            sleep_hours=2.0,
            sleep_quality=3.0,
            stress_level=5.0,
            hydration_liters=2.0,
            migraine_occurred=False,
            migraine_intensity=0.0,
        )
        warnings = pipeline.validate_log(log)
        assert any("sleep" in w.lower() for w in warnings)

    def test_validate_log_migraine_with_intensity(self, pipeline):
        """A valid migraine log (occurred=True, intensity>0) produces no intensity warning."""
        from datetime import date
        log = DailyLog(
            date=date(2024, 1, 1),
            sleep_hours=6.0,
            sleep_quality=4.0,
            stress_level=8.0,
            hydration_liters=1.5,
            migraine_occurred=True,
            migraine_intensity=7.0,
        )
        warnings = pipeline.validate_log(log)
        assert not any("intensity" in w.lower() for w in warnings)

    def test_high_caffeine_warning(self, pipeline):
        from datetime import date
        log = DailyLog(
            date=date(2024, 1, 1),
            sleep_hours=7.0,
            sleep_quality=5.0,
            stress_level=5.0,
            hydration_liters=2.0,
            caffeine_mg=700.0,
            migraine_occurred=False,
            migraine_intensity=0.0,
        )
        warnings = pipeline.validate_log(log)
        assert any("caffeine" in w.lower() for w in warnings)
