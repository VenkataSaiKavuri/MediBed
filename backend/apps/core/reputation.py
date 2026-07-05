"""
Reputation scoring for patients. Score starts at 100 and moves based on how a booking
resolves — reliable behavior (showing up, cancelling early before a bed was ever held)
is neutral-to-positive; no-shows and late cancellations (after a bed was already reserved
for them) cost points. Once a user crosses either threshold below, they're flagged and
lose instant-booking privileges (enforced in apps/bookings/serializers.py).
"""
from django.db import transaction

MIN_SCORE = 0
MAX_SCORE = 100

# Point deltas per outcome
NO_SHOW_PENALTY = -20
LATE_CANCEL_PENALTY = -5  # cancelling AFTER a hospital already held a bed (i.e. was CONFIRMED)
COMPLETED_REWARD = 2      # small reward for reliably following through

# Auto-flag thresholds — crossing EITHER one flags the account
NO_SHOW_COUNT_THRESHOLD = 3
REPUTATION_SCORE_THRESHOLD = 50


def _clamp(score: int) -> int:
    return max(MIN_SCORE, min(MAX_SCORE, score))


@transaction.atomic
def apply_reputation_change(user, delta: int, is_no_show: bool = False) -> None:
    """Applies a reputation delta to a user and re-evaluates whether they should be flagged.
    Locked to avoid a race if somehow two bookings for the same user resolve simultaneously."""
    from apps.users.models import User  # local import avoids a circular import at module load

    locked_user = User.objects.select_for_update().get(pk=user.pk)
    locked_user.reputation_score = _clamp(locked_user.reputation_score + delta)
    if is_no_show:
        locked_user.no_show_count += 1

    should_flag = (
        locked_user.no_show_count >= NO_SHOW_COUNT_THRESHOLD
        or locked_user.reputation_score <= REPUTATION_SCORE_THRESHOLD
    )
    if should_flag and not locked_user.is_flagged:
        locked_user.is_flagged = True

    locked_user.save(update_fields=["reputation_score", "no_show_count", "is_flagged"])
