import json
from pathlib import Path
from typing import Any


class StorageService:
    """Small JSON store with safe defaults and atomic writes."""

    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load(self, filename: str, default: Any) -> Any:
        path = self.data_dir / filename
        if not path.exists():
            return default
        try:
            with path.open(encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            return default

    def save(self, filename: str, value: Any) -> None:
        path = self.data_dir / filename
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False, default=str)
        temporary.replace(path)
