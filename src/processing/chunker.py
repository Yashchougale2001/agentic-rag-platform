from typing import List

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 200


def chunk_text(
    text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[str]:
    """
    Simple character-based chunker with overlap.
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == text_len:
            break
        start = end - overlap

    return chunks