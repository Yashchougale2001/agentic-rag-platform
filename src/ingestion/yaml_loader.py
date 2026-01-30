from typing import List, Dict
from pathlib import Path
import yaml


def load_yaml_file(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    docs = []

    def flatten(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_prefix = f"{prefix}.{k}" if prefix else k
                yield from flatten(v, new_prefix)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                new_prefix = f"{prefix}[{i}]"
                yield from flatten(v, new_prefix)
        else:
            yield f"{prefix}: {obj}"

    text = "\n".join(list(flatten(data)))
    docs.append(
        {
            "id": Path(path).name,
            "text": text,
            "metadata": {"source": str(path), "file_type": "yaml"},
        }
    )
    return docs