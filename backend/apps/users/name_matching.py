"""
Basic name-match verification — compares the name a patient typed at upload time against
their account's registered name. This is NOT OCR (we don't read the actual document image/PDF
content) — it's a deliberately simple self-reported check: does what they typed match who they
signed up as. It catches the common case of someone uploading a family member's or a stranger's
document without proper OCR/government-database integration, while staying honest that this is
a "basic" check per the plan's scope — a determined bad actor could still type a fake name that
matches their account. Stronger verification (real OCR + government ID API) would be a future
upgrade, not something to fake with false confidence here.
"""
import re
from difflib import SequenceMatcher

from .models import NameMatchResult

EXACT_MATCH_THRESHOLD = 0.95
CLOSE_MATCH_THRESHOLD = 0.75


def _normalize(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z\s]", "", name)  # strip punctuation/numbers
    name = re.sub(r"\s+", " ", name)
    return name


def compute_name_match(account_name: str, document_name: str) -> tuple[str, float]:
    """Returns (NameMatchResult value, similarity score 0.0-1.0)."""
    a = _normalize(account_name)
    b = _normalize(document_name)

    if not a or not b:
        return NameMatchResult.MISMATCH, 0.0

    score = SequenceMatcher(None, a, b).ratio()

    if score >= EXACT_MATCH_THRESHOLD:
        return NameMatchResult.EXACT_MATCH, score
    elif score >= CLOSE_MATCH_THRESHOLD:
        return NameMatchResult.CLOSE_MATCH, score
    else:
        return NameMatchResult.MISMATCH, score
