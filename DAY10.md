# Day 10 — Hospital Admin Pending Requests Dashboard

## What's done

### Backend (Task 2 support)
- `apps/bookings/serializers.py` — `CreateBookingSerializer` now actually sets `sla_deadline`
  (2 hours from creation, matching the original plan's Day 10 spec) when a booking is created.
  This field existed on the model since Day 1 but was never populated until now.

### Frontend (Tasks 1, 2, 3)
- `BookingsDashboard.jsx` (new) — the real pending-requests screen, replacing yesterday's Postman
  workaround:
  - Tabs: **Pending** / **Confirmed** / **Completed** / **All**
  - Each booking card shows patient name/phone, bed type, doctor, reason, and a **live SLA
    countdown** for pending requests (updates every 30s, turns red and reads "SLA expired" once
    the 2-hour window passes — note: nothing *automatically* happens when it expires yet, that's
    Day 24's auto-escalation logic; today it's just a visible warning to the admin)
  - **Confirm/Reject** buttons on pending requests, **Mark Completed / Mark No-show** buttons on
    confirmed ones — each calls the same `transition_booking()` state machine from Day 8
- `HospitalAdminDashboard.jsx` — added a "📋 View Booking Requests" link
- `App.jsx` — new route `/dashboard/hospital-admin/bookings`

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
No new models — no migration needed (sla_deadline field already existed).

## Test it

1. **As a patient**, create a fresh booking request (like Day 9's test) so you have something in "Pending"
2. **Log out, log in as hospital_admin**
3. On the hospital admin dashboard, click **"📋 View Booking Requests"**
4. You should see your booking under the **Pending** tab, with an SLA countdown like "1h 58m left"
5. Click **✓ Confirm** — the booking should move out of Pending; switch to the **Confirmed** tab to find it there
6. Click **✓ Mark Completed** on it — it should now appear under **Completed**
7. Switch back to your **patient** browser session, refresh the booking confirmation page — status
   should reflect each change in real time (well, on refresh — live push updates aren't built yet)

**Test reject too:** create a second booking as patient, reject it as admin, confirm it disappears
from Pending and shows "rejected" status if you check the patient's booking confirmation page.

**Test the SLA countdown is honest:** you can temporarily edit a booking's `sla_deadline` in Django
admin to a time in the past, then reload the Bookings dashboard — the countdown should immediately
show "SLA expired" in red instead of counting down.

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-10-pending-requests

git add backend/apps/bookings/serializers.py
git commit -m "feat(bookings): set SLA deadline on booking creation"

git add frontend/src/pages/dashboard/BookingsDashboard.jsx frontend/src/pages/dashboard/HospitalAdminDashboard.jsx frontend/src/App.jsx
git commit -m "feat(frontend): hospital admin pending-requests dashboard with SLA countdown"

git add DAY10.md
git commit -m "docs: add Day 10 notes"

git push origin feature/day-10-pending-requests
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 11)
1. Auto-decrement bed count on booking confirm
2. Auto-increment bed count on cancel/discharge
3. Test inventory sync across multiple bookings

This is the day the fake-availability problem starts getting solved for real — bed counts will
finally move automatically instead of needing manual admin updates.

Say "let's do Day 11" when ready.
