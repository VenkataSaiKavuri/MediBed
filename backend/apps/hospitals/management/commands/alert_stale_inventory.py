"""
Finds hospitals with stale bed or equipment inventory (not updated in over
WARNING_THRESHOLD_HOURS) and sends a reminder SMS to that hospital's admin staff.

Run this periodically — same pattern as Day 15/24's commands:

  Local/manual testing:
      python manage.py alert_stale_inventory

  Production: cron once daily is reasonable — inventory staleness is a slower-moving
  problem than emergency SLAs, so this doesn't need the frequent cadence those commands do.

Note: this will re-alert every stale item every time it's run, since there's no "already
alerted" tracking yet — for daily cron this is fine (one nudge per hospital per day at most
if run once daily), but running it more frequently would spam the same hospital repeatedly.
Worth adding a "last_alerted_at" timestamp if this becomes a real annoyance in practice.
"""
from django.core.management.base import BaseCommand

from apps.hospitals.models import BedInventory, Equipment, Hospital
from apps.hospitals.staleness import staleness_level
from apps.users.models import User


class Command(BaseCommand):
    help = "Alerts hospital admins whose bed/equipment inventory hasn't been updated recently."

    def handle(self, *args, **options):
        from apps.users.otp_utils import send_sms

        stale_hospital_ids = set()

        for bed in BedInventory.objects.select_related("hospital").all():
            if staleness_level(bed.updated_at) == "stale":
                stale_hospital_ids.add(bed.hospital_id)

        for equipment in Equipment.objects.select_related("hospital").all():
            if staleness_level(equipment.updated_at) == "stale":
                stale_hospital_ids.add(equipment.hospital_id)

        if not stale_hospital_ids:
            self.stdout.write("No stale inventory found across any hospital.")
            return

        alerted_count = 0
        for hospital_id in stale_hospital_ids:
            hospital = Hospital.objects.get(id=hospital_id)
            admins = User.objects.filter(hospital_id=hospital_id, role="hospital_admin")

            if not admins.exists():
                self.stdout.write(self.style.WARNING(
                    f"{hospital.name}: inventory is stale but no hospital_admin account is linked to alert."
                ))
                continue

            message = (
                f"MedBeds reminder: your bed/equipment availability at {hospital.name} hasn't "
                f"been updated in over 6 hours. Please review and update your counts so patients "
                f"see accurate availability."
            )
            for admin in admins:
                try:
                    send_sms(admin.phone_number, message)
                except NotImplementedError:
                    pass
            alerted_count += 1
            self.stdout.write(self.style.SUCCESS(f"Alerted {admins.count()} admin(s) at {hospital.name}."))

        self.stdout.write(f"Done — {alerted_count} hospital(s) alerted for stale inventory.")
