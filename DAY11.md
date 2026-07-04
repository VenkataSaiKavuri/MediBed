# Day 11 — Auto-Decrement/Increment Bed Inventory

This is the day your original "fake availability" problem starts getting solved for real.
Bed counts now move automatically based on actual booking activity instead of needing manual
admin updates.

## What's done

### Task 1 — Auto-decrement on confirm
`apps/bookings/services.py` — when a booking transitions to `confirmed`, `_decrement_bed()` runs
inside the same atomic transaction as the status change:
- Locks the `BedInventory` row (`select_for_update()`) so two simultaneous confirms can't both
  succeed and take the bed count negative
- Raises `NoBedAvailableError` (→ `409 Conflict` from the API) if `available_count` is already 0 —
  **a booking cannot be confirmed if there's genuinely no bed**, even if the admin clicks Confirm
- If the transaction fails for any reason, the status change AND the inventory change both roll
  back together — they can never drift out of sync

### Task 2 — Auto-increment on release
When a `confirmed` booking moves to `completed`, `cancelled`, or `no_show` — all three "release"
the bed — `_increment_bed()` runs, capped so `available_count` can never exceed `total_count`
(a safety net against double-increment bugs silently inflating availability past physical capacity).

**Important distinction:** a booking that's merely `requested` and gets `cancelled` or `rejected`
does **not** trigger an increment — no bed was ever held for it in the first place, since decrement
only happens at the moment of confirmation, not at request time.

### Task 3 — Multi-booking sync test
See the test steps below — this is the important one to actually run, not just read.

## Run it
```powershell
cd backend
venv\Scripts\activate
python manage.py runserver
```
No new models — no migration needed.

## Test it

### Basic single-booking test
1. In Django admin, set a hospital's ICU bed inventory to `total_count=3, available_count=3`
2. As patient, create a booking for that hospital's ICU bed type
3. As hospital_admin, go to Bookings → Pending → click **Confirm**
4. Go to the Hospital Admin dashboard's Bed Inventory section — ICU should now show **2/3**
   (available/total), without you touching it manually
5. Back in Bookings, click **Mark Completed** on that same booking
6. Check Bed Inventory again — ICU should be back to **3/3**

### Multi-booking sync test (Task 3 — do this one properly)
1. Reset ICU to `available_count=2, total_count=2`
2. Create **3 separate booking requests** for ICU beds at that hospital (as patient — you can use
   the same account 3 times, or 3 different patient accounts if you have them)
3. As hospital_admin, confirm the **first** booking → ICU should drop to **1/2**
4. Confirm the **second** booking → ICU should drop to **0/2**
5. Try to confirm the **third** booking → this should **fail** with a `409` error message like
   *"No 'icu' beds currently available at this hospital."* — the button click should show an alert
   with that message, and the booking should remain in "Pending" (not silently confirmed anyway)
6. Now cancel the **first** confirmed booking → ICU should go back to **1/2**
7. Try confirming the third (previously blocked) request again → this time it should **succeed**,
   since a bed just freed up → ICU back to **0/2**

If all of that behaves exactly as described, your inventory system is airtight against
overbooking — which is the actual core promise of the whole platform.

### Edge case worth checking
Try setting a bed's `available_count` higher than `total_count` directly in Django admin (e.g.
available=10, total=5), then complete a confirmed booking of that type. The increment logic should
refuse to push it past `total_count` — confirm this in your test if you want extra confidence,
though it shouldn't normally arise since admins edit `total_count` only (Day 4's UI never exposes
`available_count` as editable).

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-11-inventory-sync

git add backend/apps/bookings/services.py backend/apps/bookings/views.py
git commit -m "feat(bookings): auto-decrement/increment bed inventory on booking transitions"

git add frontend/src/pages/dashboard/BookingsDashboard.jsx
git commit -m "feat(frontend): surface inventory conflict errors on booking actions"

git add DAY11.md
git commit -m "docs: add Day 11 notes"

git push origin feature/day-11-inventory-sync
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 12)
1. SMS/WhatsApp notification on booking status change
2. Push notification setup (Firebase Cloud Messaging)
3. Notification templates per status

Say "let's do Day 12" when ready.
