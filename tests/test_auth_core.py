"""Auth core utilities tests - bcrypt + JWT (no DB)."""

import time

import pytest

from app.core import auth as auth_mod
from app.core.auth import AuthError


def test_hash_and_verify_password_roundtrip():
    h = auth_mod.hash_password("super-secret-123")
    assert h != "super-secret-123"
    assert h.startswith("$2b$") or h.startswith("$2a$")
    assert auth_mod.verify_password("super-secret-123", h) is True
    assert auth_mod.verify_password("wrong-password", h) is False


def test_hash_password_empty_raises():
    with pytest.raises(AuthError):
        auth_mod.hash_password("")


def test_verify_password_with_empty_inputs():
    assert auth_mod.verify_password("", "anything") is False
    assert auth_mod.verify_password("password", "") is False


def test_create_and_decode_token_roundtrip():
    token = auth_mod.create_access_token(subject=42, extra={"email": "a@b.com"})
    assert isinstance(token, str)
    assert token.count(".") == 2  # JWT has 3 parts joined by dots

    payload = auth_mod.decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["email"] == "a@b.com"
    assert "exp" in payload and "iat" in payload


def test_decode_invalid_token_raises():
    with pytest.raises(AuthError):
        auth_mod.decode_access_token("not.a.valid.token")


def test_decode_expired_token_raises(monkeypatch):
    # Force exp into the past by mocking settings to 0 hours
    from app.core.config import settings
    monkeypatch.setattr(settings, "JWT_EXPIRY_HOURS", -1)
    token = auth_mod.create_access_token(subject=1)
    time.sleep(0.05)  # ensure exp < now
    with pytest.raises(AuthError):
        auth_mod.decode_access_token(token)
