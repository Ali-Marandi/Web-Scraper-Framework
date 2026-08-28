from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonRepository:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.kp_dir = self.base_dir / "knowledge_points"
        self.progress_dir = self.base_dir / "user_progress"
        self.sessions_dir = self.base_dir / "sessions"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for d in [self.kp_dir, self.progress_dir, self.sessions_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def load_json(self, path: Path, default: Any = None) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def save_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def knowledge_points_path(self, document_id: str) -> Path:
        return self.kp_dir / f"{document_id}.json"

    def progress_path(self, user_id: str, document_id: str) -> Path:
        return self.progress_dir / f"{user_id}__{document_id}.json"

    def session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"
