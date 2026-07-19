"""Shared FastAPI dependencies.

Every route handler gets its DB session and settings through this
module rather than constructing them itself. This is the
dependency-injection seam every future route reuses — an agent-execution
route, for instance, would add a `ChatModel` dependency here rather than
calling `get_chat_model()` inline.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db

#: Injected DB session. Reuses app.db.session.get_db (defined in the
#: initial scaffold) rather than redefining session handling here.
DbSession = Annotated[Session, Depends(get_db)]

#: Injected application settings.
AppSettings = Annotated[Settings, Depends(get_settings)]