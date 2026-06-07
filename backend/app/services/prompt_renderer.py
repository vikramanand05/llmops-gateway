from string import Template

from sqlalchemy.orm import Session

from app.models.prompt import PromptVersion
from app.schemas.chat import ChatMessage, PromptReference


class PromptNotFound(Exception):
    pass


def apply_prompt_reference(db: Session, messages: list[ChatMessage], reference: PromptReference | None) -> list[ChatMessage]:
    if reference is None:
        return messages

    prompt = (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == reference.prompt_id, PromptVersion.version == reference.version)
        .first()
    )
    if prompt is None:
        raise PromptNotFound(f"Prompt {reference.prompt_id}:{reference.version} not found")

    rendered = Template(prompt.template).safe_substitute(reference.variables)
    return [ChatMessage(role="system", content=rendered), *messages]
