"""
The booking state machine. All status changes MUST go through transition_booking() —
never set booking.status = X directly elsewhere in the codebase. This is what makes
Day 11's auto-decrement/increment and Day 15's no-show detection reliable: every
change is logged and only happens via an allowed transition.
"""
from django.db import transaction
from django.utils import timezone

from .models import Booking, BookingStatus, BookingStatusLog

# Map of allowed transitions: current status -> set of statuses it can move to
ALLOWED_TRANSITIONS = {
    BookingStatus.REQUESTED: {BookingStatus.CONFIRMED, BookingStatus.REJECTED, BookingStatus.CANCELLED, BookingStatus.ESCALATED},
    BookingStatus.CONFIRMED: {BookingStatus.COMPLETED, BookingStatus.CANCELLED, BookingStatus.NO_SHOW},
    BookingStatus.ESCALATED: {BookingStatus.CONFIRMED, BookingStatus.REJECTED},
    # Terminal states — nothing can transition out of these
    BookingStatus.REJECTED: set(),
    BookingStatus.COMPLETED: set(),
    BookingStatus.CANCELLED: set(),
    BookingStatus.NO_SHOW: set(),
}


class InvalidTransitionError(Exception):
    pass


@transaction.atomic
def transition_booking(booking: Booking, new_status: str, changed_by=None, note: str = "") -> Booking:
    """
    The only sanctioned way to change a booking's status.
    - Validates the transition is allowed from the current state
    - Locks the row (select_for_update) to prevent race conditions — e.g. two hospital admins
      confirming the same booking at the same moment, or a confirm racing a cancel
    - Writes an immutable BookingStatusLog entry
    - Bed inventory adjustment (Day 11) will hook in here, not in the view
    """
    locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
    current_status = locked_booking.status

    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise InvalidTransitionError(
            f"Cannot move booking from '{current_status}' to '{new_status}'. "
            f"Allowed next states: {sorted(allowed) or 'none (terminal state)'}"
        )

    locked_booking.status = new_status
    locked_booking.save(update_fields=["status", "updated_at"])

    BookingStatusLog.objects.create(
        booking=locked_booking,
        from_status=current_status,
        to_status=new_status,
        changed_by=changed_by,
        note=note,
    )

    return locked_booking


def can_transition(current_status: str, new_status: str) -> bool:
    """Non-mutating check — useful for the API to decide which action buttons to expose."""
    return new_status in ALLOWED_TRANSITIONS.get(current_status, set())
