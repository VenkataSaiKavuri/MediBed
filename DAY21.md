# Day 21 — One-Tap Emergency Booking

**Week 4 begins.** Everything from Weeks 1–3 was the scheduled/non-emergency booking path with
full fraud protection layered on. Today builds the other half of the original problem statement:
a deliberately faster, lower-friction path for genuine emergencies.

## The trade-off, stated plainly
`CreateEmergencyBookingSerializer` intentionally skips:
- **ID document requirement** (Day 18) — no time for that when it's urgent
- **Flagged-user block** (Day 16) — a fraud flag on someone's account shouldn't be able to delay
  emergency care; the platform accepts higher fraud risk here in exchange for speed
- **Duplicate-active-booking check** (Day 17) — someone in crisis might reasonably try multiple
  hospitals at once if the first is slow to respond
- **Deposit collection** (Day 13) — zero payment friction in an emergency flow

Everything is still logged (device_id, IP, geolocation, condition category) for **post-hoc**
fraud review — the original plan's explicit design: speed now, audit later, never the reverse.

## What's done

### Task 1 — One-tap UI
The "🚨 Emergency Booking" button on the patient dashboard (previously just an alert stub) now
navigates to `/emergency` — a real, focused flow: pick what's happening, pick a bed type, pick a
hospital, submit. No multi-step form, no doctor selection, no scheduling.

### Task 2 — Condition category + live location
- Five quick-tap condition buttons: cardiac, trauma, respiratory, maternity, other
- Browser geolocation is requested **immediately on page load** (not after some other action) —
  every second matters, so there's no reason to wait
- Location capture failing (permission denied, unsupported browser) doesn't block submission —
  it's captured on a best-effort basis, shown as a status line, never a hard requirement

### Task 3 — Emergency booking API skipping heavy KYC
- `POST /api/bookings/emergency/` — separate endpoint, separate serializer, separate (looser)
  throttle scope (`emergency_booking`, 5/hour — this throttle scope has existed since Day 1's
  settings but was unused until today)
- `is_emergency = True`, `deposit_amount = 0`, shorter SLA (**15 minutes** vs. 2 hours for
  scheduled bookings) — the actual auto-escalation logic that *acts* on this shorter SLA is
  Day 24's job; today just sets the deadline
- Booking still goes through the same `transition_booking()` state machine for everything after
  creation — confirm/reject/complete all work identically to a normal booking from here on

### Honest gap, deliberately deferred to Day 22
The hospital picker today is just an alphabetical list of all verified hospitals — **not**
sorted by actual distance. Real nearest-hospital geolocation matching is explicitly Day 22's task.
Today's UI captures the location and shows a note saying so, rather than pretending to do
something it doesn't yet do.

## Run it
No new models — no migration needed.
```powershell
cd backend
venv\Scripts\activate
python manage.py runserver
```
```powershell
cd frontend
npm run dev
```

## Test it

1. As patient, click **"🚨 Emergency Booking"** on the dashboard
2. Your browser should prompt for location permission — allow it
3. **Expected:** within a few seconds, the page shows "📍 Location captured" in green
4. Tap a condition (e.g. "🫀 Cardiac"), pick a bed type, pick a hospital
5. Click **"Send Emergency Request"**
6. **Expected:** lands on the confirmation screen, showing a red **"🚨 EMERGENCY"** badge, no
   deposit-payment step at all (compare this to the normal booking flow from Day 9/13, which
   always stops at a deposit screen first — emergency skips straight through)
7. Check that booking in Django admin — `is_emergency = True`, `deposit_amount = 0`,
   `sla_deadline` should be about 15 minutes from creation (much shorter than a normal booking's 2 hours)
8. As hospital_admin, go to Bookings dashboard — that booking should show the red 🚨 EMERGENCY
   tag right on its card

### Confirm the "skip fraud checks" trade-offs actually work
1. Take a patient account you flagged back on Day 16 (still flagged, or re-flag one)
2. Try a **normal** booking as this patient → should be blocked (Day 16's restriction)
3. Try an **emergency** booking as this same patient → should succeed anyway, confirming the
   flagged-user block is correctly bypassed for emergencies
4. Similarly, try creating 2 emergency bookings for the same hospital+bed-type back to back →
   should both succeed (no duplicate-block), unlike the regular booking flow from Day 17

### Location denial doesn't block submission
1. Deny the location permission prompt (or test in a browser/context where geolocation fails)
2. **Expected:** page shows a location error message but the rest of the form still works — you
   can still submit successfully without it

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-21-emergency-booking

git add backend/apps/bookings/serializers.py backend/apps/bookings/views.py backend/apps/bookings/urls.py
git commit -m "feat(bookings): add emergency booking endpoint that skips KYC checks for speed"

git add frontend/src/pages/bookings/EmergencyBooking.jsx frontend/src/pages/dashboard/PatientDashboard.jsx frontend/src/pages/dashboard/BookingsDashboard.jsx frontend/src/pages/bookings/BookingConfirmation.jsx frontend/src/App.jsx frontend/src/api/client.js
git commit -m "feat(frontend): one-tap emergency booking flow with condition selector and geolocation"

git add DAY21.md
git commit -m "docs: add Day 21 notes"

git push origin feature/day-21-emergency-booking
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 22)
1. Geolocation-based nearest-hospital query
2. Filter by live emergency bed availability
3. Return ranked hospital list (distance + availability)

This replaces today's plain alphabetical hospital dropdown with the real thing — sorted by actual
distance from the patient's captured location, filtered to only hospitals with real availability
for the requested bed type right now.

Say "let's do Day 22" when ready.
