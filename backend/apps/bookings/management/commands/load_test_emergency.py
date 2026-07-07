"""
Load-tests the actual concurrency protection built on Day 11 (select_for_update-based bed
decrement) by firing genuinely concurrent confirmation attempts — real Python threads, not
sequential clicks — against a hospital with deliberately limited bed stock. Manual UI testing
(Day 24) proves the *logic* is correct; this proves it survives real concurrency, which is
the actual risk in production when multiple hospital staff or automated processes could act
on bookings at the same moment.

Usage:
    python manage.py load_test_emergency --hospital-id 1 --bed-type icu --available 3 --concurrent 10

This will:
  1. Temporarily set the hospital's bed stock to --available
  2. Create --concurrent emergency bookings against it
  3. Fire all --concurrent confirmation attempts at the same instant via threads
  4. Report how many succeeded vs. were correctly blocked, and verify the final bed count
     is mathematically consistent (never negative, never more confirmed than stock allowed)
"""
import threading

from django.core.management.base import BaseCommand
from django.db import connections

from apps.bookings.models import Booking, BookingStatus
from apps.bookings.services import NoBedAvailableError, transition_booking
from apps.hospitals.models import BedInventory
from apps.users.models import User


class Command(BaseCommand):
    help = "Load-tests concurrent booking confirmation against limited bed stock to catch overbooking race conditions."

    def add_arguments(self, parser):
        parser.add_argument("--hospital-id", type=int, required=True)
        parser.add_argument("--bed-type", type=str, default="icu")
        parser.add_argument("--available", type=int, default=3, help="Bed stock to set before the test.")
        parser.add_argument("--concurrent", type=int, default=10, help="Number of simultaneous confirm attempts.")

    def handle(self, *args, **options):
        hospital_id = options["hospital_id"]
        bed_type = options["bed_type"]
        available = options["available"]
        concurrent = options["concurrent"]

        try:
            bed = BedInventory.objects.get(hospital_id=hospital_id, bed_type=bed_type)
        except BedInventory.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"No '{bed_type}' bed inventory found for hospital {hospital_id}. Create it first via Django admin."
            ))
            return

        patient = User.objects.filter(role="patient").first()
        if not patient:
            self.stdout.write(self.style.ERROR("No patient user found — create one first."))
            return

        # Set known starting stock for a deterministic test
        bed.total_count = max(bed.total_count, available)
        bed.available_count = available
        bed.save(update_fields=["total_count", "available_count"])

        self.stdout.write(f"Starting stock: {available} '{bed_type}' beds at hospital {hospital_id}")
        self.stdout.write(f"Creating {concurrent} bookings and confirming them all simultaneously...")

        bookings = [
            Booking.objects.create(
                patient=patient, hospital_id=hospital_id, bed_type=bed_type,
                status=BookingStatus.REQUESTED, is_emergency=True, deposit_amount=0,
            )
            for _ in range(concurrent)
        ]

        results = {"confirmed": 0, "blocked": 0, "unexpected_errors": 0}
        lock = threading.Lock()
        start_barrier = threading.Barrier(concurrent)  # forces every thread to wait until
                                                         # ALL are ready, so confirmations
                                                         # fire at genuinely the same instant
                                                         # rather than staggered one-by-one

        def confirm(booking):
            try:
                start_barrier.wait()
                transition_booking(booking, BookingStatus.CONFIRMED, changed_by=None, note="load test")
                with lock:
                    results["confirmed"] += 1
            except NoBedAvailableError:
                with lock:
                    results["blocked"] += 1
            except Exception as e:  # noqa: BLE001 — want to see genuinely unexpected failures, not just the expected block
                with lock:
                    results["unexpected_errors"] += 1
                self.stdout.write(self.style.ERROR(f"Unexpected error on booking {booking.id}: {e}"))
            finally:
                connections.close_all()  # each thread gets its own DB connection; close it
                                          # when done so they don't leak

        threads = [threading.Thread(target=confirm, args=(b,)) for b in bookings]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        bed.refresh_from_db()

        self.stdout.write("")
        self.stdout.write(f"Concurrent confirm attempts: {concurrent}")
        self.stdout.write(f"  Confirmed:          {results['confirmed']}")
        self.stdout.write(f"  Blocked (no bed):   {results['blocked']}")
        self.stdout.write(f"  Unexpected errors:  {results['unexpected_errors']}")
        self.stdout.write(f"Final available_count: {bed.available_count} (started at {available})")

        expected_final = available - results["confirmed"]

        if results["confirmed"] > available:
            self.stdout.write(self.style.ERROR(
                f"FAIL — OVERBOOKING DETECTED: {results['confirmed']} confirmed against only {available} available beds!"
            ))
        elif bed.available_count != expected_final:
            self.stdout.write(self.style.ERROR(
                f"FAIL — inventory count mismatch: expected {expected_final}, got {bed.available_count}"
            ))
        elif bed.available_count < 0:
            self.stdout.write(self.style.ERROR("FAIL — available_count went negative."))
        elif results["unexpected_errors"] > 0:
            self.stdout.write(self.style.ERROR("FAIL — unexpected errors occurred during confirmation."))
        else:
            self.stdout.write(self.style.SUCCESS(
                "PASS — no overbooking occurred, inventory count is mathematically consistent under real concurrency."
            ))
