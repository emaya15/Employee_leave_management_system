# Employee & Leave Management System

Built a complete backend system using **FastAPI**, **SQLAlchemy**, **MySQL** and **Alembic**.

## 1. Project description
An API for managing departments, employees and leave requests. Users log in with JWT tokens, and what they can do depends on their role (Admin, HR, Employee).

## 2. Features
- Register / login with JWT (30-minute tokens), bcrypt password hashing
- Role-based access: Admin, HR, Employee
- Department and employee management (employee delete is a **soft delete**)
- Leave requests with automatic day calculation (weekends skipped), yearly balance, overlap check, approve / reject / cancel
- Pagination, search, filtering and sorting
- Reports: dashboard and monthly leave summary
- Database tables created only by **Alembic migrations** (no `create_all()`)

## 3. Tech stack
Python 3.9+, FastAPI, Pydantic v2, SQLAlchemy 2, MySQL, Alembic, python-jose (JWT), Passlib + bcrypt, Uvicorn.

## 4. Project structure
```text
employee_leave_management/
├── app/
│   ├── main.py          # creates the FastAPI app and includes routers
│   ├── config.py        # reads .env settings
│   ├── database.py      # engine, session, Base, get_db
│   ├── models/          # SQLAlchemy tables (user, department, employee, leave)
│   ├── schemas/         # Pydantic validation (auth, department, employee, leave, report)
│   ├── routers/         # API endpoints only (no business rules)
│   ├── services/        # business logic and rules
│   └── auth/            # password.py, jwt.py, dependencies.py
├── alembic/             # migrations (versions/0001_create_initial_tables.py)
├── alembic.ini
├── .env.example
├── requirements.txt
└── README.md
```
Two small extra files were added: `app/config.py` (settings) and `app/schemas/report.py` (report response shapes).

## 5. Environment setup

### Create the MySQL database
```sql
CREATE DATABASE employee_leave_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Configure `.env`
```bash
cp .env.example .env        # Windows: copy .env.example .env
```
Edit `.env`:
```env
DATABASE_URL=mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/employee_leave_db
SECRET_KEY=paste-a-long-random-string-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```
Generate a secret key: `python -c "import secrets; print(secrets.token_hex(32))"`.
If your password has special characters (`@`, `#`, `%`), URL-encode them (`@` becomes `%40`).

### Virtual environment and dependencies
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 6. Alembic migrations

This project already contains Alembic configured and one initial migration, so you do **not** need `alembic init`. For reference, the commands used to build it were:
```bash
alembic init alembic                                            # creates the alembic/ folder (already done)
alembic revision --autogenerate -m "create initial tables"      # creates a migration file
alembic upgrade head                                            # applies it to MySQL
```
**To create the tables, just run:**
```bash
alembic upgrade head
```
Useful extras: `alembic current` (which version is applied), `alembic history`, `alembic downgrade -1` (undo the last migration).

### How Alembic detects model changes
1. `alembic/env.py` imports `app.models`, so every model registers its table on `Base.metadata`.
2. `target_metadata = Base.metadata` tells Alembic what the tables *should* look like.
3. `alembic revision --autogenerate` connects to MySQL, reads what the tables *actually* look like, and writes the differences (new table, new column, ...) into a migration file in `alembic/versions/`.
4. `alembic upgrade head` runs the migration files that have not run yet.

Always **read the generated file** before upgrading. Example: after adding a column to a model, run `alembic revision --autogenerate -m "add column"` then `alembic upgrade head`.

Want to generate the initial migration yourself instead? Delete the file in `alembic/versions/`, make sure the database is empty, then run the autogenerate command above.

## 7. Run the server
```bash
uvicorn app.main:app --reload
```
Swagger UI: http://127.0.0.1:8000/docs (ReDoc: `/redoc`).

## 8. Authentication instructions
1. **First account:** call `POST /auth/register`. The very first account in an empty database automatically becomes **Admin**.
2. **Log in:** in Swagger click **Authorize** (top right), enter your email as *username* and your password. Or call `POST /auth/login` (form data) and copy the `access_token`.
3. For Postman: use `Authorization: Bearer <access_token>`.
4. After the first account exists, anyone can register as `Employee`, but only a logged-in **Admin** can create `HR` or `Admin` accounts.

### How `users` and `employees` are related
- `users` = login accounts (email, password hash, role).
- `employees` = HR records (code, salary, department, ...).
- `users.employee_id` links an account to an employee record (one-to-one, optional).
- The link is made automatically when the **email is the same**: either the employee is created after the account, or the account registers after the employee record exists.
- Leave APIs use `users.employee_id` to know "who am I". A user without an employee record cannot apply for leave (Admin needs an employee record too if they want to apply).

## 9. Roles and permissions
| Action | Admin | HR | Employee |
|---|:-:|:-:|:-:|
| Create HR/Admin accounts | Yes | No | No |
| Create / update / delete departments | Yes | No | No |
| View departments | Yes | Yes | Yes |
| List employees, department employees | Yes | Yes | No |
| Create / update / delete employees | Yes | Yes | No |
| View one employee | Any | Any | Own only |
| Apply for leave | Yes* | Yes* | Yes* |
| View leaves / balance | All | All | Own only |
| Approve / reject leave | Yes | Yes (not own) | No |
| Cancel a pending leave | Any | Own | Own |
| Reports | Yes | Yes | No |

\* needs a linked employee record.

## 10. API endpoints
| Method | Path | Who |
|---|---|---|
| POST | `/auth/register` | Public (see rules above) |
| POST | `/auth/login` | Public |
| GET | `/auth/me` | Logged in |
| POST | `/departments` | Admin |
| GET | `/departments`, `/departments/{id}` | Logged in |
| PUT / DELETE | `/departments/{id}` | Admin |
| GET | `/departments/{id}/employees` | HR, Admin |
| POST | `/employees` | HR, Admin |
| GET | `/employees` | HR, Admin |
| GET | `/employees/{id}` | HR, Admin, or the employee themselves |
| PUT / DELETE | `/employees/{id}` | HR, Admin |
| POST | `/leaves` | Logged in |
| GET | `/leaves`, `/leaves/{id}` | Logged in (employees see own only) |
| GET | `/employees/{id}/leaves`, `/employees/{id}/leave-balance?year=2026` | HR, Admin, or that employee |
| PUT | `/leaves/{id}/approve`, `/leaves/{id}/reject` | HR, Admin |
| PUT | `/leaves/{id}/cancel` | Owner (or Admin) |
| GET | `/reports/dashboard` | HR, Admin |
| GET | `/reports/leave-summary?month=9&year=2026` | HR, Admin |

### List query parameters
- All lists: `skip` (default 0), `limit` (default 10, max 100)
- `/employees`: `name` (partial), `department_id`, `designation` (partial), `employment_type`, `is_active`, `sort_by` (`id|name|salary|date_of_joining|employee_code|created_at`), `order` (`asc|desc`)
- `/leaves`: `status`, `leave_type`, `employee_id`, `from_date`, `to_date` (leaves overlapping that range)

## 11. Example requests and responses

**Register** `POST /auth/register`
```json
{ "full_name": "Asha Admin", "email": "admin@example.com", "password": "Admin@1234" }
```
Response `201`:
```json
{ "id": 1, "full_name": "Asha Admin", "email": "admin@example.com", "role": "Admin", "is_active": true, "employee_id": null }
```

**Login** `POST /auth/login` (form fields `username`, `password`)
```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer" }
```

**Create department** `POST /departments`
```json
{ "department_name": "Engineering", "location": "Chennai" }
```

**Create employee** `POST /employees`
```json
{
  "employee_code": "EMP001", "name": "Ravi Kumar", "email": "ravi@example.com",
  "phone": "9876543210", "department_id": 1, "designation": "Developer",
  "salary": 50000, "date_of_joining": "2026-01-15", "employment_type": "Full-Time"
}
```

**Apply for leave** `POST /leaves` (logged in as an employee)
```json
{ "leave_type": "Casual", "start_date": "2026-10-12", "end_date": "2026-10-14", "reason": "Family function" }
```
Response `201`:
```json
{
  "id": 1, "employee_id": 1, "leave_type": "Casual", "start_date": "2026-10-12",
  "end_date": "2026-10-14", "total_days": 3, "reason": "Family function",
  "status": "Pending", "approved_by": null, "rejection_reason": null,
  "created_at": "2026-09-30T10:00:00", "updated_at": "2026-09-30T10:00:00"
}
```

**Reject leave** `PUT /leaves/1/reject`
```json
{ "rejection_reason": "Project deadline that week" }
```

**Leave balance** `GET /employees/1/leave-balance?year=2026`
```json
{
  "employee_id": 1, "year": 2026,
  "balances": [
    { "leave_type": "Sick", "allocated": 12, "used": 0, "pending": 0, "available": 12 },
    { "leave_type": "Casual", "allocated": 10, "used": 3, "pending": 0, "available": 7 },
    { "leave_type": "Earned", "allocated": 15, "used": 0, "pending": 0, "available": 15 }
  ]
}
```

**Dashboard** `GET /reports/dashboard`
```json
{
  "total_employees": 50, "active_employees": 46,
  "employees_per_department": [ { "department_id": 1, "department_name": "Engineering", "employee_count": 20 } ],
  "pending_leave_requests": 5, "employees_on_leave_today": 3
}
```

**Leave summary** `GET /reports/leave-summary?month=9&year=2026`
```json
{ "month": 9, "year": 2026,
  "summary": [ { "leave_type": "Casual", "status": "Approved", "request_count": 4, "total_days": 9 } ] }
```

## 12. Error handling
Errors always look like `{"detail": "message"}`.

| Code | Meaning | Example |
|---|---|---|
| 400 | Bad request / business rule broken | "Insufficient Casual leave balance (requested 5, available 2)" |
| 401 | Missing, invalid or expired token | "Invalid or expired token" |
| 403 | Role not allowed / inactive user | "Admin access required" |
| 404 | Record not found | "Employee not found" |
| 409 | Duplicate or conflict | "Employee with this email already exists", "Leave request overlaps with an existing leave" |
| 422 | Validation error (bad phone, salary <= 0, future joining date, bad enum) | FastAPI lists the invalid fields |

## 13. Leave rules (all in `app/services/leave_service.py`)
Yearly balance: Sick 12, Casual 10, Earned 15. Balance is deducted only when a leave is **approved**; it is checked when applying and again when approving. Weekends are not counted. A single request must stay within one calendar year.

## 14. Suggested testing order (Swagger)
1. Register the first user, so you have an Admin. Login and Authorize.
2. `POST /departments`, then `GET /departments`.
3. `POST /employees` (use the Admin's email if the Admin should also apply for leave).
4. Register another user with the employee's email, log in as them (Authorize again).
5. `POST /leaves`, check `GET /employees/{id}/leave-balance`.
6. Log in as Admin, `PUT /leaves/{id}/approve`, check the balance again.
7. Try errors: duplicate email (409), wrong phone (422), no token (401), employee calling `/reports/dashboard` (403).
8. Try `GET /employees?name=rav&sort_by=salary&order=desc`.

## 15. GitHub setup
```bash
git init
git add .
git status                 # make sure .env is NOT listed
git commit -m "Initial commit: employee leave management API"
git branch -M main
git remote add origin https://github.com/<your-username>/employee_leave_management.git
git push -u origin main
```
`.gitignore` already excludes `.env` and `venv/`. Only `.env.example` is committed.

## 16. Common problems
- **`ModuleNotFoundError: app`** - run commands from the project root folder (where `alembic.ini` is).
- **`Access denied for user`** - check username/password in `DATABASE_URL`.
- **`Unknown database`** - create the database first (step 5).
- **`Table ... doesn't exist`** - run `alembic upgrade head`.
- **bcrypt errors** - keep the pinned versions `passlib==1.7.4` and `bcrypt==4.0.1`.
