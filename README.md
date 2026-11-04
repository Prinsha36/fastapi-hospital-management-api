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
- **Pagination** on every list endpoint (`?limit=20&offset=0`)
- **Clear error messages**, for example `409 Department 'Cardiology' already exists`
- **Automatic API docs** with Swagger UI
- **33 automated tests** with pytest

## Tech Stack

| Tool | Purpose |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | Web framework |
| [PostgreSQL](https://www.postgresql.org/) | Database |
| [asyncpg](https://github.com/MagicStack/asyncpg) | Async PostgreSQL driver |
| [Pydantic](https://docs.pydantic.dev/) | Request validation |
| [pytest](https://docs.pytest.org/) | Testing |

## Project Structure

```
.
├── app/
│   ├── main.py              # App setup, startup/shutdown, router registration
│   ├── database.py          # PostgreSQL connection pool
│   ├── schema.sql           # Tables and sample data
│   ├── routes/              # HTTP endpoints (status codes, errors)
│   │   ├── departments.py
│   │   ├── doctors.py
│   │   ├── patients.py
│   │   ├── appointments.py
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

Edit `.env` and put in your PostgreSQL username and password:

```
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/hospital_db
```

### 5. Create the tables and sample data

```bash
psql "postgresql://USER:PASSWORD@localhost:5432/hospital_db" -f app/schema.sql
```

This creates all tables and adds sample departments, doctors, patients and appointments. It is safe to run again; existing data is skipped.

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** to see and try every endpoint.

## API Endpoints

### General

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/health` | Checks the database connection |

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

## Error Responses

| Code | Meaning | Example |
|---|---|---|
| 400 | Invalid reference or rule broken | Department does not exist, appointment in the past |
| 404 | Record not found | `Patient 99 not found` |
| 409 | Duplicate | Department name or doctor email already used, doctor already booked |
| 422 | Invalid request body | Missing field, wrong date format, invalid status |

## Database Rules

- Department names and doctor emails must be unique.
- Deleting a department keeps its doctors; their `department_id` becomes empty.
- Deleting a patient or doctor also deletes their appointments.
- A doctor can't have two active appointments at the same time. Cancelled ones don't count.

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

- [ ] Staff login with JWT authentication
- [ ] Response models for cleaner API docs
- [ ] Stricter validation (phone, email, blood group)
