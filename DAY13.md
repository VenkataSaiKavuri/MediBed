# Day 13 — Payment Gateway Integration, Refundable Deposits

**Decision made this session:** using Razorpay (centralized payments), not a blockchain/crypto
escrow. For a medical emergency platform, speed, regulatory clarity, and user familiarity with
UPI/cards outweigh the theoretical trustlessness benefits of a decentralized approach — see the
earlier discussion in-chat if you want the full reasoning again later.

## What's done

### Built dev-stub-first (same pattern as SMS/OTP/push)
`apps/bookings/payments.py` — every function (`create_order`, `verify_payment_signature`,
`refund_payment`) checks whether real Razorpay keys are configured. **If not, it returns realistic
fake IDs and auto-approves everything** — meaning the entire deposit → refund/forfeit pipeline is
fully testable right now, before you ever create a Razorpay account. The moment you add real keys
to `.env`, these same functions switch to making real API calls with zero other code changes.

### Task 1 — Razorpay integration
- `config/settings.py` — `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` (blank by default = dev-stub mode)
- `apps/bookings/models.py` — added `razorpay_order_id`, `razorpay_payment_id`, `razorpay_refund_id`,
  `deposit_forfeited` fields

### Task 2 — Refundable deposit at booking time
- `apps/bookings/payments.py` — `DEPOSIT_AMOUNTS` table (flat fee per bed type: general ₹100,
  icu ₹500, ventilator ₹1000, maternity ₹300, emergency ₹500 — tune these however you like)
- `CreateBookingSerializer` now creates a Razorpay order at booking creation time and returns
  `deposit_amount`, `razorpay_order_id`, `razorpay_key_id`, `is_stub_payment` in the response
- New endpoint: `POST /api/bookings/<id>/verify-payment/` — confirms the deposit was actually paid
- **Frontend flow changed**: `BookingForm.jsx` is now two steps — fill booking details → pay the
  deposit (either a "Simulate Payment" button in dev-stub mode, or a real Razorpay checkout modal
  once real keys exist) — only after payment succeeds does it navigate to the confirmation screen

### Task 3 — Refund/forfeiture logic
Hooked into `transition_booking()` in `services.py`, via the same `transaction.on_commit()`
pattern as notifications:
- **Refunded** on `completed`, `cancelled`, or `rejected` — a rejection isn't the patient's fault,
  so they get their money back too
- **Forfeited** on `no_show` — this is the actual anti-fraud purpose of the whole deposit system;
  someone who reserves a bed and doesn't show up loses the deposit instead of just walking away free
- A refund/forfeit failure is caught and logged, never allowed to reopen or break an already-closed
  booking

## Run it

**New migration needed:**
```powershell
cd backend
venv\Scripts\activate
python manage.py makemigrations bookings
python manage.py migrate
python manage.py runserver
```
```powershell
cd frontend
npm run dev
```

## Test it (all in dev-stub mode — no Razorpay account needed yet)

1. As **patient**, book a bed → after submitting the form, you now land on a **"Refundable
   Deposit Required"** screen showing the amount and a yellow "Dev mode" notice
2. Click **"Simulate Payment"** → should redirect to the normal confirmation screen, now showing
   a **"Deposit: ₹X (held)"** row
3. As **hospital_admin**, confirm the booking → check the patient's confirmation page — deposit
   still shows "(held)" since it's not resolved yet
4. Mark the booking **completed** → refresh the patient's confirmation page → deposit should now
   show **"(refunded)"**
5. Create a second booking, pay the stub deposit, confirm it, then mark it **no_show** instead →
   refresh the confirmation page → deposit should show **"(forfeited)"**
6. Create a third booking, pay the deposit, then **reject** it (as hospital_admin, without
   confirming first — straight from Pending) → check the patient side → deposit should show
   **"(refunded)"** since rejection isn't a fraud outcome

**Check the backend terminal** during steps 2–6 — since dev-stub mode still runs through the real
code paths, you should NOT see any errors; refunds/forfeitures happen silently and correctly.

## Going to real Razorpay later (not needed yet)
1. Sign up at razorpay.com, get test-mode keys from the dashboard
2. `pip install razorpay --break-system-packages` (or just `pip install razorpay` in your venv)
3. Add `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` to your `.env`
4. Restart the backend — every booking from that point on will use real test-mode Razorpay orders
   and the frontend will automatically show the real checkout modal instead of "Simulate Payment"

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-13-payments

git add backend/apps/bookings/payments.py backend/apps/bookings/models.py backend/apps/bookings/migrations/ backend/config/settings.py
git commit -m "feat(payments): add Razorpay integration with dev-stub mode for deposits"

git add backend/apps/bookings/serializers.py backend/apps/bookings/views.py backend/apps/bookings/urls.py backend/apps/bookings/services.py
git commit -m "feat(bookings): deposit collection on create, refund/forfeit logic on transitions"

git add frontend/src/pages/bookings/ frontend/src/api/client.js
git commit -m "feat(frontend): two-step booking flow with deposit payment (stub + real Razorpay)"

git add DAY13.md
git commit -m "docs: add Day 13 notes"

git push origin feature/day-13-payments
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 14)
Full end-to-end test: book → confirm → decrement (already covered above); fix any bugs found;
test payment + refund flow thoroughly across edge cases before Week 3's anti-fraud layer begins.

Say "let's do Day 14" when ready.
