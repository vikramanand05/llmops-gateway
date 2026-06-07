import hashlib
import secrets


def generate_api_key() -> tuple[str, str, str]:
    raw_key = f"llmops_{secrets.token_urlsafe(32)}"
    return raw_key, hash_api_key(raw_key), raw_key[:14]


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    return secrets.compare_digest(hash_api_key(raw_key), stored_hash)
