# Day 15 — No-Show Grace-Period Detection

**Note on scope:** the original plan's Day 15 was "no-show detection + auto-forfeiture + status
update." Forfeiture and the status update logic were already built on Day 13 as part of the
deposit system. Today's actual new work is the missing piece: **automatically detecting** that a
confirmed booking has gone unattended long enough to *become* a no-show, rather than requiring a
hospital admin to notice and click the button manually.

## What's done

### Task 1 — Grace period logic
- `apps/bookings/models.py` — added `confirmed_at` field, stamped automatically whenever a booking
  transitions to `confirmed` (see `services.py`). This gives us a reliable anchor point for the
  grace period even when a booking has no `scheduled_time` (e.g. "come as soon as you can" requests).
- `apps/bookings/management/commands/detect_no_shows.py` — the deadline for each confirmed booking
  is `scheduled_time` (if given) or `confirmed_at` (fallback), plus a 3-hour grace period
  (`GRACE_PERIOD_HOURS`, easy to tune).

### Task 2 — Auto-deposit forfeiture
Already working since Day 13 — nothing new needed. When the command below transitions a booking
to `no_show`, the existing `_settle_deposit()` hook in `services.py` automatically forfeits the
deposit, exactly as it would if a hospital admin clicked "Mark No-show" manually.

### Task 3 — Auto-update status to no-show
`detect_no_shows` is a **Django management command** — run manually right now, schedulable via
cron/Task Scheduler/Celery beat later once real infrastructure exists (Week 5). It:
- Finds all `confirmed` bookings
- Checks each against its calculated deadline
- Transitions overdue ones to `no_show` via the same `transition_booking()` state machine used
  everywhere else — meaning bed release and deposit forfeiture happen automatically as a side
  effect, for free, with zero special-casing
- Supports `--dry-run` to preview what would happen without actually changing anything

## Run it

**New migration needed** (confirmed_at field added):
```powershell
cd backend
venv\Scripts\activate
python manage.py makemigrations bookings
python manage.py migrate
python manage.py runserver
```

## Test it

1. Create a booking as patient, pay the deposit, confirm it as hospital_admin — note its ID
2. In Django admin, open that booking, manually edit `confirmed_at` to a time **4+ hours in the
   past** (grace period is 3 hours) → Save
3. Run a dry run first, to see what *would* happen without changing anything:
   ```powershell
   python manage.py detect_no_shows --dry-run
   ```
   You should see: `[DRY RUN] Would mark booking <id> (...) as no_show — overdue since ...`
4. Now run it for real:
   ```powershell
   python manage.py detect_no_shows
   ```
   Output: `Marked booking <id> as no_show.` then `Processed 1 overdue booking(s).`
5. Check the booking in the app (or Django admin) — status should now be `no_show`, the bed's
   `available_count` should have incremented back, and `deposit_forfeited` should be `True`
6. Check the patient's confirmation page — deposit should now show **"(forfeited)"**
7. Run the command again immediately — should print "No overdue confirmed bookings found." since
   that booking is no longer `confirmed` (it's terminal now, correctly excluded from the query)

**Test the scheduled_time path too:** create another booking with a specific `scheduled_time` set
4+ hours in the past (rather than relying on `confirmed_at`), confirm it, then run the command —
it should catch this one via the `scheduled_time` branch instead.

## Scheduling this for real (not needed today, just documented for later)
- **Windows local dev:** Task Scheduler → run `python manage.py detect_no_shows` every 15–30 min
- **Linux/production:** a cron entry, or wrap the same logic in a Celery beat periodic task once
  Celery workers are actually deployed (Week 5's infrastructure work) — the command's internal
  logic doesn't need to change at all, only how it gets triggered

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-15-no-show-detection

git add backend/apps/bookings/models.py backend/apps/bookings/migrations/ backend/apps/bookings/services.py
git commit -m "feat(bookings): stamp confirmed_at timestamp on confirmation"

git add backend/apps/bookings/management/
git commit -m "feat(bookings): add detect_no_shows management command for grace-period auto-detection"

git add backend/apps/bookings/serializers.py
git commit -m "feat(bookings): expose confirmed_at in booking API responses"

git add DAY15.md
git commit -m "docs: add Day 15 notes"

git push origin feature/day-15-no-show-detection
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 16)
1. Reputation scoring system (track cancels/no-shows per user)
2. Flag repeat offenders in DB
3. Restrict instant booking for flagged users

This is where individual no-shows start adding up to consequences — Week 3's anti-fraud layer
properly begins.

Say "let's do Day 16" when ready.
