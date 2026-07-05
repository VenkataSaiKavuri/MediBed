"""
Detects confirmed bookings whose patient never showed up, and auto-transitions them to
no_show — which in turn (via the existing state machine hooks) auto-releases the bed back
to inventory and forfeits the deposit. Run this periodically:

  Local/manual testing:
      python manage.py detect_no_shows

  Production scheduling (pick one):
      - Cron (Linux) / Task Scheduler (Windows): run the command above every 15-30 min
      - Celery beat: wrap this same logic in a periodic task once Celery workers are
        actually deployed (Week 5) — the logic itself doesn't need to change, just how
        it's triggered.

A booking is considered overdue once GRACE_PERIOD_HOURS have passed since either its
scheduled_time (if the patient specified one) or its confirmed_at timestamp (fallback for
bookings with no specific scheduled time — i.e. "come as soon as you can").
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatus
from apps.bookings.services import InvalidTransitionError, transition_booking

GRACE_PERIOD_HOURS = 3


def get_no_show_deadline(booking: Booking):
    anchor = booking.scheduled_time or booking.confirmed_at
    if not anchor:
        return None  # Shouldn't happen for a confirmed booking, but don't crash if data is odd
    return anchor + timedelta(hours=GRACE_PERIOD_HOURS)


class Command(BaseCommand):
    help = "Auto-marks overdue confirmed bookings as no-show, releasing their bed and forfeiting the deposit."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be marked no-show without actually changing anything.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()
        confirmed_bookings = Booking.objects.filter(status=BookingStatus.CONFIRMED)

        overdue = []
        for booking in confirmed_bookings:
            deadline = get_no_show_deadline(booking)
            if deadline and now > deadline:
                overdue.append(booking)

        if not overdue:
            self.stdout.write("No overdue confirmed bookings found.")
            return

        for booking in overdue:
            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Would mark booking {booking.id} ({booking.patient}) as no_show "
                    f"— overdue since {get_no_show_deadline(booking)}"
                )
                continue

            try:
                transition_booking(
                    booking,
                    BookingStatus.NO_SHOW,
                    changed_by=None,
                    note=f"Auto-marked no-show after {GRACE_PERIOD_HOURS}h grace period expired.",
                )
                self.stdout.write(self.style.SUCCESS(f"Marked booking {booking.id} as no_show."))
            except InvalidTransitionError as e:
                # Shouldn't normally happen (we only queried CONFIRMED bookings, and
                # CONFIRMED -> NO_SHOW is always allowed), but don't let one bad row crash the run
                self.stdout.write(self.style.WARNING(f"Skipped booking {booking.id}: {e}"))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"Processed {len(overdue)} overdue booking(s)."))
