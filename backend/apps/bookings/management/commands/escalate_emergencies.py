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
"""
from django.core.management.base import BaseCommand
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

        overdue = Booking.objects.filter(
            status=BookingStatus.REQUESTED,
            is_emergency=True,
            sla_deadline__lt=now,
        )

        if not overdue.exists():
            self.stdout.write("No overdue emergency bookings found.")
            return

        for booking in overdue:
            next_hospital = find_next_hospital(booking)
            old_hospital_name = booking.hospital.name

            if not next_hospital:
                # Nothing left to escalate to — leave it REQUESTED (still visible, still
                # SLA-expired, on the original hospital's dashboard) rather than transitioning
                # to a dead end. The patient already got an "escalated" notification attempt
                # is skipped here since there's genuinely nowhere to send them; the honest
                # thing is to say so rather than pretend progress was made.
                self.stdout.write(self.style.WARNING(
                    f"Booking {booking.id}: no alternative hospital with '{booking.bed_type}' "
                    f"availability found. Leaving at {old_hospital_name} past SLA."
                ))
                continue

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Would escalate booking {booking.id} from {old_hospital_name} "
                    f"to {next_hospital.name}"
                )
                continue

            try:
                # Step 1: mark ESCALATED against the OLD hospital — this is the audit trail
                # entry ("this hospital didn't respond in time") and triggers the "escalated"
                # notification template to the patient (Day 12's templates already cover this).
                transition_booking(
                    booking, BookingStatus.ESCALATED, changed_by=None,
                    note=f"No response from {old_hospital_name} within {EMERGENCY_BOOKING_SLA_MINUTES}min SLA.",
                )

                # Step 2: reassign to the new hospital and reset the SLA clock
                booking.previous_hospital_ids = list(booking.previous_hospital_ids or []) + [booking.hospital_id]
                booking.hospital = next_hospital
                booking.escalation_count += 1
                booking.sla_deadline = now + timezone.timedelta(minutes=EMERGENCY_BOOKING_SLA_MINUTES)
                booking.save(update_fields=["previous_hospital_ids", "hospital", "escalation_count", "sla_deadline"])

                # Step 3: back to REQUESTED — re-enters the exact same pending/alert pipeline,
                # now against the new hospital. Also triggers a fresh "requested" notification.
                transition_booking(
                    booking, BookingStatus.REQUESTED, changed_by=None,
                    note=f"Escalated to {next_hospital.name} (attempt #{booking.escalation_count + 1}).",
                )

                # Step 4: alert the NEW hospital exactly like a fresh emergency booking would —
                # without this, the new hospital would have no idea a request just landed on them.
                try:
                    notify_hospital_of_emergency(booking)
                except Exception as e:  # noqa: BLE001
                    print(f"[notification error] Failed to alert {next_hospital.name} on escalation: {e}")

                self.stdout.write(self.style.SUCCESS(
                    f"Booking {booking.id}: escalated from {old_hospital_name} to {next_hospital.name}."
                ))
            except InvalidTransitionError as e:
                self.stdout.write(self.style.ERROR(f"Booking {booking.id}: escalation failed — {e}"))
