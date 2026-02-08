# src/ingestion/json_loader.py
from typing import List, Dict, Any
from pathlib import Path
import json


def _flatten_kv(obj: Any, prefix: str = "") -> List[str]:
    """
    Flatten nested dict/list values into 'path: value' strings.
    Used when we need a single text blob from arbitrary JSON.
    """
    lines: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            lines.extend(_flatten_kv(v, new_prefix))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_prefix = f"{prefix}[{i}]"
            lines.extend(_flatten_kv(v, new_prefix))
    else:
        # primitive value
        lines.append(f"{prefix}: {obj}")
    return lines


def load_json(path: str) -> List[Dict]:
    """
    Load a JSON file and convert it into a list of docs:

    - If top-level is a list of objects: each element -> one doc
    - If top-level has a key 'records' that is a list: each record -> one doc
    - Otherwise: flatten entire JSON into one doc.

    Each doc:
    {
      "id": "<filename>-<index>",
      "text": "<flattened text>",
      "metadata": { "source": path, "file_type": "json", ... }
    }
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)

    docs: List[Dict] = []

    def record_to_text(rec: Dict[str, Any]) -> str:
        parts = []
        for k, v in rec.items():
            parts.append(f"{k}: {v}")
        return " ".join(parts)

    # Case 1: top-level list -> treat each item as a record
    if isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                text = record_to_text(item)
            else:
                # non-dict; just stringify
                text = str(item)
            docs.append(
                {
                    "id": f"{p.name}-{idx}",
                    "text": text,
                    "metadata": {
                        "source": str(path),
                        "file_type": "json",
                        "record_index": idx,
                    },
                }
            )
        return docs

    # Case 2: top-level dict with 'records' key that is a list
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        for idx, item in enumerate(data["records"]):
            if isinstance(item, dict):
                text = record_to_text(item)
            else:
                text = str(item)
            docs.append(
                {
                    "id": f"{p.name}-records-{idx}",
                    "text": text,
                    "metadata": {
                        "source": str(path),
                        "file_type": "json",
                        "record_index": idx,
                        "container_key": "records",
                    },
                }
            )
        return docs

    # Fallback: flatten entire JSON into one doc
    lines = _flatten_kv(data)
    text = "\n".join(lines)
    docs.append(
        {
            "id": p.name,
            "text": text,
            "metadata": {
                "source": str(path),
                "file_type": "json",
            },
        }
    )
    return docs