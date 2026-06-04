# Tool Design Concepts

## Overview

Tools enable an AI assistant to interact with external systems such as databases, APIs, and enterprise applications.

A tool definition contains:

- Name
- Description
- Input schema
- Output schema
- Safety classification
- Execution rules

---

## Read Tools vs Write Tools

### Read Tools

Read tools retrieve information without modifying data.

Examples:

- Get employee details
- Search leave requests
- Fetch payroll information
- View attendance records

Characteristics:

- Low risk
- No state changes
- Usually auto-executable

Example:

get_employee(employee_id)

Returns employee profile information.

---

### Write Tools

Write tools modify system data.

Examples:

- Create employee
- Approve leave
- Update salary
- Delete records

Characteristics:

- Changes system state
- Higher risk
- May require approval

Example:

approve_leave(leave_id)

Updates leave status.

---

## Tool Schemas

Schemas define:

1. Input parameters
2. Data types
3. Validation rules
4. Output structure

Benefits:

- Prevent invalid calls
- Improve reliability
- Enable tool discovery
- Support automated validation

---

## API-to-Tool Mapping

A tool usually wraps one backend API.

Example:

API:
POST /employees

Tool:
create_employee()

Input schema mirrors API request body.

Output schema mirrors API response.

---

## Risk Classification

### Low Risk

Read-only operations.

Examples:

- Get employee
- Search employees
- View attendance

Action:
Auto-execute.

---

### Medium Risk

Business changes that are reversible.

Examples:

- Create employee
- Update employee profile
- Apply leave

Action:
Execute with logging.

---

### High Risk

Financial, legal, or security impact.

Examples:

- Payroll processing
- Salary changes
- User deactivation

Action:
Require confirmation.

---

### Critical Risk

Destructive operations.

Examples:

- Delete employee
- Delete payroll records
- Remove audit logs

Action:
Mandatory human approval.
