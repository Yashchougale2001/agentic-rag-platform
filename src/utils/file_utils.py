import os
import mimetypes
import uuid
from pathlib import Path
from typing import Optional
import requests


def detect_mime_type(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def get_extension(path: str) -> str:
    return Path(path).suffix.lower()


def download_file(url: str, tmp_dir: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    content_disposition = response.headers.get("content-disposition")
    if content_disposition and "filename=" in content_disposition:
        filename = content_disposition.split("filename=")[-1].strip('" ')
    else:
        filename = url.split("/")[-1] or f"file-{uuid.uuid4().hex}"
    tmp_path = Path(tmp_dir) / filename
    with open(tmp_path, "wb") as f:
        f.write(response.content)
    return str(tmp_path)


def is_remote_path(path_or_url: str) -> bool:
    return path_or_url.startswith("http://") or path_or_url.startswith("https://")