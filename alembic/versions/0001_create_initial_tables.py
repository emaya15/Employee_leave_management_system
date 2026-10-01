"""create initial tables

Revision ID: 0001
Revises:
Create Date: 2026-09-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    # ---------- departments ----------
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("department_name", sa.String(100), nullable=False),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("department_name"),
    )
    op.create_index("ix_departments_id", "departments", ["id"])

    # ---------- employees ----------
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(10), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("designation", sa.String(100), nullable=False),
        sa.Column("salary", sa.Numeric(10, 2), nullable=False),
        sa.Column("date_of_joining", sa.Date(), nullable=False),
        sa.Column(
            "employment_type",
            sa.Enum("Full-Time", "Part-Time", "Intern", "Contract",
                    name="employmenttype"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"],
                                ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_code"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_employees_id", "employees", ["id"])
    op.create_index("ix_employees_name", "employees", ["name"])
    op.create_index("ix_employees_department_id", "employees", ["department_id"])

    # ---------- users ----------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(120), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("Admin", "HR", "Employee", name="userrole"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"],
                                ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ---------- leave_requests ----------
    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column(
            "leave_type",
            sa.Enum("Sick", "Casual", "Earned", name="leavetype"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("total_days", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("Pending", "Approved", "Rejected", "Cancelled",
                    name="leavestatus"),
            nullable=False,
        ),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"],
                                ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"],
                                ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leave_requests_id", "leave_requests", ["id"])
    op.create_index("ix_leave_requests_employee_id", "leave_requests", ["employee_id"])
    op.create_index("ix_leave_requests_status", "leave_requests", ["status"])


def downgrade() -> None:
    op.drop_table("leave_requests")
    op.drop_table("users")
    op.drop_table("employees")
    op.drop_table("departments")
