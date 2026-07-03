# Day 5 — Patient Search, Filters, Hospital Detail Page

## What's done

### Backend (Tasks 1 & 2 support)
- `apps/hospitals/serializers.py` — `HospitalListSerializer` now includes `available_beds`
  (dict of bed_type → available_count) and `specialties` (on-duty doctor specialties) so search
  results are actually useful at a glance.
- `apps/hospitals/views.py` — `HospitalListView` now supports query params:
  - `?search=apollo` — name/city contains
  - `?city=Guntur` — exact-ish city filter
  - `?bed_type=icu` — only hospitals with at least 1 available ICU bed right now
  - `?specialty=cardiology` — only hospitals with an on-duty doctor matching that specialty
  - All combinable, e.g. `?city=Guntur&bed_type=icu`

### Frontend (Tasks 1, 2, 3)
- `PatientDashboard.jsx` — rebuilt with a search box + city/bed-type/specialty filters, debounced
  (waits 400ms after you stop typing before re-searching, so it's not hammering the API on every keystroke).
  Each hospital card now shows live bed-availability badges and links to its detail page.
- `HospitalDetail.jsx` (new) — full hospital profile: bed availability, on-duty doctors, equipment,
  and a "Book a Bed Here" button (wired up on Day 9).
- `App.jsx` — added the `/hospitals/:id` route.

## Run it
```bash
# Backend
cd backend && venv\Scripts\activate && python manage.py runserver

# Frontend
cd frontend && npm run dev
```
No new models today — no migration needed.

## Test it

**As a patient**, on `/dashboard/patient`:
1. Type in the search box — results should update automatically after you pause typing
2. Try the City filter with a city you used when creating test hospitals
3. Try the bed type dropdown (e.g. "icu") — only hospitals with available ICU beds > 0 should show
4. Try the specialty filter using a specialty you assigned to a doctor
5. Click a hospital card — you should land on `/hospitals/<id>` showing full bed/doctor/equipment detail
6. Click "← Back to search" to return

**Edge case to verify:** set a bed type's `available_count` to 0 in the hospital admin dashboard,
then search that bed type as a patient — that hospital should disappear from results, confirming
the filter is reading live data, not stale counts.

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-05-patient-search

git add backend/apps/hospitals/serializers.py backend/apps/hospitals/views.py
git commit -m "feat(hospitals): add search filters (city, bed_type, specialty) and availability summary"

git add frontend/src/pages/dashboard/PatientDashboard.jsx frontend/src/pages/HospitalDetail.jsx frontend/src/App.jsx frontend/src/api/client.js
git commit -m "feat(frontend): patient search UI with filters and hospital detail page"

git push origin feature/day-05-patient-search
```
On GitHub: open PR, confirm base branch = `develop`, review, merge.

## Next (Day 6)
1. Connect frontend search to backend API — already mostly done today, Day 6 focuses on pagination/sorting
2. Add pagination/sorting to hospital list
3. Test search + filter flow end-to-end

Say "let's do Day 6" when ready.
