# MedBeds Backend — Day 1 Setup

## What's done (Day 1, tasks 1–3)
1. ✅ Project structure — `config/` (settings) + `apps/users`, `apps/hospitals`, `apps/bookings`, `apps/core`
2. ✅ DB schema designed — see `apps/users/models.py`, `apps/hospitals/models.py`, `apps/bookings/models.py`
3. ✅ PostgreSQL connection configured via `.env`

## Run it locally

```bash
# 1. Install PostgreSQL locally (or use Docker — see Day 30 docker-compose.yml)
# Create the database:
psql -U postgres -c "CREATE DATABASE medbeds;"
psql -U postgres -c "CREATE USER admin WITH PASSWORD 'admin';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE medbeds TO admin;"

# 2. Set up Python environment
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# edit .env if your DB credentials differ

# 4. Load env vars and run migrations
pip install python-dotenv       # already in requirements.txt
python manage.py makemigrations users hospitals bookings
python manage.py migrate

# 5. Create your platform admin account
python manage.py createsuperuser

# 6. Run the dev server
python manage.py runserver
```

Visit **http://localhost:8000/admin/** and log in — you'll already see Hospital,
Doctor, Bed Inventory, Equipment, and Booking management screens because Django's
admin auto-generates them from the models we defined (`apps/*/admin.py`).

## What each model file does
- `apps/users/models.py` — custom User with `role` field (patient/hospital_admin/doctor/platform_admin)
  for RBAC, plus fraud-tracking fields (`reputation_score`, `no_show_count`, `is_flagged`) used from Week 3 onward.
- `apps/hospitals/models.py` — `Hospital`, `BedInventory` (per bed type), `Doctor`, `Equipment`.
  `BedInventory.available_count` is the field the booking flow will auto-decrement/increment (Day 11).
- `apps/bookings/models.py` — `Booking` with the full state machine
  (`requested → confirmed/rejected → completed/cancelled/no_show`, plus `escalated` for emergency SLA timeouts),
  deposit fields (Day 13), and an audit trail (`device_id`, `ip_address`, geolocation) for fraud review (Day 25).
  `BookingStatusLog` gives you an immutable history of every status change.

## Next (Day 2)
- Build signup/login API (`apps/users/urls.py` + views)
- Integrate OTP verification
- Build frontend login/signup screens

Tell Claude "let's do Day 2" and we'll build the next 3 tasks the same way.
