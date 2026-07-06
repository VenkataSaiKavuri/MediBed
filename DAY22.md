# Day 22 — Real Nearest-Hospital Matching by Distance + Availability

Replaces yesterday's placeholder alphabetical hospital dropdown with the real thing.

## What's done

### Task 1 — Geolocation-based nearest-hospital query
`apps/hospitals/geo.py` (new) — Haversine distance calculation between the patient's captured
lat/lng and each hospital's coordinates. No PostGIS needed (deliberately deferred back on Day 1)
— plain Python math is accurate enough for city/regional-scale "which hospital is closer" ranking.

`GET /api/hospitals/nearest/?lat=X&lng=Y&bed_type=icu` — new endpoint. Computes distance to every
verified hospital, sorts ascending, returns the closest matches with a `distance_km` field on each.

### Task 2 — Filter by live availability
If `bed_type` is provided, hospitals with **zero** available beds of that type are excluded
entirely from the results — not just ranked lower. Showing a hospital with no beds during a real
emergency wastes exactly the time this whole feature exists to save.

### Task 3 — Ranked list (distance + availability)
The frontend `EmergencyBooking.jsx` now:
- Calls `/hospitals/nearest/` as soon as location is captured, re-querying whenever the bed type
  selection changes (different bed types have different availability, so the ranked list itself
  legitimately changes)
- **Auto-selects the nearest matching hospital** as the default — true one-tap speed; the patient
  doesn't have to scan a list and decide, though they still can override it
- Shows each hospital's distance (e.g. "2.3 km away") and live bed count right in the picker
- Falls back gracefully to a plain (unranked, but still bed-type-filtered) list if location
  wasn't captured — the flow still works without GPS, just without distance sorting

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

### Basic ranking
1. Make sure you have at least 2-3 verified hospitals with different lat/long coordinates and
   some available beds (check/set these in Django admin if needed — real-ish coordinates matter
   here, not the same point repeated, or every "distance" will be near-identical)
2. Go to `/emergency` as patient, allow location access
3. **Expected:** the hospital list shows each one with a distance in km, sorted closest-first,
   and the closest one should already be selected (highlighted blue) by default

### Availability filtering actually excludes, not just deprioritizes
1. In Django admin, set one hospital's `icu` bed inventory to `available_count = 0`
2. On the emergency page, switch bed type to "icu"
3. **Expected:** that hospital disappears from the list entirely — not shown lower, not shown
   grayed out, just absent
4. Switch bed type to something that hospital does have available (e.g. "general")
5. **Expected:** it reappears

### Changing bed type re-ranks correctly
1. Set up two hospitals where hospital A has ICU beds but hospital B doesn't (while B has general beds and A doesn't)
2. On `/emergency`, select "icu" → only hospital A should appear
3. Switch to "general" → hospital A should disappear, hospital B should appear (assuming B is verified and has stock)

### No-location fallback still works
1. Deny location permission (or test in a context where geolocation fails)
2. **Expected:** hospital list still populates (via the plain `bed_type`-filtered list, no
   distance shown), and you can still select one and submit successfully

### Confirm the API directly (optional, via Postman)
```
GET http://localhost:8000/api/hospitals/nearest/?lat=16.5062&lng=80.6480&bed_type=icu
Authorization: Bearer <any authenticated token>
```
Response should be a JSON array with `distance_km` on each hospital, sorted ascending, only
including hospitals with ICU availability.

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-22-nearest-hospital

git add backend/apps/hospitals/geo.py backend/apps/hospitals/views.py backend/apps/hospitals/urls.py
git commit -m "feat(hospitals): add geolocation-based nearest-hospital matching with availability filter"

git add frontend/src/pages/bookings/EmergencyBooking.jsx frontend/src/api/client.js
git commit -m "feat(frontend): replace placeholder hospital list with real distance-ranked matching"

git add DAY22.md
git commit -m "docs: add Day 22 notes"

git push origin feature/day-22-nearest-hospital
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 23)
1. Instant hospital alert on emergency request (SMS + dashboard)
2. SLA timer for hospital response (already set at 15 min since Day 21 — today builds the
   actual urgent notification/alert around it)
3. Confirm/reject action updates emergency status (already works via the existing state machine
   — today's focus is making sure hospitals actually notice fast enough to use it)

Say "let's do Day 23" when ready.
