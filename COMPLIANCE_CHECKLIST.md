# Data Protection & Compliance Checklist

**This is not legal advice.** MedBeds handles health-adjacent and government ID data — before
any real launch, have an actual lawyer familiar with India's DPDP Act (and HIPAA if you ever
serve US users) review this. What follows is a practical engineering checklist: what's already
built, what's a known gap, and what needs a real legal decision before launch.

## What's already built that helps compliance

| Requirement | Status |
|---|---|
| Encryption at rest for sensitive documents | ✅ ID documents encrypted (Day 18) |
| Encryption in transit | ✅ HTTPS enforced in production (Day 29) |
| Access control on sensitive data | ✅ ID documents: owner or platform_admin only (Day 18) |
| Audit trail of who accessed/changed what | ✅ `BookingStatusLog` (Day 8), `reviewed_by`/`reviewed_at` on ID documents (Day 19) |
| Password security | ✅ Django's built-in PBKDF2 hashing |
| OTP code security | ✅ Hashed at rest, not plaintext (Day 29) |
| Rate limiting on sensitive endpoints | ✅ OTP requests, bookings (Day 8, settings.py) |
| No PII in logs by design | ⚠️ Partially — `print()` statements in notification/reputation error handlers include booking IDs but not raw PII; worth a proper logging audit before production |

## Known gaps — need a real decision before launch

**Data retention policy — not yet defined.** Right now, nothing auto-deletes old data. ID
documents, booking history, OTP records, status logs all persist indefinitely. DPDP Act requires
data be kept only as long as necessary for the purpose collected. **Decision needed:** how long
to retain ID documents after verification (e.g. delete after 90 days?), how long to retain
rejected/expired bookings, whether OTP records should be purged after a short window (they
already expire functionally after 5 minutes, but the rows persist in the DB forever).

**Right to erasure / account deletion — not built.** A patient currently has no way to request
deletion of their account and associated data. DPDP Act (and GDPR-style regimes generally) require
this. **Needs:** a `DELETE /api/auth/me/` (or admin-assisted) flow that either hard-deletes or
properly anonymizes a user's PII while preserving what's legally/operationally required to keep
(e.g. financial records for tax purposes might need retention despite a deletion request — a
lawyer should specify exactly what must survive).

**Consent language — not built.** The signup flow doesn't currently show explicit consent
language for collecting phone number, location, or (later) ID documents. **Needs:** a privacy
notice/consent checkbox at signup and specifically before ID upload (Day 18), explaining what's
collected, why, and how long it's kept.

**Data breach notification plan — not written.** DPDP Act requires notifying the Data Protection
Board and affected individuals of certain breaches. This is a process/legal document, not code —
needs to exist before launch, not be improvised during an actual incident.

**Data localization** — if serving Indian users, DPDP Act has provisions around cross-border data
transfer for certain sensitive categories. **Needs:** confirm your hosting provider's data center
region once you reach Day 31's deployment, and whether Razorpay/any SMS provider you pick stores
data outside India in a way that matters here.

**Health data isn't the same as identity data.** Booking `condition_category` (Day 21) is
arguably sensitive health information under most frameworks, even though it's just a category
label ("cardiac", "trauma") rather than a full medical record. It's currently stored in plaintext
in the `Booking` table, readable by hospital staff (appropriately) and platform admins (for fraud
review). **Worth a decision:** whether this needs the same encryption treatment as ID documents,
or whether category-level data (not detailed medical records) is an acceptable risk level —
a lawyer's call, not an engineering one.

## What this checklist deliberately does NOT cover
- Payment Card Industry (PCI) compliance — not your concern directly since Razorpay handles card
  data; you never touch raw card numbers. Worth confirming with Razorpay's own compliance docs.
- Employment/labor law for hospital staff accounts — out of scope for a booking platform.
- Medical malpractice liability — a legal question about the *service*, not the *software*.

## Immediate low-effort wins (can do before a lawyer weighs in)
1. Add a basic privacy notice page (even a static one) linked from signup — costs little, shows
   good faith, and is a prerequisite for any real consent flow later.
2. Add a data retention TODO/constant somewhere prominent (e.g. `config/settings.py`) so it's
   visible during any future security review, rather than only living in this document.
3. When picking a hosting region for Day 31's deployment, default to an India-based data center
   if your primary user base is India-based — reduces cross-border transfer complexity later.
