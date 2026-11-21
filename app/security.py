from __future__ import annotations
import os, base64, hashlib, hmac, secrets
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from .db import DATA_DIR

KEY_PATH = DATA_DIR / ".fernet.key"

def get_fernet() -> Fernet:
    key = os.getenv("PROOF_ENCRYPTION_KEY", "").strip()
    if key and key != "REPLACE_WITH_FERNET_KEY":
        return Fernet(key.encode())
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError("PROOF_ENCRYPTION_KEY is required in production")
    if KEY_PATH.exists():
        key = KEY_PATH.read_text().strip()
    else:
        key = Fernet.generate_key().decode()
        KEY_PATH.write_text(key)
        try: KEY_PATH.chmod(0o600)
        except OSError: pass
    return Fernet(key.encode())

FERNET = get_fernet()

def encrypt_text(value: str | None) -> str:
    return FERNET.encrypt((value or "").encode("utf-8")).decode("ascii")

def decrypt_text(value: str | None) -> str:
    if not value: return ""
    try: return FERNET.decrypt(value.encode("ascii")).decode("utf-8")
    except InvalidToken: raise RuntimeError("Encryption key mismatch: cannot decrypt stored data")

def encrypt_bytes(value: bytes) -> bytes:
    return FERNET.encrypt(value)

def decrypt_bytes(value: bytes) -> bytes:
    return FERNET.decrypt(value)

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def password_hash(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=2**15, r=8, p=1, dklen=64, maxmem=128*1024*1024)
    return "scrypt$32768$8$1$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(derived).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        alg, n, r, p, salt_b64, hash_b64 = encoded.split("$")
        if alg != "scrypt": return False
        salt = base64.urlsafe_b64decode(salt_b64)
        expected = base64.urlsafe_b64decode(hash_b64)
        actual = hashlib.scrypt(password.encode(), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected), maxmem=128*1024*1024)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def new_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)
