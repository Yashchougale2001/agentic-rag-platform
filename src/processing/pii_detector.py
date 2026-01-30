import re
from typing import List, Tuple


class PIIDetector:
    """
    Very simple regex-based PII detector.
    Returns list of (start, end) spans.
    """

    EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    PHONE_RE = re.compile(r"\+?\d[\d\-\s]{7,}\d")
    SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    def detect(self, text: str) -> List[Tuple[int, int]]:
        spans = []
        for regex in [self.EMAIL_RE, self.PHONE_RE, self.SSN_RE]:
            for m in regex.finditer(text):
                spans.append((m.start(), m.end()))
        spans.sort()
        return spans