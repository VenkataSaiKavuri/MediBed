# Day 2 — Auth, OTP, Login/Signup Screens

## What's done

### Backend (Tasks 1 & 2)
- `apps/users/models.py` — added `OneTimePassword` model (OTP codes, expiry, attempt limits)
- `apps/users/otp_utils.py` — `generate_and_send_otp()` and `verify_otp()` logic. SMS sending is
  currently a **stub** that prints the code to your Django console (`[SMS STUB] ...`) — swap in
  Twilio/MSG91 in `send_sms()` before production.
- `apps/users/serializers.py` — signup validation (blocks public self-registration as
  hospital_admin/doctor/platform_admin — those roles must be created via Django admin), OTP
  request/verify serializers, and a custom JWT serializer that embeds `role` in the token.
- `apps/users/views.py` — `SignupView`, `RequestOTPView`, `VerifyOTPView`, `CustomTokenObtainPairView`.
- `apps/users/urls.py` — wired to `/api/auth/signup/`, `/api/auth/otp/request/`,
  `/api/auth/otp/verify/`, `/api/auth/login/`, `/api/auth/token/refresh/`.

### Frontend (Task 3)
- Vite + React scaffold in `frontend/`
- `src/api/client.js` — Axios instance with JWT auto-attach + auto-refresh on 401
- `src/pages/Signup.jsx`, `VerifyOtp.jsx`, `Login.jsx` — full working forms wired to the backend
- `src/App.jsx` — routes: `/signup`, `/verify-otp`, `/login`

## Run it

**Backend — apply the new migration:**
```bash
cd backend
source venv/bin/activate
python manage.py makemigrations users
python manage.py migrate
python manage.py runserver
```

**Frontend — install and run:**
```bash
cd frontend
npm install
npm run dev
```
Visit **http://localhost:3000** — you'll land on `/login`.

## Try the full flow
1. Go to `/signup`, fill the form, submit
2. You're redirected to `/verify-otp`
3. Check your **Django terminal** — you'll see `[SMS STUB] To: +91... | Message: Your MedBeds verification code is XXXXXX`
4. Copy that code into the Verify OTP screen
5. You're redirected to `/login` — log in with the username/password you just created
6. Open browser dev tools console — you'll see `Logged in as role: patient`, and you're redirected
   toward a dashboard route (routes themselves come in Day 3)

## Git commits for today

```bash
git checkout develop
git checkout -b feature/day-02-auth-otp

git add backend/apps/users/models.py
git commit -m "feat(auth): add OneTimePassword model for phone verification"

git add backend/apps/users/otp_utils.py
git commit -m "feat(auth): add OTP generation, verification, and SMS stub"

git add backend/apps/users/serializers.py backend/apps/users/views.py backend/apps/users/urls.py backend/apps/users/admin.py
git commit -m "feat(auth): add signup, login, and OTP API endpoints"

git add frontend/
git commit -m "feat(frontend): scaffold Vite+React app with login/signup/OTP screens"

git push origin feature/day-02-auth-otp
# open a PR into develop on GitHub, review, merge
```

## Next (Day 3)
1. Role-based access control (RBAC) middleware/permissions
2. Hospital Admin dashboard skeleton
3. Patient dashboard skeleton

Say "let's do Day 3" when ready.
