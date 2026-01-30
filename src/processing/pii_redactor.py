from typing import List, Tuple


def redact_pii(text: str, spans: List[Tuple[int, int]]) -> str:
    """
    Replace PII spans with [REDACTED].
    """
    if not spans:
        return text

    result = []
    last_idx = 0
    for start, end in spans:
        result.append(text[last_idx:start])
        result.append("[REDACTED]")
        last_idx = end
    result.append(text[last_idx:])
    return "".join(result)