# src/utils/logging_config.py

from __future__ import annotations

import logging
import os
from typing import Optional

try:
    # Use your existing config loader if available
    from src.utils.config_loader import load_settings
except Exception:  # pragma: no cover - fallback if not available
    load_settings = None  # type: ignore


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Initialize application-wide logging.

    Safe to call multiple times; subsequent calls will be no-ops.

    Priority for configuration:
      1) Explicit function args (level, log_file)
      2) config/settings.yaml -> settings["logging"]
      3) Hard-coded defaults

    Example `config/settings.yaml` section this supports:

        logging:
          level: INFO
          file: logs/app.log
          format: "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
          datefmt: "%Y-%m-%d %H:%M:%S"
    """
    # If we've already configured logging once, just return root logger
    if getattr(setup_logging, "_configured", False):
        return logging.getLogger()

    settings = {}
    if load_settings is not None:
        try:
            settings = load_settings() or {}
        except Exception:
            settings = {}

    log_cfg = settings.get("logging", {}) if isinstance(settings, dict) else {}

    # Resolve level
    level_str = level or log_cfg.get("level", "INFO")
    numeric_level = getattr(logging, level_str.upper(), logging.INFO)

    # Resolve format and datefmt
    fmt = log_cfg.get(
        "format",
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    datefmt = log_cfg.get("datefmt", "%Y-%m-%d %H:%M:%S")

    # Resolve log file path (optional)
    file_path = log_file or log_cfg.get("file")

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers to avoid duplicate logs
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optional file handler
    if file_path:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # Fall back to console-only logging
            root_logger.warning("Failed to set up file logging at %s: %s", file_path, e)

    # Quiet some noisy third-party loggers (tweak as needed)
    logging.getLogger("chromadb").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    setup_logging._configured = True  # type: ignore[attr-defined]
    return root_logger


__all__ = ["setup_logging"]