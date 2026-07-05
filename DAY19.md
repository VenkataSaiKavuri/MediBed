# Day 19 — Platform Admin Fraud Dashboard

This is where all of Week 3's soft signals (Day 16's flagged users, Day 17's suspicious bookings,
Day 18's mismatched ID documents) finally get a real interface, instead of only being visible by
digging through Django admin.

## What's done

### Task 1 — Dashboard UI
`PlatformAdminDashboard.jsx` (new) — three tabs with live counts in the tab labels: **Flagged
Users**, **Suspicious Bookings**, **Pending ID Reviews**. Lands at `/dashboard/platform-admin`
(the redirect logic for this role already existed in `Login.jsx` since Day 3 — the route just
never had anything to point to until today).

### Task 2 — List flagged users/bookings/documents for review
New `apps/core/fraud_views.py` + `fraud_serializers.py`, all under `/api/admin-panel/`:
- `GET /summary/` — counts for the tab badges in one call
- `GET /flagged-users/` — patients with `is_flagged=True`
- `GET /suspicious-bookings/` — bookings with `is_suspicious=True`, including `fraud_flags`,
  `device_id`, `ip_address` (deliberately **not** exposed in the normal patient/hospital-facing
  `BookingSerializer` — only visible here, to platform admins)
- `GET /pending-documents/` — ID uploads that aren't an automatic `exact_match` and haven't been
  reviewed yet

### Task 3 — Manual approve/block actions
- `POST /flagged-users/<id>/unflag/` — restores instant-booking privileges
- `POST /suspicious-bookings/<id>/clear/` — marks a flagged booking as reviewed-and-legitimate
  (doesn't touch the booking's actual status — confirm/reject still happens normally via the
  hospital admin flow)
- `POST /pending-documents/<id>/review/` with `{"action": "approve"}` or `{"action": "reject"}` —
  approving a mismatch manually sets `id_document_verified = True` on the user (for legitimate
  cases like nicknames or transliteration differences); rejecting leaves it unverified but marks
  the document reviewed so it drops off the pending queue

### A UX fix worth noting
The "View document" button doesn't use a plain link — a normal `<a href>` wouldn't carry the JWT
`Authorization` header needed to pass `DownloadIdentityDocumentView`'s access control, so it would
just 401. Instead it fetches the file through the authenticated axios client as a blob and opens
that in a new tab.

## Run it

No new models today — no migration needed.
```powershell
cd backend
venv\Scripts\activate
python manage.py runserver
```
```powershell
cd frontend
npm run dev
```

## First — you need a platform_admin test account
This role has never been created in your test data yet:
1. Go to `http://localhost:8000/admin/` → **Users** → **Add**
2. Set `role = platform_admin`, fill in username/password/phone_number
3. Save

## Test it

1. Log in with that platform_admin account → should land on `/dashboard/platform-admin`
2. Check the tab counts match what you'd expect from your testing across Days 16–18 (e.g. if you
   flagged a user via 3 no-shows on Day 16, "Flagged Users (1)" or more should show)

### Flagged Users tab
1. Click a flagged user's **"Restore booking privileges"** button
2. Check Django admin → that user's `is_flagged` should now be `False`
3. Log in as that patient, try booking → should now succeed (assuming deposit/ID requirements are separately met)

### Suspicious Bookings tab
1. You should see the Day 17 test bookings with their `fraud_flags` reasons displayed
2. Click **"Mark as legitimate"** on one
3. Check Django admin → that booking's `is_suspicious` should now be `False`
4. Confirm its actual booking `status` (requested/confirmed/etc.) is unaffected — clearing the
   flag is separate from the booking lifecycle

### Pending ID Reviews tab
1. You should see the Day 18 mismatch test document
2. Click **"View document"** — should open the (correctly decrypted, readable) file in a new tab
3. Click **"Approve"**
4. Check Django admin → that document's `reviewed = True`, and the uploading user's
   `id_document_verified` should now be `True` (manually approved despite the name mismatch)
5. Upload another mismatched test document from a different account, this time click **"Reject"**
6. Check Django admin → `reviewed = True` but `id_document_verified` stays `False` — correctly
   removed from the pending queue either way, but only approval actually verifies the account

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-19-fraud-dashboard

git add backend/apps/core/fraud_serializers.py backend/apps/core/fraud_views.py backend/apps/core/urls.py backend/config/urls.py
git commit -m "feat(admin): add platform admin fraud review API endpoints"

git add frontend/src/pages/dashboard/PlatformAdminDashboard.jsx frontend/src/App.jsx frontend/src/api/client.js
git commit -m "feat(frontend): platform admin fraud dashboard with flagged users, bookings, and ID review tabs"

git add DAY19.md
git commit -m "docs: add Day 19 notes"

git push origin feature/day-19-fraud-dashboard
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Week 3 complete — Next: Week 4 begins, Day 21
1. One-tap Emergency booking UI
2. Emergency form: phone + OTP + condition category + live location
3. Emergency booking API (skips heavy KYC)

This is the other half of your original problem statement — everything so far has been the
scheduled/non-emergency booking path with full fraud protection; Week 4 builds the fast,
lower-friction emergency path deliberately designed to trade some of that protection for speed
when someone's life is actually on the line.

(Day 20 in the original plan was a pure buffer/bug-fix day — given we've been testing
continuously throughout Week 3, we can roll straight into Day 21 unless you'd like a dedicated
pass first.)

Say "let's do Day 21" when ready — or "let's do Day 20" if you want a consolidation pass first.
