"""Tests for privacy utilities."""
from __future__ import annotations

import pytest

from backend.privacy.privacy import PrivacyManager


@pytest.fixture()
def pm() -> PrivacyManager:
    return PrivacyManager()


class TestPrivacyManager:
    def test_encrypt_decrypt_roundtrip(self, pm):
        data = {"field": "value", "number": 42}
        encrypted = pm.encrypt_user_data(data, "user_abc")
        decrypted = pm.decrypt_user_data(encrypted, "user_abc")
        assert decrypted == {"field": "value", "number": 42}

    def test_encrypt_produces_bytes(self, pm):
        encrypted = pm.encrypt_user_data({"x": 1}, "user_abc")
        assert isinstance(encrypted, bytes)

    def test_different_users_cannot_decrypt(self, pm):
        from cryptography.fernet import InvalidToken
        encrypted = pm.encrypt_user_data({"secret": "data"}, "user_one")
        with pytest.raises(Exception):
            pm.decrypt_user_data(encrypted, "user_two")

    def test_generate_user_key_deterministic(self, pm):
        key1 = pm.generate_user_key("same_user")
        key2 = pm.generate_user_key("same_user")
        assert key1 == key2

    def test_different_users_different_keys(self, pm):
        key_a = pm.generate_user_key("user_a")
        key_b = pm.generate_user_key("user_b")
        assert key_a != key_b

    def test_anonymize_logs_returns_list(self, pm, sample_logs):
        result = pm.anonymize_logs(sample_logs)
        assert isinstance(result, list)
        assert len(result) == len(sample_logs)

    def test_anonymize_logs_hashes_cycle_day(self, pm, migraine_log):
        from datetime import date
        from backend.data_schema.models import DailyLog
        log_with_cycle = DailyLog(
            date=date(2024, 1, 1),
            sleep_hours=7.0,
            sleep_quality=6.0,
            stress_level=4.0,
            hydration_liters=2.0,
            migraine_occurred=True,
            migraine_intensity=5.0,
            menstrual_cycle_day=14,
        )
        result = pm.anonymize_logs([log_with_cycle])
        assert result[0]["menstrual_cycle_day"] != 14
        assert isinstance(result[0]["menstrual_cycle_day"], str)

    def test_encrypt_complex_data(self, pm):
        data = {"list": [1, 2, 3], "nested": {"a": "b"}}
        encrypted = pm.encrypt_user_data(data, "user_x")
        decrypted = pm.decrypt_user_data(encrypted, "user_x")
        assert decrypted["list"] == [1, 2, 3]
        assert decrypted["nested"] == {"a": "b"}
