# Day 24 — Auto-Escalation to the Next Hospital

This is the payoff for Day 23's alert system: if a hospital genuinely doesn't respond within the
15-minute SLA despite the SMS + dashboard alert firing correctly, the request needs to move on
automatically rather than leaving a patient waiting indefinitely on a hospital that isn't answering.

## What's done

### Task 1 — Auto-escalation logic
- `apps/bookings/services.py` — `ALLOWED_TRANSITIONS` updated so `ESCALATED` can move back to
  `REQUESTED`. `ESCALATED` is intentionally transient: it exists mainly as an audit-log marker
  ("this hospital didn't respond in time") before immediately re-entering the exact same
  pending/alert/SLA pipeline against the newly-assigned hospital.
- `apps/hospitals/matching.py` (new) — refactored Day 22's distance logic into
  `find_ranked_hospitals()` (shared with the `/nearest/` API endpoint, so there's exactly one
  definition of "best hospital match" in the whole codebase) and `find_next_hospital(booking)`,
  which excludes the current hospital plus every hospital already tried for this specific booking.
- `apps/bookings/management/commands/escalate_emergencies.py` (new) — the actual escalation job:
  finds overdue emergency bookings, reassigns to the next-nearest hospital with real availability,
  resets the SLA clock, and alerts the new hospital exactly like a fresh emergency booking would.
  If no alternative hospital exists, it honestly leaves the booking as-is rather than pretending
  progress was made — logged as a warning for visibility.

### Task 2 — Escalation notification to patient
Reuses Day 12's existing `"escalated"` notification template — no new notification code needed,
since the template ("we're finding you another hospital now") was already written back then in
anticipation of this. The patient also gets a fresh `"requested"` notification once reassigned to
the new hospital.

### Task 3 — Test the escalation chain
See below — this needs at least 3 verified hospitals with real availability and distinct
coordinates to properly exercise a multi-hop escalation chain.

### Tracking fields added
- `Booking.escalation_count` — how many times this booking has bounced between hospitals
- `Booking.previous_hospital_ids` — every hospital already tried, so the same one is never
  offered twice for the same booking

### Frontend
- `BookingConfirmation.jsx` — shows "Escalated N times" when applicable, and now **polls every
  10 seconds** while an emergency booking is still `requested`/`escalated`, since escalation
  happens entirely server-side — a patient shouldn't need to manually refresh mid-emergency to
  see their request moved to a new hospital

## Run it

**New migration needed** (`escalation_count`, `previous_hospital_ids` fields):
```powershell
cd backend
venv\Scripts\activate
python manage.py makemigrations bookings
python manage.py migrate
python manage.py runserver
```

## Test it

### Set up for a real multi-hop chain
You need **3 verified hospitals** with distinct lat/long coordinates and available stock for the
same bed type (e.g. all three have `icu` beds available). This mirrors Day 22's setup.

### Trigger and force an escalation
1. As patient, submit an emergency booking — note which hospital it landed on (the nearest one)
2. In Django admin, open that booking, manually set `sla_deadline` to a time **in the past**
3. Run the escalation command:
   ```powershell
   python manage.py escalate_emergencies --dry-run
   ```
   **Expected:** `[DRY RUN] Would escalate booking <id> from <Hospital A> to <Hospital B>`
4. Run it for real:
   ```powershell
   python manage.py escalate_emergencies
   ```
   **Expected:** `Booking <id>: escalated from <Hospital A> to <Hospital B>.`

### Verify the booking actually moved
1. Check that booking in Django admin — `hospital` should now be **Hospital B** (the next-nearest
   with stock), `escalation_count` = 1, `previous_hospital_ids` = `[<Hospital A's id>]`
2. Check `sla_deadline` — should be freshly reset to ~15 minutes from now, not still expired
3. Check the `status_logs` — should show `requested → escalated` (with a note about Hospital A not
   responding) followed by `escalated → requested` (with a note about the new assignment)

### Confirm Hospital B actually gets alerted
Check your backend terminal from the escalation run — you should see a fresh
`[SMS STUB] To: <Hospital B's phone>...` alert, exactly like a brand-new emergency booking would
generate, plus the patient's own "escalated" and "requested" SMS stubs.

### Confirm the patient sees it without refreshing
1. Keep the patient's confirmation page open in a browser tab from before the escalation
2. Run the escalation command in a terminal
3. Within ~10 seconds (without touching the browser), the page should auto-update to show the new
   status and hospital

### Test a full multi-hop chain (3 hospitals)
1. Repeat the "backdate + run command" cycle on the same booking two more times
2. Each time, it should escalate to a **different** hospital (never repeating one already tried)
3. After exhausting all 3, run the command once more
4. **Expected:** `Booking <id>: no alternative hospital with 'icu' availability found. Leaving at
   <Hospital C> past SLA.` — confirms it correctly recognizes when there's genuinely nowhere left
   to send the request, rather than looping or crashing

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-24-auto-escalation

git add backend/apps/bookings/models.py backend/apps/bookings/migrations/ backend/apps/bookings/services.py
git commit -m "feat(bookings): add escalation tracking fields, allow ESCALATED->REQUESTED transition"

git add backend/apps/hospitals/matching.py backend/apps/hospitals/views.py
git commit -m "refactor(hospitals): extract shared nearest-hospital matching logic"

git add backend/apps/bookings/management/commands/escalate_emergencies.py
git commit -m "feat(bookings): add auto-escalation command for unanswered emergency requests"

git add backend/apps/bookings/serializers.py
git commit -m "feat(bookings): expose escalation tracking fields in API"

git add frontend/src/pages/bookings/BookingConfirmation.jsx
git commit -m "feat(frontend): show escalation history and auto-poll emergency booking status"

git add DAY24.md
git commit -m "docs: add Day 24 notes"

git push origin feature/day-24-auto-escalation
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Week 4 (emergency booking) complete — Next: Week 5, Day 27
1. "Last updated" staleness indicator on bed/doctor data
2. Auto-alert hospital admin if inventory stale
3. UI polish for availability displays

(Days 25-26 in the original plan were emergency audit logging — already substantially covered
since Day 1's device_id/ip_address/geolocation fields — and a full emergency-flow simulation test
pass, which today's multi-hop chain test above largely already covers.)

Say "let's do Day 27" when ready — or "let's do Day 25" if you'd like a dedicated pass on
emergency audit logging and fraud review first.
