# from typing import List

# DEFAULT_CHUNK_SIZE = 800
# DEFAULT_CHUNK_OVERLAP = 200


# def chunk_text(
#     text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP
# ) -> List[str]:
#     """
#     Simple character-based chunker with overlap.
#     """
#     chunks = []
#     start = 0
#     text_len = len(text)

#     while start < text_len:
#         end = min(start + chunk_size, text_len)
#         chunk = text[start:end]
#         chunks.append(chunk)
#         if end == text_len:
#             break
#         start = end - overlap

#     return chunks
from typing import List
import re

from src.utils.config_loader import load_model_config

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 200


def _get_chunk_params(chunk_size: int = None, overlap: int = None):
    """
    If chunk_size/overlap are provided, use them.
    Otherwise, pull defaults from model.yaml:chunking or fall back to constants.
    """
    cfg = load_model_config().get("chunking", {})

    default_size = cfg.get("chunk_size", DEFAULT_CHUNK_SIZE)
    default_overlap = cfg.get("chunk_overlap", DEFAULT_CHUNK_OVERLAP)

    if chunk_size is None:
        chunk_size = default_size
    if overlap is None:
        overlap = default_overlap

    return chunk_size, overlap


def _split_by_chars(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    text_len = len(text)

    if chunk_size <= 0:
        return [text]

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == text_len:
            break
        # ensure we don't go negative
        start = max(0, end - overlap)

    return chunks


def _markdown_section_chunker(
    text: str, chunk_size: int, overlap: int
) -> List[str]:
    """
    Very simple markdown-aware chunker:
    - Split by heading lines starting with '#'
    - Then apply char-based splitting within each section.
    """
    # Split and keep the delimiters (headings)
    parts = re.split(r"(^#+ .*$)", text, flags=re.MULTILINE)

    sections: List[str] = []
    i = 0
    while i < len(parts):
        if re.match(r"^#+ .*$", parts[i]):
            header = parts[i]
            body = parts[i + 1] if i + 1 < len(parts) else ""
            sections.append(header + "\n" + body)
            i += 2
        else:
            if parts[i].strip():
                sections.append(parts[i])
            i += 1

    chunks: List[str] = []
    for sec in sections:
        chunks.extend(_split_by_chars(sec, chunk_size, overlap))

    return chunks


def chunk_text(
    text: str,
    chunk_size: int = None,
    overlap: int = None,
    file_type: str = None,
) -> List[str]:
    """
    Chunk text into overlapping segments.

    - If chunk_size/overlap are None, they are read from model.yaml:chunking.
    - If file_type is 'md' or 'markdown', use a simple heading-aware markdown chunker.
    - Otherwise, use plain character-based splitting.
    """
    chunk_size, overlap = _get_chunk_params(chunk_size, overlap)
    ft = (file_type or "").lower()

    if ft in ("md", "markdown"):
        return _markdown_section_chunker(text, chunk_size, overlap)

    return _split_by_chars(text, chunk_size, overlap)