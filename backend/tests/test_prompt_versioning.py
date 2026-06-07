from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.prompt import PromptVersion
from app.schemas.chat import ChatMessage, PromptReference
from app.services.prompt_renderer import apply_prompt_reference


def test_prompt_reference_is_rendered():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(PromptVersion(prompt_id="demo", name="Demo", version="v1", template="Hello $name"))
    db.commit()

    messages = apply_prompt_reference(
        db,
        [ChatMessage(role="user", content="Question")],
        PromptReference(prompt_id="demo", version="v1", variables={"name": "Vikram"}),
    )

    assert messages[0].role == "system"
    assert messages[0].content == "Hello Vikram"
