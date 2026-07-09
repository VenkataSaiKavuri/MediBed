# Day 27 — Staleness Indicators, Stale-Inventory Alerts (Week 5 begins)

This directly serves the original problem statement: confidently-displayed bed counts that are
actually hours stale is exactly the "fake availability" trust problem MedBeds exists to solve.

## What's done

### Task 1 — "Last updated" staleness indicator
- `apps/hospitals/staleness.py` (new) — three tiers: **fresh** (≤1h), **aging** (≤6h), **stale**
  (>6h). Shared by both the API (to show patients/admins a warning) and the alert command.
- `BedInventorySerializer` / `EquipmentSerializer` — both now include a `staleness` field
- `HospitalListSerializer` (patient search results) — new `inventory_staleness` field showing
  the **most-stale** bed row's level, not the freshest — an honest "worst case" trust signal
  rather than hiding a stale row behind a fresh-looking one

### Task 2 — Auto-alert hospital admin if stale
`apps/hospitals/management/commands/alert_stale_inventory.py` (new) — finds every hospital with
at least one bed or equipment row past the 6-hour stale threshold, and sends an SMS reminder to
that hospital's `hospital_admin` account(s). Same dev-stub SMS pattern as every other notification
in the app — logs to console locally, real provider swap-in later.

**Honest limitation noted in the code**, not hidden: there's no "already alerted today" tracking
yet, so running this command more than once a day would re-alert the same stale items repeatedly.
Fine for a daily cron; would need a `last_alerted_at` timestamp if run more frequently in practice.

### Task 3 — UI polish for availability displays
- `StalenessBadge.jsx` (new, shared component) — 🟢 Live / 🟡 Updated a while ago / 🔴 May be
  outdated, used consistently across three different views:
  - Patient search results (`PatientDashboard.jsx`) — one badge per hospital card
  - Hospital detail page (`HospitalDetail.jsx`) — one badge per bed type
  - Hospital admin dashboard (`BedInventorySection.jsx`, `EquipmentSection.jsx`) — one badge
    per item, so admins see exactly which rows need attention
- `HospitalAdminDashboard.jsx` — a red banner appears at the top if **any** bed/equipment item
  is stale, prompting the admin to review before a patient encounters outdated numbers

**A nice side effect worth knowing**: editing a bed's total count or cycling equipment status
already updates `updated_at` (Django's `auto_now=True`) as a natural side effect of the existing
Day 4 CRUD actions — so an admin freshening their staleness badge is literally just "go update
your numbers," no separate "mark as reviewed" button needed.

## Run it

**New serializer fields, but no model changes — no migration needed.**
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

### See staleness change live
1. In Django admin, open a bed inventory row, note its `updated_at` timestamp
2. As patient, search and find that hospital — check the staleness badge (should be 🟢 Live if
   recently created/edited)
3. Manually edit that bed's `updated_at` in Django admin to **8 hours ago** → Save
4. Refresh the patient search page — that hospital's badge should now show 🔴 May be outdated
5. Open the hospital detail page — that specific bed type's badge should also show stale
6. As hospital_admin, log in — you should see the red warning banner at the top of the dashboard,
   and that specific bed card should show the 🔴 badge too

### Confirm editing refreshes staleness naturally
1. Still on the hospital admin dashboard, click "edit total" on that stale bed, change the
   number, save
2. **Expected:** the badge immediately flips back to 🟢 Live — since the edit itself updated
   `updated_at`, no separate action needed

### Test the alert command
1. Make sure at least one hospital has a stale item (repeat the backdating from above if needed)
2. Run:
   ```powershell
   python manage.py alert_stale_inventory
   ```
3. **Expected:** console output like `Alerted 1 admin(s) at <Hospital Name>.` and a
   `[SMS STUB] To: ...` line in the same terminal, since this command runs standalone
4. Run it again immediately
5. **Expected:** re-alerts the same hospital (the known limitation from the docstring) — confirms
   the behavior matches what's documented, not a surprise

### Test a hospital with no bed data at all
1. Create a brand-new hospital in Django admin with zero bed inventory rows
2. Search for it as a patient
3. **Expected:** no staleness badge shown at all (not a red one, not blank space causing layout
   issues — `inventory_staleness` returns `null` when there's nothing to judge staleness against)

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-27-staleness-indicators

git add backend/apps/hospitals/staleness.py backend/apps/hospitals/serializers.py
git commit -m "feat(hospitals): add staleness levels to bed/equipment/hospital serializers"

git add backend/apps/hospitals/management/
git commit -m "feat(hospitals): add alert_stale_inventory command to nudge hospital admins"

git add frontend/src/components/StalenessBadge.jsx frontend/src/pages/dashboard/PatientDashboard.jsx frontend/src/pages/HospitalDetail.jsx frontend/src/pages/dashboard/components/BedInventorySection.jsx frontend/src/pages/dashboard/components/EquipmentSection.jsx frontend/src/pages/dashboard/HospitalAdminDashboard.jsx
git commit -m "feat(frontend): staleness badges across search, detail, and admin dashboard views"

git add DAY27.md
git commit -m "docs: add Day 27 notes"

git push origin feature/day-27-staleness-indicators
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 28)
1. Hospital analytics dashboard (occupancy trends)
2. Booking volume + no-show rate charts
3. Export reports feature (CSV/PDF)

Say "let's do Day 28" when ready.
