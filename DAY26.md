# Day 26 — Concurrent Load Testing, Escalation Race-Condition Fix

## What's done

### Task 2 — Fixed a real race condition (found while building this properly)
`escalate_emergencies.py` (Day 24) had a genuine bug: it read the list of overdue bookings, then
looped through computing `next_hospital` and making changes — but if the command ran twice with
overlapping timing (e.g. a slow cron cycle overlapping the next scheduled run), **both processes
could read the same booking before either had locked it**, both compute a next-hospital match from
the same stale data, and both attempt to escalate — risking a double-escalation or an incorrect
hospital assignment.

**The fix:** the command now only reads booking **IDs** upfront, then for each one, wraps the
actual escalation work in `@transaction.atomic` with `select_for_update()` — locking the row
**first**, then **re-checking** that it's still `REQUESTED` and still past its SLA deadline
*after* acquiring the lock. If another process already handled it in the meantime, this run
simply sees that and skips it cleanly — no error, no double-processing, just correct behavior
under real concurrency.

### Task 1 & 3 — Real concurrent load test
`apps/bookings/management/commands/load_test_emergency.py` (new) — this is the actual point of
today. Manual UI clicking (Day 24) proves the *logic* is right; it doesn't prove the system
survives genuine concurrency, where multiple things happen at the exact same instant rather than
quickly one after another. This command:
- Sets a hospital's bed stock to a known number
- Creates N bookings against it
- Uses a `threading.Barrier` to force all N confirmation attempts to fire at **the same instant**
  (not staggered), directly stress-testing Day 11's `select_for_update()`-based decrement logic
- Reports confirmed vs. correctly-blocked counts, and verifies the math is airtight: never more
  confirmed than available stock, never a negative count, no unexpected errors

## Run it
No new models — no migration needed.
```powershell
cd backend
venv\Scripts\activate
python manage.py runserver
```
(Keep this running in one terminal — the load test needs the DB, though it doesn't need the
dev server itself running since it's a management command, not an HTTP test. You can actually
run the load test command from a **second terminal** while the first sits idle or runs the server.)

## Test it

### The load test — this is the important one
```powershell
python manage.py load_test_emergency --hospital-id 1 --bed-type icu --available 3 --concurrent 10
```
(Replace `--hospital-id 1` with a real hospital ID from your Django admin that has an `icu` bed
inventory row — the command will create one if needed... actually it requires one to already
exist, so check Django admin first and add an `icu` row if that hospital doesn't have one.)

**Expected output**, roughly:
```
Starting stock: 3 'icu' beds at hospital 1
Creating 10 bookings and confirming them all simultaneously...

Concurrent confirm attempts: 10
  Confirmed:          3
  Blocked (no bed):   7
  Unexpected errors:  0
Final available_count: 0 (started at 3)
PASS — no overbooking occurred, inventory count is mathematically consistent under real concurrency.
```

**What would indicate a real bug:** `Confirmed: 5` (or any number > 3), or a final
`available_count` that's negative, or `FAIL` in the last line. If you see any of those, that
means Day 11's concurrency protection has an actual hole — tell me immediately, since that's a
production-critical bug, not a cosmetic one.

### Try a few different scales to build confidence
```powershell
python manage.py load_test_emergency --hospital-id 1 --bed-type icu --available 1 --concurrent 20
python manage.py load_test_emergency --hospital-id 1 --bed-type general --available 5 --concurrent 50
```
Higher concurrency ratios (way more attempts than beds) are actually a *harder* test for race
conditions to slip through, so these are worth running a few times each — race conditions don't
always reproduce on the first attempt.

### Test the escalation race-condition fix
This one's harder to trigger deliberately (it requires two overlapping command runs), but you can
at least confirm the normal single-run path still works exactly as it did on Day 24:
1. Redo Day 24's manual escalation test (backdate an emergency booking's SLA, run
   `python manage.py escalate_emergencies`)
2. **Expected:** identical behavior to before — this confirms today's rewrite didn't break the
   normal (non-racing) path while fixing the race condition

**If you want to actually simulate the race**, open two terminals and run
`python manage.py escalate_emergencies` in both at nearly the same moment against a booking you've
backdated. **Expected:** one succeeds with the escalation, the other prints nothing (silently
skips since the booking's no longer in a state needing action) — not an error, not a double-escalation.

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-26-load-testing

git add backend/apps/bookings/management/commands/escalate_emergencies.py
git commit -m "fix(bookings): close race condition in emergency escalation with lock-then-recheck pattern"

git add backend/apps/bookings/management/commands/load_test_emergency.py
git commit -m "feat(bookings): add concurrent load test for booking confirmation race conditions"

git add DAY26.md
git commit -m "docs: add Day 26 notes"

git push origin feature/day-26-load-testing
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Week 4 (Emergency Booking) now genuinely complete — Next: Week 5, Day 27
1. "Last updated" staleness indicator on bed/doctor data
2. Auto-alert hospital admin if inventory stale
3. UI polish for availability displays

Say "let's do Day 27" when ready.
