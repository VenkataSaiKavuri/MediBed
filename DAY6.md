# Day 6 — Pagination, Sorting, End-to-End Test Pass

## What's done

### Backend (Task 2)
- `config/settings.py` — added `DEFAULT_PAGINATION_CLASS` (DRF's `PageNumberPagination`) and
  `PAGE_SIZE = 10` globally. This means `GET /api/hospitals/` now returns
  `{ count, next, previous, results: [...] }` instead of a bare array.
- `apps/hospitals/views.py` — added `?ordering=` support (`name`, `-name`, `city`, `-city`,
  `updated_at`, `-updated_at`) with an allow-list so a bad value can't be used to sort by an
  unintended/sensitive field. Defaults to `name` for stable, predictable pagination (without a
  default order, page 2 could show items you already saw on page 1).

### Frontend (Tasks 1 & 2)
- `PatientDashboard.jsx` — updated to read the new paginated response shape, added a sort dropdown,
  and Previous/Next pagination buttons with a "Page X of Y" indicator. Changing any filter or sort
  now resets you back to page 1 (expected — otherwise you could land on an empty page 4 after a
  filter that only has 2 pages of results).

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
No new models today — no migration needed.

## Test pagination + sorting specifically
1. You'll need **more than 10 verified hospitals** to see pagination in action. If you don't have
   that many test hospitals yet, quickly add a few more via Django admin (name + city + lat/long +
   "is verified" checked is enough — beds/doctors optional).
2. On `/dashboard/patient`, confirm you see "X hospitals found" and, if X > 10, a "Page 1 of N" control at the bottom.
3. Click **Next** — results should change, "Previous" should become clickable, page number increments.
4. Change the sort dropdown to "City (A–Z)" — results should reorder and reset to page 1.
5. Apply a filter (e.g. bed type) that narrows results below 10 — pagination controls should
   disappear or show "Page 1 of 1" since there's nothing more to page through.

## Task 3 — Full end-to-end test pass (Days 1–6 together)

Run through this whole checklist in one sitting — it's the first time everything gets tested as one system rather than day-by-day pieces:

- [ ] **Signup** a new patient account → OTP appears in backend console → verify → redirected to login
- [ ] **Login** as that patient → lands on `/dashboard/patient`, tokens present in Local Storage
- [ ] **Search** with no filters → see all verified hospitals, paginated if >10
- [ ] **Filter** by city, then bed type, then specialty, then combine 2+ filters together
- [ ] **Sort** by each of the 4 sort options, confirm order actually changes
- [ ] **Click a hospital** → detail page loads with correct beds/doctors/equipment
- [ ] **Log out** from patient, **log in** as your hospital_admin test account
- [ ] Land on `/dashboard/hospital-admin` → see correct hospital, beds, doctors, equipment
- [ ] **Add** a new bed type, doctor, and equipment entry — confirm each appears immediately
- [ ] **Edit** a bed's total count, toggle a doctor's duty status, cycle equipment status
- [ ] **Delete** one of each (bed/doctor/equipment) — confirm removal persists after page refresh
- [ ] **RBAC check**: while logged in as patient, manually navigate to `/dashboard/hospital-admin` →
      confirm you're redirected away, not shown hospital data
- [ ] **RBAC check**: while logged in as hospital_admin, manually navigate to `/dashboard/patient` →
      confirm same redirect behavior

If everything on this list works, your foundation (auth, RBAC, hospital data, search) is solid
going into Week 2, where booking logic gets layered on top of it.

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-06-pagination-testing

git add backend/config/settings.py backend/apps/hospitals/views.py
git commit -m "feat(hospitals): add pagination and sorting to hospital search"

git add frontend/src/pages/dashboard/PatientDashboard.jsx
git commit -m "feat(frontend): pagination controls and sort dropdown on patient search"

git add DAY6.md
git commit -m "docs: add Day 6 notes and full end-to-end test checklist"

git push origin feature/day-06-pagination-testing
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next — Week 2 begins: Day 8
1. Build booking state machine (`requested → confirmed/rejected → completed/cancelled/no_show`)
2. Create Bookings API (create, update status)
3. Design booking DB relations (link to bed/doctor/patient)

This is where the platform stops being "just a directory" and becomes an actual booking system.
Say "let's do Day 8" when you've finished the end-to-end checklist above (Day 7 in the original
plan was a pure buffer/bug-fix day — since we've been testing continuously, we can roll straight
into Day 8 unless the checklist above turns up problems).
