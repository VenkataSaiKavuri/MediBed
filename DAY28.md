# Day 28 — Hospital Analytics Dashboard, Booking/No-Show Charts, CSV Export

## Scope note, stated upfront
"Occupancy trends" is derived from **booking activity** (volume per day, current bed
utilization), not a true historical time-series of bed counts — there's no snapshot table
recording what occupancy looked like at past points in time, only the current state plus the
full booking history. That's the honest data available, and today's dashboard is built around it
rather than pretending to have trend data that doesn't exist.

**PDF export wasn't built today** — CSV was the higher-value choice for the time available: it
opens universally in Excel/Sheets/Numbers and needed zero new dependencies. A dedicated PDF
export (via `reportlab` or similar) is a reasonable future addition if it's actually needed, not
a corner cut silently — flagged here plainly.

## What's done

### Task 1 — Occupancy
`apps/bookings/analytics.py` (new) — `get_occupancy_stats()` computes current utilization
`(total - available) / total` per bed type, as a percentage.

### Task 2 — Booking volume + no-show rate
- `get_booking_volume_by_day()` — bookings created per day over a selectable window (7/30/90 days)
- `get_no_show_rate()` — no-shows as a % of **resolved** bookings only (completed + no_show +
  cancelled) — deliberately excludes still-pending bookings, since something that hasn't
  happened yet can't fairly count toward a reliability rate either way
- `get_status_breakdown()` — how bookings in the window split across all statuses

### Task 3 — CSV export
`HospitalAnalyticsExportView` — streams every booking for the admin's hospital as a downloadable
CSV (patient, bed type, status, deposit info, escalation count, timestamps) — the raw data behind
the dashboard's aggregates, for admins who want to open it in their own spreadsheet tool.

### Frontend
- `HospitalAnalytics.jsx` (new) — occupancy bars (red above 80%), a hand-rolled SVG bar chart for
  booking volume (no new npm dependency — kept the install simple), no-show rate card
  (color-coded: red above 15%), status breakdown list, a date-range selector, and an
  **"⬇ Export CSV"** button (uses the same authenticated-blob-fetch pattern as Day 19's ID
  document viewer, since a plain link wouldn't carry the JWT header)
- New **"📊 Analytics"** button on the Hospital Admin dashboard, next to the existing Bookings link

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

1. Log in as hospital_admin, click **"📊 Analytics"**
2. **Occupancy section**: should show a bar per bed type with a percentage and a colored progress
   bar (blue normally, red if occupancy > 80%)
3. **Booking Volume chart**: should show a bar per day with bookings created in the selected
   window — hover over a bar to see the exact date/count in a tooltip
4. Switch the date range dropdown between 7/30/90 days — chart and stats should update
5. **No-Show Rate card**: should show a percentage — test its color logic by ensuring you have a
   mix of completed and no_show bookings in your test data (reuse Day 15/16's test data)
6. **Status Breakdown**: should list every status present in the window with counts, color-coded
   to match the badges used elsewhere in the app

### Test the CSV export
1. Click **"⬇ Export CSV"**
2. **Expected:** a file named `medbeds_bookings_export.csv` downloads
3. Open it in Excel/Sheets/Numbers — confirm columns match: Booking ID, Patient, Phone, Bed Type,
   Status, Is Emergency, Condition, Created At, Confirmed At, deposit fields, Escalation Count
4. Confirm row count roughly matches your hospital's total booking count (not filtered by date —
   this exports everything, unlike the dashboard's date-range-filtered charts)

### Confirm scoping is correct
1. If you have a second hospital_admin account for a different hospital, log in as them
2. Check their analytics — should show **only their hospital's** data, never mixing with the first

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-28-analytics

git add backend/apps/bookings/analytics.py backend/apps/bookings/views.py backend/apps/bookings/urls.py
git commit -m "feat(bookings): add hospital analytics aggregation and CSV export endpoints"

git add frontend/src/pages/dashboard/HospitalAnalytics.jsx frontend/src/pages/dashboard/HospitalAdminDashboard.jsx frontend/src/App.jsx frontend/src/api/client.js
git commit -m "feat(frontend): hospital analytics dashboard with occupancy, volume chart, no-show rate, CSV export"

git add DAY28.md
git commit -m "docs: add Day 28 notes"

git push origin feature/day-28-analytics
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 29)
1. Security pass — input validation + HTTPS enforcement
2. Encrypt sensitive data at rest (mostly already done — ID documents since Day 18)
3. Compliance check (DPDP Act/HIPAA depending on region)

Say "let's do Day 29" when ready.
