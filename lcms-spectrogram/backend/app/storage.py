from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from .models import SessionRecord


class SessionStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, SessionRecord] = {}

    def create_session_dir(self) -> tuple[str, Path]:
        session_id = uuid4().hex[:10]
        session_dir = self.root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_id, session_dir

    def save(self, record: SessionRecord) -> SessionRecord:
        self._records[record.session_id] = record
        return record

    def get(self, session_id: str) -> SessionRecord | None:
        return self._records.get(session_id)
