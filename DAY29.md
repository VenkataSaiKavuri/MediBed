# Day 29 — Security Pass: HTTPS, Input Validation, OTP Hashing, Compliance Checklist

## What's done

### Task 1a — HTTPS enforcement
`config/settings.py` — a block of production-only security settings (`SECURE_SSL_REDIRECT`,
`SESSION_COOKIE_SECURE`, HSTS headers, clickjacking protection, etc.), all conditional on
`DEBUG=False` so local development over plain HTTP is completely unaffected. Flip
`DJANGO_DEBUG=False` in production and these activate automatically.

### Task 1b — Input validation gaps closed
Found and fixed two real gaps while auditing:
- **Phone number format** — `SignupSerializer` accepted literally any string up to 15
  characters as a "phone number," including garbage that would silently break SMS delivery
  later. Now validated against a basic E.164-ish pattern.
- **Geolocation bounds** — both `NearestHospitalsView` (Day 22) and
  `CreateEmergencyBookingSerializer` (Day 21) accepted any float for lat/lng, including
  physically impossible values like `lat=999`. Now bounded to real coordinate ranges
  (-90 to 90 / -180 to 180).

### Task 2 — Encryption at rest: found and fixed a real gap
**OTP codes were stored in plaintext** since Day 2 — anyone with database read access (a leaked
backup, insider access, SQL injection) could see valid, unexpired verification codes directly.
Fixed today: codes are now SHA-256 hashed before storage (same principle as password hashing),
verified by re-hashing the input and comparing — the plaintext code only ever exists in memory
briefly and in the SMS sent to the user, never in the database.

**Migration needed** — the `code` field widened from 6 characters to 64 (to hold a hash).

Everything else sensitive was already encrypted/protected from earlier days: ID documents
(Day 18, Fernet encryption), passwords (Django's built-in PBKDF2, since Day 1), JWT tokens
(signed, short-lived, since Day 2).

### Task 3 — Compliance checklist
`COMPLIANCE_CHECKLIST.md` (new, project root) — explicitly framed as an engineering checklist,
**not legal advice**. Covers what's already built that helps (encryption, access control, audit
trails, rate limiting), and honestly lists what's NOT built yet and needs a real legal decision
before launch: data retention policy, right-to-erasure, consent language, breach notification
plan, data localization, and whether `condition_category` needs the same encryption treatment as
ID documents. This is meant to be a real pre-launch reference, not a box-ticking exercise.

## Run it

**New migration needed** (OTP code field widened):
```powershell
cd backend
venv\Scripts\activate
python manage.py makemigrations users
python manage.py migrate
python manage.py runserver
```

## Test it

### OTP hashing actually works
1. Request a signup OTP for a new account
2. Check the OTP in Django admin → **One Time Passwords** — the `code` field should show a long
   hex string (the hash), not the 6-digit code
3. Check your backend terminal — the actual 6-digit code should still be there in the
   `[SMS STUB]` line (that's the only place the plaintext code should ever appear)
4. Enter that 6-digit code in the verify screen → should still work normally, confirming the
   hash-and-compare logic is correct

### Phone number validation
1. Try signing up with an invalid phone number (e.g. `abc123` or a 2-digit number)
2. **Expected:** `400 Bad Request` with a clear message about phone number format
3. Try a valid one (e.g. `+919876543210`) → should succeed as normal

### Geolocation bounds
Via Postman:
```
GET http://localhost:8000/api/hospitals/nearest/?lat=999&lng=80.64&bed_type=icu
Authorization: Bearer <any token>
```
**Expected:** `400 Bad Request` — "lat must be between -90 and 90..."

### HTTPS settings don't break local dev
1. Confirm `DJANGO_DEBUG=True` is still set in your `.env`
2. Run the app normally — everything should work exactly as before, since the new security
   settings are all gated behind `if not DEBUG`
3. (Optional, advanced) Temporarily set `DJANGO_DEBUG=False` in `.env`, restart — the server will
   likely fail or behave oddly locally since HTTPS isn't actually configured on localhost; this
   is expected and exactly why these settings stay off in dev. **Set DEBUG back to True
   afterward** — don't leave your local setup in this state.

## Read the compliance checklist
Open `COMPLIANCE_CHECKLIST.md` — no testing needed, just worth actually reading through before
you consider this project ready for real users, especially the "known gaps" section.

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-29-security-pass

git add backend/config/settings.py
git commit -m "feat(security): add production HTTPS/HSTS/clickjacking settings, gated on DEBUG=False"

git add backend/apps/users/models.py backend/apps/users/migrations/ backend/apps/users/otp_utils.py backend/apps/users/admin.py
git commit -m "fix(security): hash OTP codes at rest instead of storing plaintext"

git add backend/apps/users/serializers.py
git commit -m "fix(validation): add phone number format validation at signup"

git add backend/apps/hospitals/views.py backend/apps/bookings/serializers.py
git commit -m "fix(validation): add geolocation coordinate bounds checking"

git add COMPLIANCE_CHECKLIST.md
git commit -m "docs: add data protection and compliance checklist"

git add DAY29.md
git commit -m "docs: add Day 29 notes"

git push origin feature/day-29-security-pass
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 30) — Dockerization + CI/CD
1. Dockerize backend + frontend + Postgres + Redis (Docker Compose)
2. GitHub Actions CI pipeline (lint + test on push)
3. GitHub Actions CD pipeline (auto-deploy to staging on merge to main)

This was actually already scaffolded back on Day 1 (the original project plan doc included
Dockerfiles and CI/CD YAML) — Day 30 is where we actually build and test that against your real,
now much more complete, application.

Say "let's do Day 30" when ready.
