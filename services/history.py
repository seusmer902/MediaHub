"""Historial de descargas (JSON)."""
import json
import uuid
from datetime import datetime

from config import HISTORY_FILE, MAX_HISTORY


def load() -> list:
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(items: list) -> None:
    tmp = HISTORY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(HISTORY_FILE)


def add(**fields) -> dict:
    entry = {
        "id": uuid.uuid4().hex,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        **fields,
    }
    items = load()
    items.insert(0, entry)
    _save(items[:MAX_HISTORY])
    return entry


def remove(entry_id: str) -> None:
    _save([e for e in load() if e.get("id") != entry_id])


def clear() -> None:
    _save([])
