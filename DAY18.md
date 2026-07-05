# Day 18 — ID Upload, Name-Match Verification, Encrypted Storage

## Important scope note
This is real government ID handling — approached deliberately conservatively:
- Name-match verification here is a **basic self-reported string comparison** (does the name
  typed at upload time match the account name), **not OCR** and **not a government ID database
  lookup**. That's intentionally out of scope for now — faking that level of confidence would be
  worse than being honest about the limitation.
- A mismatch is a **soft signal** (flag for review), never a hard block — matching Day 17's
  philosophy, since name variations (nicknames, transliteration differences, married names) are
  common and shouldn't lock out real patients.
- Emergency bookings (Day 21+) will deliberately skip this requirement entirely for speed — this
  gate only applies to the *non-emergency* booking flow.

## What's done

### Task 3 — Encrypted storage (built first, since 1 & 2 depend on it)
- `apps/users/encryption.py` (new) — Fernet symmetric encryption. Files are encrypted **before**
  ever touching disk. In dev, if you haven't set `ID_DOCUMENT_ENCRYPTION_KEY`, a key is derived
  deterministically from `SECRET_KEY` so files stay decryptable across server restarts. **In
  production, `ID_DOCUMENT_ENCRYPTION_KEY` must be set explicitly** — the doc comments explain why.
- `config/settings.py` — added `MEDIA_ROOT`/`MEDIA_URL` (needed for any FileField) and the new
  encryption key setting.
- Encrypted files are never served via Django's normal media URL — only through
  `DownloadIdentityDocumentView`, which decrypts on the fly and is restricted to the document's
  own patient or a `platform_admin`.

### Task 1 — ID upload
- `apps/users/models.py` — new `IdentityDocument` model: `document_type` (aadhaar/passport),
  `encrypted_file`, `name_on_document`, plus review fields for Day 19's admin dashboard.
- `POST /api/auth/identity-documents/` — upload endpoint (patient only, multipart form)
- `GET /api/auth/identity-documents/mine/` — status check (never returns the file itself)
- `GET /api/auth/identity-documents/<id>/download/` — decrypt-and-download, owner or platform_admin only
- Frontend: `UploadIdentityDocument.jsx` — file picker + document type + self-reported name

### Task 2 — Name-match verification
- `apps/users/name_matching.py` (new) — normalizes both names (lowercase, strip punctuation) and
  computes a similarity ratio via Python's `difflib.SequenceMatcher`. Three buckets:
  `exact_match` (≥0.95), `close_match` (≥0.75), `mismatch` (below). An exact match
  auto-sets `id_document_verified = True` on the user; anything less is left for manual review.

### Enforcement
`CreateBookingSerializer.validate()` now requires **at least one uploaded** `IdentityDocument`
before a non-emergency booking can be created — not necessarily a *verified* one, just an
upload on file. If missing, the frontend's `BookingForm.jsx` catches that specific error and
redirects straight to `/verify-identity` instead of showing raw error text.

## Run it

**New migration + one-time setup needed:**
```powershell
cd backend
venv\Scripts\activate
pip install cryptography --break-system-packages
python manage.py makemigrations users
python manage.py migrate
python manage.py runserver
```
```powershell
cd frontend
npm run dev
```

## Test it

### First-time booking now requires ID upload
1. Create a **brand new** patient account (or use one that's never booked before)
2. Try to book a bed
3. **Expected:** instead of reaching the deposit screen, you're redirected to `/verify-identity`
4. Fill the form — pick a document type, type a name, upload any small image or PDF file
5. Submit → should redirect you back
6. Try booking again → should now proceed normally to the deposit screen

### Exact match auto-verification
1. Upload an ID with the **name_on_document exactly matching** your account's first+last name
   (check what name you signed up with)
2. Check that user in Django admin → `id_document_verified` should now be `True`
3. Check the `IdentityDocument` entry in Django admin → `name_match_result` = `exact_match`

### Mismatch is flagged but doesn't block
1. Create another test patient, upload an ID with a **clearly different name** (e.g. signed up as
   "Test Patient" but type "Someone Else Entirely" as the document name)
2. Check Django admin → that `IdentityDocument` should show `name_match_result = mismatch`
3. Check that user → `id_document_verified` should still be `False`
4. Try booking anyway → **should still succeed** (upload existing is all that's required, not a
   verified match) — confirms this is a soft signal, not a hard block

### Encryption actually works
1. Find the uploaded file on disk: `backend/media/identity_documents/<year>/<month>/`
2. Try opening it directly in a text editor or image viewer
3. **Expected:** unreadable garbage — confirms it's genuinely encrypted, not just renamed

### Access control on download
1. Via Postman, try `GET /api/auth/identity-documents/<id>/download/` using a **different
   patient's** token (not the one who uploaded it)
2. **Expected:** `403 Forbidden`
3. Try again using the actual owning patient's token → should succeed and return a downloadable
   (now-decrypted) file
4. Try with a `platform_admin` token (if you have one set up) → should also succeed

## Git commits for today
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/day-18-id-verification

git add backend/requirements.txt backend/config/settings.py
git commit -m "chore: add cryptography dependency and media/encryption settings"

git add backend/apps/users/encryption.py backend/apps/users/name_matching.py
git commit -m "feat(identity): add file encryption and basic name-match verification logic"

git add backend/apps/users/models.py backend/apps/users/migrations/ backend/apps/users/serializers.py backend/apps/users/views.py backend/apps/users/urls.py backend/apps/users/admin.py
git commit -m "feat(identity): add ID document upload, status, and access-controlled download endpoints"

git add backend/apps/bookings/serializers.py
git commit -m "feat(bookings): require an uploaded ID document before non-emergency booking"

git add frontend/src/pages/identity/ frontend/src/pages/bookings/BookingForm.jsx frontend/src/App.jsx frontend/src/api/client.js
git commit -m "feat(frontend): ID upload page, redirect from booking flow when ID is missing"

git add DAY18.md
git commit -m "docs: add Day 18 notes"

git push origin feature/day-18-id-verification
```
On GitHub: open PR, confirm base = `develop`, review, merge.

## Next (Day 19)
1. Platform Admin fraud dashboard UI
2. List flagged users/bookings for review
3. Manual approve/block action for admin

This is where all of Week 3's soft signals (Day 17's device/IP flags, today's name mismatches)
finally get a real interface for a human to act on, instead of only being visible in Django admin.

Say "let's do Day 19" when ready.
