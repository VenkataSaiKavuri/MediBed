"""
Encrypts/decrypts identity document bytes before they touch disk. Uses Fernet
(symmetric, authenticated encryption) from the `cryptography` package.

Key resolution:
- If ID_DOCUMENT_ENCRYPTION_KEY is set in .env, use it directly (production path).
- If not set (dev convenience), derive a stable key from DJANGO_SECRET_KEY so files encrypted
  during local development stay decryptable across server restarts — a randomly-generated
  key each restart would make every previously-uploaded document permanently unreadable.

IMPORTANT: in production, ID_DOCUMENT_ENCRYPTION_KEY MUST be explicitly set and kept secret —
deriving it from SECRET_KEY is a dev-only convenience, not a production security posture,
since it means anyone with SECRET_KEY (already highly sensitive) could also decrypt ID documents.
"""
import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def _get_fernet_key() -> bytes:
    configured_key = getattr(settings, "ID_DOCUMENT_ENCRYPTION_KEY", "")
    if configured_key:
        return configured_key.encode() if isinstance(configured_key, str) else configured_key

    # Dev fallback: derive a deterministic 32-byte key from SECRET_KEY
    digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_bytes(data: bytes) -> bytes:
    fernet = Fernet(_get_fernet_key())
    return fernet.encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    fernet = Fernet(_get_fernet_key())
    return fernet.decrypt(token)
