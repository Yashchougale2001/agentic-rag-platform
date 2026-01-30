from typing import List, Dict
from pathlib import Path


def load_md_file(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return [
        {
            "id": Path(path).name,
            "text": text,
            "metadata": {"source": str(path), "file_type": "markdown"},
        }
    ]