# Day 8 — Booking State Machine, Bookings API, DB Relations

## What's done

### Task 1 — State machine
- `apps/bookings/services.py` — the real core of today's work. `transition_booking()` is now the
  **only** sanctioned way to change a booking's status anywhere in the codebase. It:
  - Validates the move against `ALLOWED_TRANSITIONS` (e.g. you can't jump `requested → completed`
    directly — it must pass through `confirmed` first)
  - Locks the row with `select_for_update()` inside a DB transaction, so two admins can't both
    confirm the same booking at the same instant and cause a double-decrement later (Day 11)
  - Writes an immutable `BookingStatusLog` row every time — this is your audit trail for disputes

### Task 2 — Bookings API
- `apps/bookings/serializers.py` — `CreateBookingSerializer` (patient books), `BookingSerializer`
  (full read view with patient/hospital/doctor names resolved, plus the status log), `TransitionBookingSerializer`
- `apps/bookings/views.py`:
  - `POST /api/bookings/` — patient creates a booking (rate-limited: 10/hour, anti-spam)
  - `GET /api/bookings/mine/` — patient's own booking history
  - `GET /api/bookings/hospital/` — hospital admin's bookings for their hospital (optional `?status=requested` filter)
  - `GET /api/bookings/<id>/` — detail, access-controlled (only the patient who booked it or that hospital's staff)
  - `PATCH /api/bookings/<id>/transition/` — the status-change endpoint. **Role matters here on
    top of the state machine**: a patient can only ever move a booking to `cancelled`; hospital
    staff can move it to `confirmed`/`rejected`/`completed`/`no_show`. Even if the state machine
    would technically allow a transition, the role check blocks it if it's not that role's job to
    make that call.

### Task 3 — DB relations
Already built on Day 1, confirmed correct today:
- `Booking.patient` → User (who's booking)
- `Booking.hospital` → Hospital (where)
- `Booking.doctor` → Doctor, nullable (optional — not every booking needs a specific doctor)
- `Booking.bed_type` → a string matching `BedInventory.bed_type`, **not a foreign key to a specific
  BedInventory row**. This is deliberate: bed types are a shared vocabulary
  (general/icu/ventilator/etc), and Day 11's inventory adjustment will look up
  `BedInventory.objects.get(hospital=booking.hospital, bed_type=booking.bed_type)` at transition time.

## Run it
```powershell
cd backend
venv\Scripts\activate
python manage.py runserver
```
No new models today — the Booking model existed since Day 1 and its migration was already applied
back then. No `makemigrations`/`migrate` needed.

## Test it (via Django admin + a REST client, since there's no UI yet — that's Day 9)

You can test with `curl`, Postman, or Django admin directly. Quickest is Django admin for now:

1. Go to `http://localhost:8000/admin/` → **Bookings** → **Add**
   - This lets you manually create a booking to inspect the shape, but note: **manually saving in
     Django admin bypasses the state machine** (it just sets the field directly). Use the API for
     real transition testing.

2. **Test via API** (use Postman, Insomnia, or `curl` with your patient's JWT access token):
   ```
   POST http://localhost:8000/api/bookings/
   Authorization: Bearer <patient_access_token>
   Content-Type: application/json

   {
     "hospital": 1,
     "bed_type": "icu",
     "condition_category": "cardiac observation"
   }
   ```
   Should return `201` with `"status": "requested"`.

3. **Try an invalid transition** — as hospital staff, try jumping straight to `completed` on a
   freshly requested booking:
   ```
   PATCH http://localhost:8000/api/bookings/1/transition/
   Authorization: Bearer <hospital_admin_access_token>
   { "status": "completed" }
   ```
   Should return `400` with a message like `"Cannot move booking from 'requested' to 'completed'"`
   — this confirms the state machine is actually enforcing order, not just accepting anything.

4. **Try the correct sequence**: `requested → confirmed` (as hospital_admin), then `confirmed → completed`.
   Both should succeed. Check `GET /api/bookings/1/` — the `status_logs` array should show both transitions with timestamps.

5. **Try a role violation**: as the *patient*, attempt `PATCH .../transition/` with `{"status": "confirmed"}`.
   Should return `403 Forbidden` — patients can't confirm their own bookings, only cancel them.

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-08-booking-state-machine

git add backend/apps/bookings/services.py
git commit -m "feat(bookings): add state machine service enforcing valid status transitions"

git add backend/apps/bookings/serializers.py backend/apps/bookings/views.py backend/apps/bookings/urls.py
git commit -m "feat(bookings): add booking create/list/detail/transition API endpoints"

git add DAY8.md
git commit -m "docs: add Day 8 notes"

git push origin feature/day-08-booking-state-machine
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 9)
1. Patient booking form UI — the actual "Book a Bed Here" button on the hospital detail page
   finally does something
2. Connect booking form to backend
3. Booking confirmation screen

Say "let's do Day 9" when ready.
