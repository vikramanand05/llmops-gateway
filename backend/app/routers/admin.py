from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_api_key
from app.db.session import get_db
from app.models.api_key import APIKey
from app.models.prompt import PromptVersion
from app.models.usage import UsageLog
from app.schemas.admin import APIKeyCreate, APIKeyCreated, APIKeyRead, CostSummary, UsageLogRead
from app.schemas.prompt import PromptVersionCreate, PromptVersionRead, PromptVersionUpdate
from app.services.router import DEFAULT_FALLBACK_CHAIN, model_router
from app.services.usage import summarize_costs

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")


@router.post("/api-keys", response_model=APIKeyCreated, dependencies=[Depends(require_admin)])
def create_api_key(payload: APIKeyCreate, db: Session = Depends(get_db)) -> APIKeyCreated:
    raw_key, key_hash, prefix = generate_api_key()
    row = APIKey(
        name=payload.name,
        key_hash=key_hash,
        key_prefix=prefix,
        rpm_limit=payload.rpm_limit,
        tpd_limit=payload.tpd_limit,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return APIKeyCreated(
        id=row.id,
        name=row.name,
        api_key=raw_key,
        key_prefix=row.key_prefix,
        rpm_limit=row.rpm_limit,
        tpd_limit=row.tpd_limit,
    )


@router.get("/api-keys", response_model=list[APIKeyRead], dependencies=[Depends(require_admin)])
def list_api_keys(db: Session = Depends(get_db)) -> list[APIKey]:
    return db.query(APIKey).order_by(APIKey.created_at.desc()).all()


@router.patch("/api-keys/{api_key_id}/disable", response_model=APIKeyRead, dependencies=[Depends(require_admin)])
def disable_api_key(api_key_id: str, db: Session = Depends(get_db)) -> APIKey:
    row = db.get(APIKey, api_key_id)
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    row.active = False
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/usage", response_model=list[UsageLogRead], dependencies=[Depends(require_admin)])
def list_usage_logs(limit: int = Query(100, le=500), db: Session = Depends(get_db)) -> list[UsageLog]:
    return db.query(UsageLog).order_by(UsageLog.created_at.desc()).limit(limit).all()


@router.get("/costs/summary", response_model=CostSummary, dependencies=[Depends(require_admin)])
def cost_summary(db: Session = Depends(get_db)) -> dict:
    return summarize_costs(db)


@router.post("/prompts", response_model=PromptVersionRead, dependencies=[Depends(require_admin)])
def create_prompt(payload: PromptVersionCreate, db: Session = Depends(get_db)) -> PromptVersion:
    row = PromptVersion(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/prompts", response_model=list[PromptVersionRead], dependencies=[Depends(require_admin)])
def list_prompts(db: Session = Depends(get_db)) -> list[PromptVersion]:
    return db.query(PromptVersion).order_by(PromptVersion.prompt_id, PromptVersion.version).all()


@router.put("/prompts/{prompt_row_id}", response_model=PromptVersionRead, dependencies=[Depends(require_admin)])
def update_prompt(prompt_row_id: str, payload: PromptVersionUpdate, db: Session = Depends(get_db)) -> PromptVersion:
    row = db.get(PromptVersion, prompt_row_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/prompts/{prompt_row_id}", dependencies=[Depends(require_admin)])
def delete_prompt(prompt_row_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    row = db.get(PromptVersion, prompt_row_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


@router.get("/providers/health", dependencies=[Depends(require_admin)])
def provider_health() -> dict:
    return {
        "fallback_chain": DEFAULT_FALLBACK_CHAIN,
        "providers": [
            {"model": model, "provider": model_router.provider_for_model(model), "status": "configured"}
            for model in DEFAULT_FALLBACK_CHAIN
        ],
    }
