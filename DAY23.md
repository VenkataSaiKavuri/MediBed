# Day 23 — Instant Hospital Alerts for Emergency Requests

## What's done

### Task 1 — Instant SMS + dashboard alert
- `apps/core/notifications.py` — new `notify_hospital_of_emergency()`, separate from the
  per-status patient templates (this is hospital-facing, not patient-facing). Sends an urgent SMS
  to `Hospital.phone_number` the moment an emergency booking is created, including bed type,
  condition, and patient contact info.
- `CreateEmergencyBookingSerializer.create()` now calls this alongside the existing patient
  notification — both wrapped in their own try/except so a notification failure can never delay
  or block the actual booking from being created.
- **Dashboard alert:** `BookingsDashboard.jsx` now polls for pending emergencies every 15 seconds
  (no websockets/real-time push infrastructure yet — this is the pragmatic stand-in). When the
  count goes up, it:
  - Plays a short beep (generated on the fly via the Web Audio API — no external sound file)
  - Flashes the browser tab title to "🚨 NEW EMERGENCY — MedBeds" until the admin clicks back into the tab
  - Shows a pulsing red banner at the top of the Bookings dashboard, regardless of which tab is
    open, that jumps to the Pending tab when clicked

### Task 2 — SLA timer made impossible to miss
The 15-minute emergency SLA has existed since Day 21; today it gets urgent visual treatment —
emergency bookings' countdown text pulses and stays red throughout (vs. the normal amber-then-red
progression for scheduled bookings), and refreshes twice as often (every 10s vs 30s) since minutes
matter much more here.

### Task 3 — Confirm/reject (already worked, verified today it's fast enough)
No new code — this already worked via Day 8's state machine. Today's testing focus is confirming
a hospital admin can actually notice and act within the 15-minute window using the new alerts,
not building new transition logic.

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

### Basic alert flow
1. Open the hospital admin's Bookings dashboard in one browser tab, log in
2. In a **different** browser (or incognito window), log in as a patient and submit an emergency
   booking against that same hospital
3. Within ~15 seconds, switch back to the hospital admin tab (don't click anything, just watch)
4. **Expected:** you should hear a short beep, see the browser tab title change to "🚨 NEW
   EMERGENCY — MedBeds", and see a pulsing red banner appear at the top of the page saying "🚨 1
   emergency request awaiting response!" — **even if you were sitting on the "Confirmed" or
   "Completed" tab**, not just Pending

### Banner click behavior
1. Click the red banner
2. **Expected:** switches you to the Pending tab where you can see and act on the emergency booking

### Title flash clears on focus
1. Switch away to a different browser tab/window while the title is flashing
2. Switch back
3. **Expected:** the title should revert to normal once you focus back on the tab

### Check the hospital SMS alert
1. Check your backend terminal right after submitting the emergency booking (Step 2 above)
2. **Expected:** in addition to the patient's SMS stub, you should see a second stub line
   addressed to the **hospital's** phone number, with wording like "URGENT MedBeds Alert:
   Emergency icu bed request (cardiac) from ... Respond within 15 minutes..."

### Confirm the urgent SLA styling
1. With a pending emergency booking visible, look at its countdown text
2. **Expected:** it should be red and gently pulsing (opacity fading in/out), distinct from a
   normal scheduled booking's amber static countdown

### End-to-end: actually respond within the window
1. From the alert banner, navigate to Pending, find the emergency booking
2. Click Confirm (assuming the bed/deposit conditions are met — remember emergency bookings have
   `deposit_amount = 0`, so no deposit-not-paid block applies here, unlike regular bookings)
3. **Expected:** succeeds normally, bed inventory decrements, booking moves to Confirmed — same
   state machine as every other booking, now demonstrably reachable in time thanks to the alert

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-23-emergency-alerts

git add backend/apps/core/notifications.py backend/apps/bookings/serializers.py backend/apps/bookings/views.py
git commit -m "feat(notifications): add instant SMS alert to hospital on emergency booking creation"

git add frontend/src/pages/dashboard/BookingsDashboard.jsx frontend/src/api/client.js
git commit -m "feat(frontend): live-polling emergency alert banner, beep, and title flash on hospital dashboard"

git add DAY23.md
git commit -m "docs: add Day 23 notes"

git push origin feature/day-23-emergency-alerts
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 24)
1. Auto-escalation logic (unanswered request → next hospital)
2. Escalation notification to patient
3. Test escalation chain across 3+ hospitals

This is the payoff for today's alert system — if a hospital genuinely doesn't respond within the
15-minute SLA despite every alert, the request needs to automatically move on to the next-nearest
hospital rather than leaving the patient waiting indefinitely.

Say "let's do Day 24" when ready.
