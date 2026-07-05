# Day 17 — Duplicate Booking Prevention, Device/IP Fingerprinting, Bot Heuristics

## What's done

### Task 1 — Rate-limiting refinement: hard duplicate-booking block
The existing 10/hour throttle (Day 8) limits *volume* but doesn't stop someone from creating 5
separate requests for the **same bed at the same hospital** before the first one even gets a
response — all 5 comfortably fit under an hourly limit.

`apps/bookings/fraud_detection.py` — `has_duplicate_active_booking()` checks whether the patient
already has an unresolved (`requested`/`confirmed`/`escalated`) booking for that exact
hospital + bed type combination, and `CreateBookingSerializer.validate()` now **hard-blocks**
creation if so, with a clear message telling them to cancel the existing one first.

### Task 2 — Device/IP fingerprint tracking
`detect_device_ip_sharing()` — checks how many **distinct patient accounts** have used the same
`device_id` or `ip_address` in the last 24 hours. Crossing the threshold (3 accounts) is a
**soft signal**, not a block — flagged for review, since a shared family device or hospital kiosk
can trigger this completely legitimately.

### Task 3 — Bot-pattern detection heuristics
`detect_rapid_fire()` — flags (soft signal again) if the same device has created 3+ bookings
within a 5-minute window. Both this and the device-sharing check run in
`evaluate_soft_fraud_signals()`, called right after a booking is created; results are stored on
the booking itself (`is_suspicious`, `fraud_flags` — a list of human-readable reason strings).

**Deliberately soft, not hard, rules:** none of Day 17's fraud signals block a booking outright —
they flag it for a human (platform admin, Day 19's dashboard) to judge. Auto-blocking on these
would risk locking out entirely legitimate cases (a family member booking beds for several
relatives during a real emergency looks identical to "bot pattern" from the system's point of view).

### Where flags currently surface
Since the platform admin fraud dashboard doesn't exist yet (Day 19), flagged bookings are visible
right now only via **Django admin** — `is_suspicious` is a filterable column, `fraud_flags` and
the device/IP fields are visible on the booking detail page. Not exposed in the patient/hospital
API responses, so as not to tip off anyone gaming the system about exactly what's being watched.

## Run it

**New migration needed** (`is_suspicious`, `fraud_flags` fields added):
```powershell
cd backend
venv\Scripts\activate
python manage.py makemigrations bookings
python manage.py migrate
python manage.py runserver
```

## Test it

### Duplicate booking block
1. As patient, create a booking for a specific hospital + bed type, pay the deposit (leave it
   `requested`, don't get it confirmed yet)
2. Try to create **another** booking for the exact same hospital + bed type
3. **Expected:** `400 Bad Request` — *"You already have an active request for this bed type at
   this hospital. Cancel it first..."*
4. Cancel the first one, then retry — should succeed now

### Device/IP sharing signal
This needs 3+ different patient accounts booking from what looks like the same device/IP. Since
your browser sends a consistent IP locally, the IP-based check is the easiest to trigger:
1. Create 3 different patient accounts (or reuse existing test ones)
2. Have each create a booking (different hospitals/bed types so they don't hit the duplicate block)
   within the same 24-hour window — which they will be, since you're testing right now
3. Check the 3rd (or later) booking in Django admin

**Expected:** `is_suspicious = True`, `fraud_flags` shows something like `["IP address used by 3
distinct accounts in 24h"]`

**Note:** since you're testing everything from one machine, this will likely trigger very easily
and often — that's expected in local dev. In production with real diverse users, this would only
fire for genuinely unusual concentration.

### Rapid-fire signal
1. As one patient, create 3 bookings for **different** hospitals/bed types (to dodge the duplicate
   block) within about a minute of each other
2. Check the 3rd booking in Django admin

**Expected:** `fraud_flags` includes something like `["3 bookings from this device in 5 minutes"]`
(note: `device_id` is currently only populated if the frontend sends an `X-Device-Id` header,
which isn't wired up yet — see the gap noted below)

## Known gap, noted for later
The frontend doesn't currently send a real `X-Device-Id` header — `device_id` will be blank for
all bookings created through the UI right now, meaning the device-sharing and rapid-fire checks
won't have anything to key off of until that's wired up. The **IP-based** signal still works
today since `ip_address` is captured automatically from the request. Adding a real device
fingerprint (e.g. a generated UUID stored in localStorage, similar to Day 12's `dev_fcm_token`
pattern) is a natural small addition — flagging it here rather than fixing it now to keep today's
scope to what was actually planned.

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-17-fraud-heuristics

git add backend/apps/bookings/models.py backend/apps/bookings/migrations/
git commit -m "feat(bookings): add is_suspicious and fraud_flags fields"

git add backend/apps/bookings/fraud_detection.py
git commit -m "feat(bookings): add duplicate-booking hard rule and device/IP soft fraud signals"

git add backend/apps/bookings/serializers.py
git commit -m "feat(bookings): wire fraud detection into booking creation"

git add backend/apps/bookings/admin.py
git commit -m "feat(admin): surface fraud signals in Django admin"

git add DAY17.md
git commit -m "docs: add Day 17 notes"

git push origin feature/day-17-fraud-heuristics
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 18)
1. ID upload (Aadhaar/passport) for non-emergency bookings
2. Basic name-match verification
3. Encrypted ID storage

Say "let's do Day 18" when ready.
