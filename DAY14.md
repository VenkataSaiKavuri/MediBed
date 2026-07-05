# Day 14 — Full End-to-End Test Pass

Week 1 got its own checklist back on Day 6. This is the equivalent checkpoint for **Week 2** —
auth through payments — before Week 3 layers an anti-fraud system on top of all of it. Go through
every box in one sitting if you can; catching a gap now is much cheaper than after more complexity
is stacked on top.

## Part A — Auth & Identity (Days 1–3)
- [ ] Sign up a brand new patient account → OTP appears in backend console → verify → redirected to login
- [ ] Log in as that patient → lands on `/dashboard/patient`, tokens in Local Storage
- [ ] `dev_fcm_token` also present in Local Storage (Day 12)
- [ ] Manually navigate to `/dashboard/hospital-admin` while logged in as patient → redirected away (RBAC)
- [ ] Log in as hospital_admin → lands on `/dashboard/hospital-admin`, sees correct hospital data
- [ ] Manually navigate to `/dashboard/patient` while logged in as hospital_admin → redirected away

## Part B — Hospital Data Management (Days 4–6)
- [ ] Add/edit/delete a bed type, doctor, and equipment entry from the hospital admin dashboard
- [ ] Confirm changes persist after a page refresh (not just client-side state)
- [ ] As patient, search with no filters → paginated list of verified hospitals appears
- [ ] Filter by city, bed type, and specialty individually, then combined
- [ ] Sort by each of the 4 sort options, confirm order changes correctly
- [ ] Click into a hospital → detail page shows correct live beds/doctors/equipment
- [ ] Zero out a bed type's `available_count` → confirm it disappears from that bed-type filter

## Part C — Booking Lifecycle (Days 8–11)
- [ ] Create a booking as patient → lands on deposit screen (not confirmation directly)
- [ ] Pay the stub deposit → lands on confirmation screen showing "Deposit: ₹X (held)"
- [ ] As hospital_admin, see it in Pending with an SLA countdown and "✓ Deposit paid" indicator
- [ ] **Attempt to confirm an unpaid booking** → blocked with 402/alert (edge case fix — the most important one)
- [ ] Confirm a paid booking → bed's `available_count` auto-decrements by 1
- [ ] Mark it completed → bed's `available_count` auto-increments back
- [ ] Deposit shows "(refunded)" on the patient's confirmation page after completion
- [ ] Create + confirm + mark a second booking as **no_show** → deposit shows "(forfeited)"
- [ ] Create + reject (without confirming) a third booking → deposit shows "(refunded)"
- [ ] **Multi-booking overbooking test** (from Day 11): with 2 available beds, confirm 2 bookings,
      try confirming a 3rd → blocked with 409; cancel one confirmed booking → 3rd can now confirm

## Part D — Notifications (Day 12)
- [ ] Backend terminal shows an SMS+push stub pair on booking creation
- [ ] Another pair on confirm, another on complete, another on reject — each with correct wording
      for that specific status (check the actual message text matches the template, not just that
      *a* message appeared)
- [ ] Temporarily break `send_sms()` (add a `raise Exception` at the top) → confirm a booking anyway
      → booking still succeeds, terminal shows `[notification error] ...` instead of a crash →
      **remember to undo this change afterward**

## Part E — Payment Edge Cases (post-Day-13 audit)
- [ ] Re-verify an already-paid booking via Postman → returns existing data unchanged, no error
- [ ] Try to verify payment on an already-completed booking → 400 "no longer awaiting payment"
- [ ] Try to book an off-duty doctor via direct API call (bypassing the frontend dropdown) → 400 blocked

## Part F — Cross-cutting checks
- [ ] Cancel a `requested` (not yet confirmed) booking as patient → succeeds, no bed inventory
      change occurs (since no bed was ever held for a merely-requested booking)
- [ ] Cancel a `confirmed` booking as patient → succeeds, bed inventory increments, deposit refunds
- [ ] Try an invalid transition via Postman (e.g. `requested → completed` directly) → 400 blocked
- [ ] Try a role violation via Postman (patient attempting `confirmed` status) → 403 blocked
- [ ] Check a completed booking's `status_logs` in the API response → shows the full history with
      timestamps and who changed each step

## If everything above passes
Your foundation — auth, RBAC, hospital data, search, the full booking lifecycle, notifications,
and payments with proper fraud guards — is solid. That's a genuinely substantial, working system.
Week 3 (no-show tracking, reputation scoring, rate-limiting, ID verification, fraud dashboard) can
now be built on top of something that actually holds together end to end.

## If something fails
Tell me exactly which checklist item failed and what you saw (error message, wrong status, etc.)
— we'll fix it before moving forward rather than building Week 3's fraud logic on a shaky base.

## Git commits for today
If this session only surfaces bugs to fix rather than new code, commit fixes individually as
they come up, same pattern as the edge-case fixes:
```powershell
git checkout develop
git pull origin develop
git checkout -b day-14-e2e-testing

# ... fix whatever's found, commit each fix separately with a clear message ...

git add DAY14.md
git commit -m "docs: add Day 14 end-to-end test checklist"

git push origin day-14-e2e-testing
```
If nothing fails, you can commit just the checklist doc itself and move on.

## Next — Week 3 begins: Day 15
1. No-show detection (grace period expiry)
2. Auto-deposit forfeiture on no-show — **already built early**, as part of Day 13! We got ahead
   of the original plan here, so Day 15 will focus on the grace-period/expiry detection logic
   (auto-marking a confirmed-but-unattended booking as no_show after time passes) rather than
   forfeiture itself, which already works.
3. Auto-update booking status to "No-show"

Say "let's do Day 15" once you've been through this checklist.
