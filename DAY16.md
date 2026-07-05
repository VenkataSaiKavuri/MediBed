# Day 16 — Reputation Scoring, Flagging Repeat Offenders

## What's done

### Task 1 — Reputation scoring system
`apps/core/reputation.py` (new) — `apply_reputation_change(user, delta, is_no_show=False)`:
- Score starts at 100 (set on Day 1), clamped between 0–100
- **No-show:** -20 points, `no_show_count` +1
- **Cancelling a CONFIRMED booking** (a bed was already held): -5 points — smaller penalty since
  cancelling is still the "right" behavior compared to silently no-showing, but a hospital did
  hold a real bed that went unused
- **Cancelling a merely REQUESTED booking** (never confirmed, no bed was ever held): **no
  penalty** — changing your mind before a hospital even responds is completely normal
- **Completing a stay:** +2 points — small reward for reliability

Hooked into `apps/bookings/services.py`'s `_update_reputation()`, called via the same
`transaction.on_commit()` pattern as notifications and deposit settlement — runs automatically no
matter which code path (manual admin action or the Day 15 auto-no-show detector) triggered the
status change.

### Task 2 — Flag repeat offenders
`apply_reputation_change()` auto-flags (`is_flagged = True`) whenever **either** threshold is
crossed:
- `no_show_count >= 3`, or
- `reputation_score <= 50`

Both are simple constants at the top of `reputation.py` — easy to tune later based on real usage
patterns.

### Task 3 — Restrict instant booking for flagged users
`apps/bookings/serializers.py` — `CreateBookingSerializer.validate()` now rejects booking creation
entirely for flagged users, with a clear message directing them to call the hospital directly or
contact support. `PatientDashboard.jsx` also shows a persistent warning banner if the logged-in
patient is flagged, so it's not a surprise the first time they try to book.

## Run it
```powershell
cd backend
venv\Scripts\activate
python manage.py runserver
```
```powershell
cd frontend
npm run dev
```
No new models — no migration needed (reputation fields already existed since Day 1).

## Test it

### Basic point movement
1. Create a booking, pay, confirm it, mark it completed → check that patient's `/api/auth/me/`
   response (or just watch Django admin → Users) — `reputation_score` should tick up by 2 (101
   would be clamped to 100 if already maxed)
2. Create + pay + confirm another booking, then cancel it as patient (while confirmed) → score
   drops by 5
3. Create a booking, pay, but cancel it **before** confirming (while still `requested`) → score
   should NOT change at all

### Triggering a flag via no-show count
1. Create + pay + confirm 3 separate bookings for the same test patient
2. Mark all 3 as `no_show` (either manually via Bookings dashboard, or backdate `confirmed_at` and
   run `python manage.py detect_no_shows` from Day 15 — either path works since both go through
   the same state machine)
3. Check that user in Django admin → `no_show_count` should be 3, `is_flagged` should now be `True`

### Triggering a flag via score threshold (faster path)
1. On a fresh test patient, do 3 late-cancels (confirm then cancel) — score goes 100→95→90→85...
   won't hit 50 quickly this way; no-shows are much faster (-20 each, 3 of them = -60, well past
   both thresholds). Easiest test is just the no-show path above — score AND count both trip at once.

### Confirm the restriction actually blocks booking
1. Log in as the now-flagged patient
2. Go to `/dashboard/patient` → confirm you see the red **"restricted booking privileges"** banner
3. Try to book any bed → submitting the form should fail with the same message as a validation error
4. Confirm via Postman too: `POST /api/bookings/` as this flagged patient → `400 Bad Request` with
   the restriction message

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-16-reputation-scoring

git add backend/apps/core/reputation.py
git commit -m "feat(reputation): add scoring logic and auto-flagging for repeat offenders"

git add backend/apps/bookings/services.py
git commit -m "feat(bookings): hook reputation updates into booking status transitions"

git add backend/apps/bookings/serializers.py backend/apps/users/serializers.py
git commit -m "feat(bookings): block instant booking for flagged users; expose no_show_count in profile"

git add frontend/src/pages/dashboard/PatientDashboard.jsx
git commit -m "feat(frontend): show restricted-booking warning banner for flagged patients"

git add DAY16.md
git commit -m "docs: add Day 16 notes"

git push origin feature/day-16-reputation-scoring
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 17)
1. Rate-limiting middleware (block rapid duplicate bookings) — the booking_create throttle
   scope already exists (10/hour) from Day 8; today refines this further
2. Device/IP fingerprint tracking
3. Bot-pattern detection heuristics

Say "let's do Day 17" when ready.
