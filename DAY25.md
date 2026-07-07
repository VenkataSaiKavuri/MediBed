# Day 25 — Emergency Audit Logging, Post-Hoc Fraud Review

## A real gap found and fixed while building this properly
While implementing today's task, I found that **emergency bookings never actually ran through
Day 17's fraud-signal detection** — `evaluate_soft_fraud_signals()` existed and was imported into
`serializers.py`, but nothing ever called it for the emergency path. That's a genuine oversight
from Day 21, not a deliberate design choice — fixed today.

## What's done

### Task 2 — Post-hoc fraud review flag (built first, since it's the core fix)
`CreateEmergencyBookingSerializer.create()` now runs `evaluate_soft_fraud_signals()` (device/IP
sharing, rapid-fire detection — the same Day 17 checks regular bookings get) right after an
emergency booking is created. If a signal fires, `is_suspicious` and `fraud_flags` get set exactly
like a regular booking would.

**Deliberately NOT force-flagging every emergency as suspicious** — an earlier draft of today's
work did that, but it would've flooded the existing "Suspicious Bookings" tab (meant for actual
fraud signals) with every routine emergency, diluting its usefulness. Instead:
- `is_suspicious` keeps its precise meaning: "a heuristic actually fired"
- **Every** emergency booking — flagged or not — is separately reviewable via Task 3's dedicated
  audit log, since the whole point of post-hoc review is accountability for bypassing real-time
  checks, not just catching the ones that happen to trip a heuristic

### Task 1 — Emergency audit log
Nothing new needed here structurally — `device_id`, `ip_address`, `patient_latitude/longitude`,
and full `status_logs` history have existed since Day 1/8. Today's real work was making sure this
data is actually **assembled and visible** in one place (Task 3), not scattered across Django admin.

### Task 3 — Admin view for emergency logs
New **"Emergency Audit Log"** tab on the Platform Admin dashboard — `GET /api/admin-panel/emergency-audit/`
lists every emergency booking, most recent first, showing:
- Patient, current hospital, condition, bed type, status
- Full escalation chain (previous hospitals tried + escalation count, from Day 24)
- Device ID, IP address, captured geolocation
- Fraud flags, if any fired
- A red "⚠ Flagged" tag for anything Day 17's heuristics caught

## Run it
No new models — no migration needed (all fields used today already existed).
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

### Confirm the fraud-signal gap is actually fixed
1. Create 3 emergency bookings from 3 different patient accounts within a short window (same
   approach as Day 17's IP-sharing test — since you're testing from one machine, your IP is shared)
2. Check the 3rd emergency booking in Django admin

**Expected:** `is_suspicious = True`, `fraud_flags` shows something like `["IP address used by 3
distinct accounts in 24h"]` — this **wasn't happening before today's fix**; emergency bookings
were completely invisible to fraud detection until now.

### Test the new Emergency Audit Log tab
1. Log in as platform_admin, go to the dashboard
2. Click **"Emergency Audit Log"**
3. **Expected:** every emergency booking you've created across Days 21-24's testing should appear
   here, most recent first, each showing device/IP/location and current status
4. Find one that went through escalation (from Day 24's testing) — **Expected:** it shows
   "Previously tried: <Hospital A>" and "(1 escalation)" or however many hops it went through
5. Find the ones flagged from the test above — **Expected:** red "⚠ Flagged" tag visible, with
   the specific fraud_flags reason shown below

### Confirm normal (non-emergency) suspicious bookings still work correctly
Go to the "Suspicious Bookings" tab — should still show only regular bookings with actual Day 17
signals, same as before. Confirms the two tabs serve genuinely different purposes now: one for
"something looked off," one for "this bypassed checks by design, here's the full record regardless."

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-25-emergency-audit

git add backend/apps/bookings/serializers.py
git commit -m "fix(bookings): run fraud-signal detection on emergency bookings (was never wired in)"

git add backend/apps/core/fraud_serializers.py backend/apps/core/fraud_views.py backend/apps/core/urls.py
git commit -m "feat(admin): add emergency audit log endpoint with full device/IP/escalation trail"

git add frontend/src/pages/dashboard/PlatformAdminDashboard.jsx frontend/src/api/client.js
git commit -m "feat(frontend): add Emergency Audit Log tab to platform admin dashboard"

git add DAY25.md
git commit -m "docs: add Day 25 notes"

git push origin feature/day-25-emergency-audit
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 26)
1. Full emergency flow simulation (multiple concurrent requests)
2. Fix timing/escalation bugs
3. Load-test emergency matching logic

Say "let's do Day 26" when ready — or "let's do Day 27" to move into Week 5 if you're satisfied
Day 24's multi-hop escalation test already substantially covered today's simulation goals.
