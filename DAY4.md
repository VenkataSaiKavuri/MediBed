# Day 4 — Bed / Doctor / Equipment CRUD

## What's done

### Backend (all 3 tasks)
- `apps/hospitals/views.py` — replaced the single `UpdateBedInventoryView`/`UpdateEquipmentView`
  with full `ModelViewSet`s (`BedInventoryViewSet`, `DoctorViewSet`, `EquipmentViewSet`) via a shared
  `HospitalScopedViewSetMixin` that automatically scopes every query to the logged-in admin's own
  hospital and auto-attaches `hospital_id` on create (so no one can create a bed for a hospital
  that isn't theirs).
- `apps/hospitals/serializers.py` — `DoctorSerializer` now accepts a `user_id` on create/update; it
  validates that the ID belongs to an existing account with `role="doctor"` before linking it.
- `apps/hospitals/urls.py` — new REST routes via DRF's router:
  - `GET/POST /api/hospitals/mine/beds/`, `PATCH/DELETE /api/hospitals/mine/beds/<id>/`
  - `GET/POST /api/hospitals/mine/doctors/`, `PATCH/DELETE /api/hospitals/mine/doctors/<id>/`
  - `GET/POST /api/hospitals/mine/equipment/`, `PATCH/DELETE /api/hospitals/mine/equipment/<id>/`

### Frontend (all 3 tasks)
- `src/pages/dashboard/components/BedInventorySection.jsx` — add bed type, edit total count inline, delete
- `src/pages/dashboard/components/DoctorSection.jsx` — add doctor (by existing user_id), toggle on/off duty, delete
- `src/pages/dashboard/components/EquipmentSection.jsx` — add equipment, cycle status (available → in_use → maintenance), delete
- `HospitalAdminDashboard.jsx` — now composes these three sections instead of just displaying static data

## Run it
```bash
# Backend
cd backend && source venv/bin/activate && python manage.py runserver

# Frontend
cd frontend && npm run dev
```
No new models today, so **no migration needed**.

## Test it

**As hospital_admin**, on `/dashboard/hospital-admin`:

1. **Beds**: click "+ Add Bed Type" → pick ICU, total 10 → Save. You'll see a new card "10/0" (0 available
   since nothing's booked yet — that's expected, `available_count` only moves via the booking flow, Day 11).
   Click "edit total" on any card to change the total count.

2. **Doctors**: to add one, you first need a *user account* with `role=doctor`. Quickest path right now:
   Django admin → Users → create a user, set role=doctor, note its ID number. Then in the dashboard,
   click "+ Add Doctor", type that User ID + specialty + license number → Save. Click the "On duty"/"Off duty"
   button to toggle it.

3. **Equipment**: click "+ Add Equipment" → name "Dialysis Machine", total 4, available 4 → Save.
   Click the status button to cycle available → in_use → maintenance.

4. Try deleting an entry with the ✕ button — confirm it disappears and reloading the page confirms it's
   actually gone from the DB (not just hidden client-side).

## A gap worth knowing about (we'll fix it Day 18-ish, flagging now for awareness)
Doctor creation currently requires *you* to already know a valid doctor's User ID — there's no
"invite a doctor by email/phone" flow yet. That's intentional for now (keeps scope contained) but
is a rough edge for a real hospital admin. Worth a "Doctor invite" feature later if you want it.

## Git commits for today
```bash
git checkout develop
git checkout -b feature/day-04-inventory-crud

git add backend/apps/hospitals/views.py backend/apps/hospitals/serializers.py backend/apps/hospitals/urls.py
git commit -m "feat(hospitals): full CRUD viewsets for beds, doctors, equipment scoped to admin's hospital"

git add frontend/src/pages/dashboard/components/ frontend/src/pages/dashboard/HospitalAdminDashboard.jsx frontend/src/api/client.js
git commit -m "feat(frontend): editable bed/doctor/equipment sections on hospital admin dashboard"

git push origin feature/day-04-inventory-crud
```
On GitHub: open PR, **set base branch to `develop`** (not main — the mistake from before), merge.

## Next (Day 5)
1. Patient-side hospital search UI (real search box, not just a static list)
2. Search filters (location, specialty, bed availability)
3. Hospital profile detail page

Say "let's do Day 5" when ready.
