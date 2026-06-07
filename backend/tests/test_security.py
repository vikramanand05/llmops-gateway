from app.core.security import generate_api_key, hash_api_key, verify_api_key
from app.middleware.api_key import _extract_api_key


def test_api_key_hashing_and_verification():
    raw, key_hash, prefix = generate_api_key()
    assert raw.startswith("llmops_")
    assert prefix == raw[:14]
    assert key_hash == hash_api_key(raw)
    assert verify_api_key(raw, key_hash)
    assert not verify_api_key("wrong", key_hash)


def test_extract_api_key_from_bearer_header():
    request = type("RequestStub", (), {"headers": {"authorization": "Bearer llmops_test"}})()
    assert _extract_api_key(request) == "llmops_test"
