# app/main.py
# The entry point. Start it with:  uvicorn app.main:app --reload
# NOTE: there is no Base.metadata.create_all() here - tables come from Alembic migrations.
from fastapi import FastAPI

from app.routers import auth, departments, employees, leaves, reports

app = FastAPI(
    title="Employee & Leave Management System",
    description="Backend API for managing employees and their leave requests.",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(leaves.router)
app.include_router(leaves.employee_leaves_router)
app.include_router(reports.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Employee & Leave Management API is running. Open /docs for Swagger."}
