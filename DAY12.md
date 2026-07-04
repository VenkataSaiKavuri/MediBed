# Day 12 — Notifications on Booking Status Change

## What's done

### Task 3 — Notification templates (built first, since 1 & 2 depend on it)
- `apps/core/notifications.py` (new) — `NOTIFICATION_TEMPLATES` dict with SMS + push copy for
  every booking status (requested, confirmed, rejected, completed, cancelled, no_show, escalated).
  `notify_booking_status_change(booking)` is the single function that looks up the right template
  and fires both channels.

### Task 1 — SMS/WhatsApp notification
- Hooked into `apps/bookings/services.py`'s `transition_booking()` via `transaction.on_commit()` —
  meaning the SMS only fires *after* the DB transaction (status change + inventory adjustment) has
  actually committed successfully, never before, and never if the transition failed.
- Also hooked into `CreateBookingSerializer.create()` so the very first "requested" SMS goes out
  immediately on booking creation, not just on later transitions.
- Notification failures are caught and logged, never allowed to break a booking action — a broken
  SMS provider should never prevent someone from confirming a real bed.
- Still uses the same console-logging SMS stub from Day 2 (`apps/users/otp_utils.send_sms`) — swap
  in Twilio/MSG91 there and every notification (OTP + booking) upgrades to real SMS at once.

### Task 2 — Push notification setup (FCM)
- `apps/users/models.py` — added `fcm_token` field to `User` (blank until a device registers one)
- `apps/users/views.py` + `urls.py` — new `POST /api/auth/fcm-token/` endpoint
- `apps/core/notifications.py` — `send_push()` stub, same pattern as SMS: logs to console in DEBUG,
  raises `NotImplementedError` in production until real Firebase Cloud Messaging is wired in
- Frontend: `AuthContext.jsx` generates a stable fake device token per browser (stored in
  localStorage) and registers it after login — this lets you exercise the **entire pipeline**
  (register → store → send push on status change) locally without needing a real Firebase project
  yet. Swapping in real Firebase SDK calls later is a drop-in replacement for `registerDeviceToken()`.

## Run it

**New migration needed** (fcm_token field added to User):
```powershell
cd backend
venv\Scripts\activate
python manage.py makemigrations users
python manage.py migrate
python manage.py runserver
```
```powershell
cd frontend
npm run dev
```

## Test it

1. Log in as **patient** — check your backend terminal, you should see:
   ```
   [SMS STUB] To: +91... | Message: MedBeds: Your icu bed request at ... has been sent...
   ```
   (only if you create a booking right after — login alone doesn't trigger this)
2. Open browser dev tools → Application/Storage → Local Storage — confirm a `dev_fcm_token` key exists
3. Create a new booking as patient → check backend terminal for **both**:
   ```
   [SMS STUB] To: ... | Message: MedBeds: Your icu bed request at ... has been sent...
   [PUSH STUB] To token dev-xxxxx... | Booking request sent: Your icu bed request at ... is awaiting confirmation.
   ```
4. As hospital_admin, confirm that booking → terminal should show a new pair of SMS+push stub
   lines with the "confirmed" template wording
5. Mark it completed → another pair with "completed" wording
6. Try rejecting a different pending booking → "rejected" wording appears

**Confirm failures don't break bookings:** temporarily rename `send_sms` in `otp_utils.py` to
`send_sms_broken` (or add a deliberate `raise Exception("test")` at the top of it), then confirm a
booking. The status change and bed inventory update should still succeed — check the terminal for
`[notification error] Failed to notify booking ...` instead of a crashed request. **Undo this
change afterward.**

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-12-notifications

git add backend/apps/core/notifications.py
git commit -m "feat(notifications): add per-status SMS/push templates and dispatch logic"

git add backend/apps/users/models.py backend/apps/users/migrations/ backend/apps/users/views.py backend/apps/users/urls.py
git commit -m "feat(users): add fcm_token field and registration endpoint for push notifications"

git add backend/apps/bookings/services.py backend/apps/bookings/serializers.py
git commit -m "feat(bookings): trigger notifications on booking creation and status transitions"

git add frontend/src/context/AuthContext.jsx frontend/src/api/client.js
git commit -m "feat(frontend): register device token for push notifications on login"

git add DAY12.md
git commit -m "docs: add Day 12 notes"

git push origin feature/day-12-notifications
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 13)
1. Integrate payment gateway (Razorpay/Stripe)
2. Refundable deposit/hold logic at booking time
3. Refund/forfeiture logic on cancel/no-show

Say "let's do Day 13" when ready.
