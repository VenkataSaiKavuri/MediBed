"""
Auto-escalates emergency bookings that a hospital hasn't responded to within the SLA
(15 minutes, set at creation on Day 21) to the next-nearest hospital with availability.

Run this periodically — same scheduling approach as Day 15's detect_no_shows:

  Local/manual testing:
      python manage.py escalate_emergencies

  Production: cron every 1-2 minutes, or a Celery beat periodic task once Celery workers
  are actually deployed (Week 5). Given the 15-minute SLA, this needs to run far more
  frequently than detect_no_shows' 15-30 minute cadence — an emergency escalation check
  running only every 30 minutes would defeat the point entirely.

Day 26 fix: the per-booking escalation work is now wrapped in select_for_update + a
re-check of conditions AFTER acquiring the lock. Without this, two overlapping runs of
this command (e.g. a slow cron cycle overlapping the next one) could both read the same
overdue booking, both compute a "next hospital" from the same stale previous_hospital_ids,
and both attempt to escalate it — potentially double-escalating or skipping a hospital
that should have been tried. Locking the row first and re-validating means the second
run will simply see the booking is no longer overdue (or already escalated) and skip it
cleanly instead of racing the first run.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatus
from apps.bookings.serializers import EMERGENCY_BOOKING_SLA_MINUTES
from apps.bookings.services import InvalidTransitionError, transition_booking
from apps.core.notifications import notify_hospital_of_emergency
from apps.hospitals.matching import find_next_hospital


class Command(BaseCommand):
    help = "Escalates emergency bookings past their SLA deadline to the next-nearest hospital with availability."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview without making changes.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()

        # Just the IDs here — the actual row gets locked and re-fetched fresh inside the
        # per-booking transaction below, since this initial queryset can go stale the moment
        # another process (or another run of this same command) touches a row.
        overdue_ids = list(
            Booking.objects.filter(
                status=BookingStatus.REQUESTED,
                is_emergency=True,
                sla_deadline__lt=now,
            ).values_list("id", flat=True)
        )

        if not overdue_ids:
            self.stdout.write("No overdue emergency bookings found.")
            return

        for booking_id in overdue_ids:
            if dry_run:
                self._preview(booking_id)
            else:
                self._escalate_one(booking_id, now)

    def _preview(self, booking_id):
        booking = Booking.objects.filter(pk=booking_id).first()
        if not booking or booking.status != BookingStatus.REQUESTED:
            return  # already handled by a previous iteration/run since the dry-run started
        next_hospital = find_next_hospital(booking)
        if next_hospital:
            self.stdout.write(
                f"[DRY RUN] Would escalate booking {booking.id} from {booking.hospital.name} "
                f"to {next_hospital.name}"
            )
        else:
            self.stdout.write(
                f"[DRY RUN] Booking {booking.id}: no alternative hospital found, would stay at {booking.hospital.name}"
            )

    @transaction.atomic
    def _escalate_one(self, booking_id, now):
        # Lock the row FIRST, then re-check every condition — this is what actually closes
        # the race window described in the module docstring above.
        try:
            booking = Booking.objects.select_for_update().get(pk=booking_id)
        except Booking.DoesNotExist:
            return

        if booking.status != BookingStatus.REQUESTED or booking.sla_deadline >= now:
            # Another process already escalated/resolved this booking between when we
            # listed it as overdue and when we got the lock — nothing to do, not an error.
            return

        old_hospital_name = booking.hospital.name
        next_hospital = find_next_hospital(booking)

        if not next_hospital:
            self.stdout.write(self.style.WARNING(
                f"Booking {booking.id}: no alternative hospital with '{booking.bed_type}' "
                f"availability found. Leaving at {old_hospital_name} past SLA."
            ))
            return

        try:
            transition_booking(
                booking, BookingStatus.ESCALATED, changed_by=None,
                note=f"No response from {old_hospital_name} within {EMERGENCY_BOOKING_SLA_MINUTES}min SLA.",
            )

            booking.previous_hospital_ids = list(booking.previous_hospital_ids or []) + [booking.hospital_id]
            booking.hospital = next_hospital
            booking.escalation_count += 1
            booking.sla_deadline = now + timezone.timedelta(minutes=EMERGENCY_BOOKING_SLA_MINUTES)
            booking.save(update_fields=["previous_hospital_ids", "hospital", "escalation_count", "sla_deadline"])

            transition_booking(
                booking, BookingStatus.REQUESTED, changed_by=None,
                note=f"Escalated to {next_hospital.name} (attempt #{booking.escalation_count + 1}).",
            )

            try:
                notify_hospital_of_emergency(booking)
            except Exception as e:  # noqa: BLE001
                print(f"[notification error] Failed to alert {next_hospital.name} on escalation: {e}")

            self.stdout.write(self.style.SUCCESS(
                f"Booking {booking.id}: escalated from {old_hospital_name} to {next_hospital.name}."
            ))
        except InvalidTransitionError as e:
            self.stdout.write(self.style.ERROR(f"Booking {booking.id}: escalation failed — {e}"))
