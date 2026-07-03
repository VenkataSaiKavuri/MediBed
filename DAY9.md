# Day 9 — Patient Booking Form UI

## What's done

### Task 1 & 2 — Booking form UI, connected to backend
- `src/pages/bookings/BookingForm.jsx` (new) — patient picks bed type (only shows types with
  availability > 0), an optional preferred doctor (only on-duty ones), an optional scheduled
  time, and an optional reason. Submits via `bookingsAPI.create()` from Day 8's API.
- `src/api/client.js` — added `bookingsAPI` (create, mine, detail, hospitalList, transition)

### Task 3 — Booking confirmation screen
- `src/pages/bookings/BookingConfirmation.jsx` (new) — shown right after submitting a request.
  Shows live status (color-coded badge), booking details, and a **Cancel** button if the booking
  is still cancellable (`requested` or `confirmed` state — matches the state machine from Day 8).

### Wiring
- `HospitalDetail.jsx` — "Book a Bed Here" button now actually navigates to the booking form
  instead of showing an alert.
- `App.jsx` — new routes: `/hospitals/:hospitalId/book` and `/bookings/:id/confirmation`

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
No new models — no migration needed.

## Test the full flow

1. Log in as your **patient** account
2. Search for a hospital that has at least one bed type with `available_count > 0`
   (if none do, go set one via the hospital_admin dashboard first — remember `available_count`
   only auto-adjusts via bookings from Day 11 onward; for now you can only set it by editing a
   bed's total via Django admin directly, since the frontend form only edits `total_count`)
3. Click into the hospital → click **"Book a Bed Here"**
4. Fill the form: pick a bed type, optionally a doctor, optionally a time/reason
5. Submit → you should land on the confirmation screen showing **"Awaiting hospital confirmation"**
   with a yellow badge
6. Click **"Cancel this booking"** → confirm the dialog → status updates to "Cancelled" and the
   cancel button disappears (matches Day 8's rule: cancelled is a terminal state)

## Test the hospital side manually (dashboard UI for this comes Day 10)
Since the hospital admin's "pending requests" screen isn't built until tomorrow, confirm/reject
right now via Postman exactly like Day 8's testing:
```
PATCH http://localhost:8000/api/bookings/<id>/transition/
Authorization: Bearer <hospital_admin_token>
{ "status": "confirmed" }
```
Then refresh the patient's confirmation page in the browser — the badge should update to green
"Confirmed" and the Cancel button should still be available (confirmed bookings remain cancellable).

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-09-booking-form

git add backend
git status
# (only commit if anything backend-side actually changed — today was frontend-heavy;
#  if `git status` shows nothing under backend/, skip the backend add/commit)

git add frontend/src/pages/bookings/ frontend/src/pages/HospitalDetail.jsx frontend/src/App.jsx frontend/src/api/client.js
git commit -m "feat(frontend): patient booking form and confirmation screen"

git add DAY9.md
git commit -m "docs: add Day 9 notes"

git push origin feature/day-09-booking-form
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 10)
1. Hospital Admin "pending requests" dashboard — replaces today's manual Postman testing with a real UI
2. Accept/reject action + SLA timer logic
3. Auto-update booking status on hospital action

Say "let's do Day 10" when ready.
