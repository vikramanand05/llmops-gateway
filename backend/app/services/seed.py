from app.core.security import generate_api_key
from app.db.session import SessionLocal
from app.models.api_key import APIKey
from app.models.prompt import PromptVersion


def seed_default_data() -> None:
    db = SessionLocal()
    try:
        if not db.query(APIKey).first():
            raw_key, key_hash, prefix = generate_api_key()
            db.add(
                APIKey(
                    name="demo-key",
                    key_hash=key_hash,
                    key_prefix=prefix,
                    rpm_limit=60,
                    tpd_limit=10_000,
                )
            )
            print(f"Seeded demo API key. Save this local key: {raw_key}")

        exists = (
            db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == "support-assistant", PromptVersion.version == "v1")
            .first()
        )
        if not exists:
            db.add(
                PromptVersion(
                    prompt_id="support-assistant",
                    name="Support Assistant",
                    version="v1",
                    template="You are a concise support assistant for $company. Keep answers actionable.",
                )
            )
        db.commit()
    finally:
        db.close()
