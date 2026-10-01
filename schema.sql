-- Employee & Leave Management System
-- MySQL schema
-- This file is provided as a SQL schema/reference script.
-- Alembic remains the migration tool used by the application.

CREATE DATABASE IF NOT EXISTS employee_leave_db;
USE employee_leave_db;

-- 1. Departments
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(150) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Employees
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(10) NOT NULL,
    department_id INT NOT NULL,
    designation VARCHAR(100) NOT NULL,
    salary DECIMAL(12,2) NOT NULL,
    date_of_joining DATE NOT NULL,
    employment_type ENUM('Full-Time', 'Part-Time', 'Intern', 'Contract') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_employee_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_employee_salary
        CHECK (salary > 0)
);

-- 3. Users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'HR', 'Employee') NOT NULL DEFAULT 'Employee',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    employee_id INT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_employee
        FOREIGN KEY (employee_id)
        REFERENCES employees(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- 4. Leave Requests
CREATE TABLE IF NOT EXISTS leave_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    leave_type ENUM('Sick', 'Casual', 'Earned') NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days INT NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected', 'Cancelled')
        NOT NULL DEFAULT 'Pending',
    approved_by INT NULL,
    rejection_reason TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_leave_employee
        FOREIGN KEY (employee_id)
        REFERENCES employees(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_leave_approved_by
        FOREIGN KEY (approved_by)
        REFERENCES users(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT chk_leave_total_days
        CHECK (total_days > 0),

    CONSTRAINT chk_leave_dates
        CHECK (end_date >= start_date)
);

-- Helpful indexes for filtering/searching.
CREATE INDEX idx_employees_department_id
    ON employees(department_id);

CREATE INDEX idx_employees_is_active
    ON employees(is_active);

CREATE INDEX idx_leave_employee_id
    ON leave_requests(employee_id);

CREATE INDEX idx_leave_status
    ON leave_requests(status);

CREATE INDEX idx_leave_type
    ON leave_requests(leave_type);

CREATE INDEX idx_leave_start_date
    ON leave_requests(start_date);

CREATE INDEX idx_leave_end_date
    ON leave_requests(end_date);

CREATE INDEX idx_leave_approved_by
    ON leave_requests(approved_by);
