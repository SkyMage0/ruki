"""Encryption service for PII: phones, document numbers. Keys from env only."""

import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.config import get_settings


class EncryptionService:
    """Fernet encryption for sensitive fields. Supports key rotation via env."""

    def __init__(self) -> None:
        settings = get_settings()
        key_b64 = settings.encryption_key
        if not key_b64:
            # Dev fallback: derive from JWT_SECRET (do not use in prod without ENCRYPTION_KEY)
            raw = (settings.jwt_secret or "dev-secret").encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"ruki_enc_v1",
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(raw))
        else:
            key = key_b64.encode() if isinstance(key_b64, str) else key_b64
        self._fernet = Fernet(key)

    def encrypt(self, plain: str) -> str:
        if not plain:
            return ""
        return self._fernet.encrypt(plain.encode()).decode()

    def decrypt(self, cipher: str) -> str | None:
        if not cipher:
            return None
        try:
            return self._fernet.decrypt(cipher.encode()).decode()
        except (InvalidToken, Exception):
            return None


# Singleton for app use
_encryption: EncryptionService | None = None


def get_encryption() -> EncryptionService:
    global _encryption
    if _encryption is None:
        _encryption = EncryptionService()
    return _encryption
