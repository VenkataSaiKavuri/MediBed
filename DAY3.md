# Day 3 — RBAC + Dashboard Skeletons

## What's done

### Backend (Task 1)
- `apps/core/permissions.py` — `IsPatient`, `IsHospitalAdmin`, `IsDoctor`, `IsPlatformAdmin`,
  `IsHospitalStaff`, `BelongsToSameHospital` — DRF permission classes to plug into any view.
- `apps/users/views.py` — added `MeView` (`GET /api/auth/me/`) so the frontend can fetch the
  logged-in user's full profile (role, hospital, reputation score) any time, not just at login.

### Backend (Task 2 support)
- `apps/hospitals/serializers.py` + `views.py` + `urls.py` — new endpoints:
  - `GET /api/hospitals/` — list verified hospitals (patient search, Day 5 adds filters)
  - `GET /api/hospitals/mine/` — hospital admin's own hospital, fully nested with beds/doctors/equipment
  - `PATCH /api/hospitals/beds/<id>/` — update bed total_count (admin only, scoped to their hospital)
  - `PATCH /api/hospitals/equipment/<id>/` — update equipment (same scoping)

### Frontend (Tasks 2 & 3)
- `src/context/AuthContext.jsx` — fetches `/me/` on load, exposes `user`, `loading`, `logout`, `refetch`
- `src/components/ProtectedRoute.jsx` — redirects to `/login` if not authenticated or wrong role
- `src/pages/dashboard/PatientDashboard.jsx` — shows hospital list + emergency booking button (stub)
- `src/pages/dashboard/HospitalAdminDashboard.jsx` — shows the admin's hospital: beds, doctors, equipment
- `App.jsx` updated to wrap everything in `AuthProvider` and protect the two dashboard routes by role

## Run it

```bash
# Backend
cd backend
source venv/bin/activate
python manage.py runserver

# Frontend (new terminal)
cd frontend
npm run dev
```

## Set up test data (needed before dashboards show anything)

1. Go to `http://localhost:8000/admin/`
2. **Add a Hospital**: name, address, city, lat/long, phone — check "is verified"
3. On that same Hospital page, add a couple of **Bed inventory** rows (e.g. General: total 20, available 15) and **Equipment** rows
4. Go to **Users** → open the hospital_admin test user you want to use (or create one: set `role = hospital_admin`, and set its `hospital` field to the hospital you just created)
   - Note: hospital_admin accounts can't self-signup through the public form (by design, to prevent fake hospital accounts) — they must be created/assigned via Django admin
5. Log out of your patient test account in the browser if logged in, and log in as this hospital_admin user instead (use the same `/login` page — role comes from the account, not a toggle)

## Test both dashboards

**As a patient:**
- Log in with your existing patient account → lands on `/dashboard/patient`
- You should see the hospital(s) you marked "is verified" in Django admin

**As a hospital admin:**
- Log in with the hospital_admin account you just set up → lands on `/dashboard/hospital-admin`
- You should see your hospital's name, bed counts, doctors, and equipment

**Test RBAC is actually working:**
- While logged in as a patient, manually type `http://localhost:3000/dashboard/hospital-admin` in the address bar → should redirect you back to `/login` (or patient dashboard) instead of showing hospital data

## Git commits for today

```bash
git checkout develop
git checkout -b feature/day-03-rbac-dashboards

git add backend/apps/core/permissions.py
git commit -m "feat(rbac): add role-based permission classes"

git add backend/apps/users/views.py backend/apps/users/serializers.py backend/apps/users/urls.py
git commit -m "feat(auth): add /me/ endpoint for current user profile"

git add backend/apps/hospitals/serializers.py backend/apps/hospitals/views.py backend/apps/hospitals/urls.py
git commit -m "feat(hospitals): add hospital list/detail/mine endpoints scoped by RBAC"

git add frontend/src/context/ frontend/src/components/ProtectedRoute.jsx frontend/src/pages/dashboard/ frontend/src/App.jsx frontend/src/pages/Login.jsx frontend/src/api/client.js
git commit -m "feat(frontend): add auth context, protected routes, patient and hospital admin dashboards"

git push origin feature/day-03-rbac-dashboards
```

## Next (Day 4)
1. Bed inventory CRUD (edit total_count from the admin dashboard UI, not just Django admin)
2. Doctor roster CRUD
3. Equipment inventory CRUD

Say "let's do Day 4" when ready.
