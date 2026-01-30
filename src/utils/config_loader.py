import os
import yaml
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def _load_yaml(name: str) -> dict:
    path = CONFIG_DIR / name
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings() -> dict:
    return _load_yaml("settings.yaml")


def load_model_config() -> dict:
    return _load_yaml("model.yaml")


def load_paths() -> dict:
    return _load_yaml("paths.yaml").get("paths", {})


def ensure_directories():
    paths = load_paths()
    for key in ["data_dir", "db_dir", "logs_dir", "tmp_dir"]:
        p = Path(paths.get(key, ""))
        if p and not p.exists():
            p.mkdir(parents=True, exist_ok=True)