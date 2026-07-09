"""
Defines what counts as "stale" inventory data — shared by the API (to surface a warning to
patients/admins) and the alert command (to decide who needs a nudge to update their numbers).
"""
from django.utils import timezone

FRESH_THRESHOLD_HOURS = 1     # updated within this window: shown as fresh/green, no concern
WARNING_THRESHOLD_HOURS = 6   # updated within this window: shown as aging/amber
# Anything older than WARNING_THRESHOLD_HOURS is "stale" (red) — and triggers the
# hospital-admin alert command if it stays that way.


def hours_since(dt) -> float:
    if not dt:
        return float("inf")
    return (timezone.now() - dt).total_seconds() / 3600


def staleness_level(dt) -> str:
    """Returns 'fresh', 'aging', or 'stale' based on how long ago dt was."""
    hours = hours_since(dt)
    if hours <= FRESH_THRESHOLD_HOURS:
        return "fresh"
    elif hours <= WARNING_THRESHOLD_HOURS:
        return "aging"
    return "stale"
