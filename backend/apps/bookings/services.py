"""
The booking state machine. All status changes MUST go through transition_booking() —
never set booking.status = X directly elsewhere in the codebase. This is what makes
Day 11's auto-decrement/increment and Day 15's no-show detection reliable: every
change is logged and only happens via an allowed transition.
"""
from django.db import transaction

from apps.hospitals.models import BedInventory

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

# A bed is only actually "held" once a booking is CONFIRMED — not while merely REQUESTED.
# So inventory only ever needs to move at the two edges of that held period:
STATUSES_THAT_RELEASE_A_HELD_BED = {BookingStatus.COMPLETED, BookingStatus.CANCELLED, BookingStatus.NO_SHOW}


class InvalidTransitionError(Exception):
    pass


class NoBedAvailableError(Exception):
    """Raised if a booking tries to move to CONFIRMED but the hospital has 0 available beds
    of that type right now — protects against overbooking beyond physical capacity."""
    pass


def _decrement_bed(hospital_id: int, bed_type: str) -> None:
    try:
        bed = BedInventory.objects.select_for_update().get(hospital_id=hospital_id, bed_type=bed_type)
    except BedInventory.DoesNotExist:
        raise NoBedAvailableError(
            f"No '{bed_type}' bed inventory record exists for this hospital — cannot confirm."
        )
    if bed.available_count <= 0:
        raise NoBedAvailableError(f"No '{bed_type}' beds currently available at this hospital.")
    bed.available_count -= 1
    bed.save(update_fields=["available_count", "updated_at"])


def _increment_bed(hospital_id: int, bed_type: str) -> None:
    try:
        bed = BedInventory.objects.select_for_update().get(hospital_id=hospital_id, bed_type=bed_type)
    except BedInventory.DoesNotExist:
        return  # Nothing to release back to — shouldn't happen if decrement succeeded earlier, but don't crash
    # Never let available exceed total — guards against double-increment bugs silently
    # inflating availability past physical capacity.
    if bed.available_count < bed.total_count:
        bed.available_count += 1
        bed.save(update_fields=["available_count", "updated_at"])


@transaction.atomic
def transition_booking(booking: Booking, new_status: str, changed_by=None, note: str = "") -> Booking:
    """
    The only sanctioned way to change a booking's status.
    - Validates the transition is allowed from the current state
    - Locks the row (select_for_update) to prevent race conditions — e.g. two hospital admins
      confirming the same booking at the same moment, or a confirm racing a cancel
    - Adjusts bed inventory: decrements on confirm, increments when a confirmed booking ends
      (completed/cancelled/no_show) — all inside the same atomic transaction as the status
      change itself, so inventory and booking state can never drift apart even if something
      fails partway through
    - Writes an immutable BookingStatusLog entry
    """
    locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
    current_status = locked_booking.status

    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise InvalidTransitionError(
            f"Cannot move booking from '{current_status}' to '{new_status}'. "
            f"Allowed next states: {sorted(allowed) or 'none (terminal state)'}"
        )

    # --- Inventory side effects, before we commit the status change ---
    if new_status == BookingStatus.CONFIRMED:
        _decrement_bed(locked_booking.hospital_id, locked_booking.bed_type)
    elif current_status == BookingStatus.CONFIRMED and new_status in STATUSES_THAT_RELEASE_A_HELD_BED:
        _increment_bed(locked_booking.hospital_id, locked_booking.bed_type)

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
