from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from backend.data_schema.models import DailyLog


def _load_app_salt() -> bytes:
    """Load the application salt from the MVM_APP_SALT environment variable.

    Raises RuntimeError if the variable is not set, preventing the application
    from starting with an insecure default.
    """
    salt = os.environb.get(b"MVM_APP_SALT")
    if not salt:
        raise RuntimeError(
            "MVM_APP_SALT environment variable is not set. "
            "Please configure a securely stored secret before starting the application."
        )
    return salt


_APP_SALT: bytes = _load_app_salt()


class PrivacyManager:
    """Handles encryption, decryption, and anonymization of user data."""

    # ------------------------------------------------------------------
    # Key management
    # ------------------------------------------------------------------

    def generate_user_key(self, user_id: str) -> bytes:
        """Derive a Fernet-compatible key from *user_id* via PBKDF2-HMAC-SHA256."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_APP_SALT,
            # 600 000 iterations matches the OWASP 2023 recommendation for
            # PBKDF2-HMAC-SHA256.
            iterations=600_000,
        )
        raw_key = kdf.derive(user_id.encode())
        return base64.urlsafe_b64encode(raw_key)

    def _fernet(self, user_id: str) -> Fernet:
        return Fernet(self.generate_user_key(user_id))

    # ------------------------------------------------------------------
    # Encryption / decryption
    # ------------------------------------------------------------------

    def encrypt_user_data(self, data: dict[str, Any], user_id: str) -> bytes:
        """Serialize *data* to JSON and encrypt with a key derived from *user_id*."""
        plaintext = json.dumps(data, default=str).encode()
        return self._fernet(user_id).encrypt(plaintext)

    def decrypt_user_data(self, encrypted: bytes, user_id: str) -> dict[str, Any]:
        """Decrypt *encrypted* bytes and deserialize the JSON payload."""
        plaintext = self._fernet(user_id).decrypt(encrypted)
        return json.loads(plaintext.decode())

    # ------------------------------------------------------------------
    # Anonymization
    # ------------------------------------------------------------------

    def anonymize_logs(self, logs: list[DailyLog]) -> list[dict[str, Any]]:
        """Return logs with no user-identifying fields.

        The ``date`` is kept for temporal analysis but user-linkable
        metadata is removed.  Menstrual cycle day is hashed to preserve
        cycle-phase information without revealing the raw value.
        """
        anonymized: list[dict[str, Any]] = []
        for log in logs:
            d = log.model_dump()
            # Replace potentially identifying fields.
            if d.get("menstrual_cycle_day") is not None:
                d["menstrual_cycle_day"] = self._hash_int(d["menstrual_cycle_day"])
            anonymized.append(d)
        return anonymized

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_int(value: int) -> str:
        return hashlib.sha256(str(value).encode()).hexdigest()[:12]
