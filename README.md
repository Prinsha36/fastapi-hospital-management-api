# Hospital Management System API

A REST API for managing hospital data: departments, doctors, patients and appointments. Built with **FastAPI** and **PostgreSQL**, using raw SQL through `asyncpg`.

## Features

- **Departments**: create, list, update and delete hospital departments
- **Doctors**: each doctor can belong to a department
- **Patients**: store patient details, with search by name
- **Appointments**: book a patient with a doctor at a date and time
  - A doctor can't be double-booked at the same time
  - Appointments can't be booked in the past
  - Cancelling an appointment frees the time slot
- **Emergency department**: register walk-in patients and treat the most serious first
  - Triage levels: `critical`, `urgent`, `less_urgent`, `non_urgent`
  - A live queue sorted by triage level, then arrival time
  - Unknown patients (e.g. unconscious) can be registered by description and identified later
  - Only Emergency Medicine doctors can take a case
- **Staff login with JWT**: reading is open, changing data needs a login, deleting needs an admin
- **Pagination** on every list endpoint (`?limit=20&offset=0`)
- **Clear error messages**, for example `409 Department 'Cardiology' already exists`
- **Automatic API docs** with Swagger UI
- **Input validation**: phone, email, blood group, gender and date of birth are checked and cleaned up
- **92 automated tests** with pytest

## Tech Stack

| Tool | Purpose |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | Web framework |
| [PostgreSQL](https://www.postgresql.org/) | Database |
| [asyncpg](https://github.com/MagicStack/asyncpg) | Async PostgreSQL driver |
| [Pydantic](https://docs.pydantic.dev/) | Request validation |
| [PyJWT](https://pyjwt.readthedocs.io/) | Login tokens |
| [pwdlib](https://github.com/frankie567/pwdlib) | Password hashing (Argon2) |
| [pytest](https://docs.pytest.org/) | Testing |

## Project Structure

```
.
├── app/
│   ├── main.py              # App setup, startup/shutdown, router registration
│   ├── database.py          # PostgreSQL connection pool
│   ├── schema.sql           # Tables and sample data
│   ├── core/
│   │   ├── security.py      # Password hashing and JWT tokens
│   │   └── auth.py          # Login checks used by protected routes
│   ├── routes/              # HTTP endpoints (status codes, errors)
│   │   ├── auth.py
│   │   ├── departments.py
│   │   ├── doctors.py
│   │   ├── patients.py
│   │   ├── appointments.py
│   │   ├── emergency.py
│   │   └── pagination.py    # Shared limit/offset parameters
│   ├── schemas/             # Pydantic models for request bodies
│   └── services/            # SQL queries
├── tests/                   # pytest tests
├── .env.example             # Template for environment variables
├── pytest.ini
└── requirements.txt
```

Each feature is split into three layers:

- **routes**: receive the request and return the response
- **services**: talk to the database
- **schemas**: define and validate what the request body must look like

## Getting Started

### 1. Prerequisites

- Python 3.11 or newer
- PostgreSQL

### 2. Clone and install

```bash
git clone https://github.com/Prinsha36/fastapi-hospital-management-api.git
cd fastapi-hospital-management-api

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create the database

```bash
createdb hospital_db
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your PostgreSQL username and password, plus a secret key for login tokens:

```
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/hospital_db
SECRET_KEY=your-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Generate a secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Create the tables and sample data

```bash
psql "postgresql://USER:PASSWORD@localhost:5432/hospital_db" -f app/schema.sql
```

This creates all tables and adds sample departments, doctors, patients, appointments and emergency cases. It is safe to run again; existing data is skipped.

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** to see and try every endpoint.

### 7. Create the first admin account

The first account can be created without logging in, and it automatically becomes an **admin**:

```json
POST /auth/register
{
  "username": "admin",
  "password": "choose-a-strong-password",
  "full_name": "Hospital Admin"
}
```

After that, only a logged-in admin can create more accounts.

## Authentication

| Action | Who can do it |
|---|---|
| `GET` (read data) | Anyone |
| `POST`, `PUT`, `PATCH` (create and edit) | Any logged-in user (staff or admin) |
| `DELETE` | Admins only |
| Create or delete user accounts | Admins only |

**Log in in Swagger:** open `/docs`, click **Authorize** at the top right, enter your username and password, and click **Authorize**. Swagger then sends your token with every request.

**Log in with curl:**

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=admin&password=choose-a-strong-password"
# → {"access_token": "eyJhbGciOi...", "token_type": "bearer"}

curl -X POST http://127.0.0.1:8000/patients/ \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Bishal Lama"}'
```

Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (60 by default). Log in again to get a new one.

## API Endpoints

### General

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/health` | Checks the database connection |

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create a user (first user is free and becomes admin; then admins only) |
| POST | `/auth/login` | Log in with username and password, returns a token |
| GET | `/auth/me` | Show the logged-in user |
| GET | `/auth/users` | List users (admins only) |
| DELETE | `/auth/users/{id}` | Delete a user (admins only) |

### Departments

| Method | Endpoint | Description |
|---|---|---|
| GET | `/departments/` | List departments |
| GET | `/departments/{id}` | Get one department |
| GET | `/departments/{id}/doctors` | List doctors in a department |
| POST | `/departments/` | Create a department |
| PUT | `/departments/{id}` | Replace a department |
| PATCH | `/departments/{id}` | Update some fields |
| DELETE | `/departments/{id}` | Delete a department |

### Doctors

| Method | Endpoint | Description |
|---|---|---|
| GET | `/doctors/` | List doctors |
| GET | `/doctors/{id}` | Get one doctor |
| GET | `/doctors/{id}/appointments` | List a doctor's appointments |
| POST | `/doctors/` | Create a doctor |
| PUT | `/doctors/{id}` | Replace a doctor |
| PATCH | `/doctors/{id}` | Update some fields |
| DELETE | `/doctors/{id}` | Delete a doctor |

### Patients

| Method | Endpoint | Description |
|---|---|---|
| GET | `/patients/` | List patients (search with `?name=`) |
| GET | `/patients/{id}` | Get one patient |
| GET | `/patients/{id}/appointments` | List a patient's appointments |
| POST | `/patients/` | Create a patient |
| PUT | `/patients/{id}` | Replace a patient |
| PATCH | `/patients/{id}` | Update some fields |
| DELETE | `/patients/{id}` | Delete a patient |

### Appointments

| Method | Endpoint | Description |
|---|---|---|
| GET | `/appointments/` | List appointments (filter by `patient_id`, `doctor_id`, `status`, `date`) |
| GET | `/appointments/{id}` | Get one appointment |
| POST | `/appointments/` | Book an appointment |
| PUT | `/appointments/{id}` | Replace an appointment |
| PATCH | `/appointments/{id}` | Update some fields, e.g. cancel |
| DELETE | `/appointments/{id}` | Delete an appointment |

### Emergency

| Method | Endpoint | Description |
|---|---|---|
| GET | `/emergency/` | List all cases, newest first (filter by `status`, `triage_level`, `patient_id`, `doctor_id`) |
| GET | `/emergency/queue` | Patients waiting to be seen, most serious first |
| GET | `/emergency/{id}` | Get one case |
| POST | `/emergency/` | Register an arriving patient |
| PATCH | `/emergency/{id}` | Change triage level, complaint or patient while the case is open |
| PATCH | `/emergency/{id}/assign` | Give the case to a doctor and start treatment |
| PATCH | `/emergency/{id}/close` | Discharge, admit or transfer the patient |
| DELETE | `/emergency/{id}` | Delete a case (admin only) |

A case moves through these steps, and can't go backwards:

```
waiting  →  in_treatment  →  discharged / admitted / transferred
```

### Pagination

Every list endpoint accepts:

| Parameter | Default | Description |
|---|---|---|
| `limit` | 20 | How many rows to return (1–100) |
| `offset` | 0 | How many rows to skip |

Example: page 2 with 10 per page is `GET /patients/?limit=10&offset=10`.

## Example Requests

**Create a department**

```bash
curl -X POST http://127.0.0.1:8000/departments/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Urology", "description": "Urinary tract and kidney conditions."}'
```

**Create a doctor**

```json
POST /doctors/
{
  "name": "Dr. Ramesh Koirala",
  "specialization": "Urologist",
  "phone": "9800000011",
  "email": "ramesh.koirala@hospital.com",
  "department_id": 1
}
```

**Book an appointment**

```json
POST /appointments/
{
  "patient_id": 1,
  "doctor_id": 1,
  "appointment_time": "2026-12-10T10:30",
  "reason": "Follow-up checkup"
}
```

`status` defaults to `scheduled`. Allowed values: `scheduled`, `completed`, `cancelled`.

**Cancel an appointment**

```json
PATCH /appointments/1
{ "status": "cancelled" }
```

**Register an emergency patient**

```json
POST /emergency/
{
  "patient_id": 1,
  "complaint": "Severe chest pain",
  "triage_level": "critical"
}
```

For an unknown patient, send `patient_description` instead of `patient_id`, e.g. `"Unknown male, around 30"`. Link the real patient later with `PATCH /emergency/{id}` and `{"patient_id": 12}`.

**Assign a doctor, then close the case**

```json
PATCH /emergency/1/assign
{ "doctor_id": 10 }

PATCH /emergency/1/close
{ "outcome": "admitted", "notes": "Moved to cardiology ward" }
```

The doctor must be in the **Emergency Medicine** department, otherwise you get `400`. In the sample data that is Dr. Kiran Bhandari. Find their ID with `GET /departments/{id}/doctors` or `GET /doctors/`.

## Error Responses

| Code | Meaning | Example |
|---|---|---|
| 400 | Invalid reference or rule broken | Department does not exist, appointment in the past |
| 404 | Record not found | `Patient 99 not found` |
| 409 | Duplicate or wrong step | Department name or doctor email already used, doctor already booked, emergency case already closed |
| 422 | Invalid request body | Missing field, wrong date format, invalid status |

## Validation Rules

Invalid input returns **422** with a message naming the field. Some values are cleaned up automatically.

| Field | Rule | Cleaned up |
|---|---|---|
| Names | 2–100 characters, not blank | Extra spaces trimmed |
| Phone | 7–15 digits, optional leading `+` | `+977 980-000-0001` → `+9779800000001` |
| Email | Valid format, e.g. `name@hospital.com` | |
| Blood group | `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-` | `ab+` → `AB+` |
| Gender | `Male`, `Female`, `Other` | `female` → `Female` |
| Date of birth | Not in the future, not before 1900 | |
| IDs | Positive numbers | |
| Username | 3–50 letters, numbers, `_` or `.` | |
| Password | 6–128 characters | |

All rules live in [`app/schemas/common.py`](app/schemas/common.py).

## Database Rules

- Department names and doctor emails must be unique.
- Deleting a department keeps its doctors; their `department_id` becomes empty.
- Deleting a patient or doctor also deletes their appointments.
- A doctor can't have two active appointments at the same time. Cancelled ones don't count.
- A patient can only have one open emergency case at a time.
- An emergency case needs either a patient or a description of an unknown patient.
- Deleting a patient also deletes their emergency cases. Deleting a doctor keeps the case; its `doctor_id` becomes empty.

## Running Tests

```bash
pytest          # short output
pytest -v       # show each test
```

Tests create their own records with unique names and delete them afterwards, so existing data is not changed.

To run tests against a separate database, create it and add this to `.env`. The tests create the tables themselves:

```
TEST_DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/hospital_test
```

## Roadmap

- [x] Staff login with JWT authentication
- [ ] Response models for cleaner API docs
- [x] Stricter validation (phone, email, blood group)
- [x] Emergency department with triage queue
