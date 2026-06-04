# Tool Safety Rules

## Rule 1: Validate Inputs

Every tool call must validate:

- Required fields
- Data types
- Business constraints
- Authorization

Example:

employee_id must exist.

---

## Rule 2: Principle of Least Privilege

Tools should only access data necessary for the task.

Example:

Managers can view team members only.

---

## Rule 3: Approval for High-Risk Actions

Require explicit user confirmation for:

- Salary updates
- Payroll processing
- Employee termination
- Record deletion

---

## Rule 4: Audit Logging

Log:

- User
- Timestamp
- Tool name
- Inputs
- Outputs
- Result

---

## Rule 5: Prevent Destructive Actions

Never execute:

- Delete employee
- Delete payroll
- Delete audit logs

without approval.

---

## Rule 6: Sensitive Data Protection

Mask:

- Bank account numbers
- Tax IDs
- Personal identifiers

Example:

XXXXXX1234

---

## Rule 7: Error Handling

Return structured errors.

Example:

{
  "success": false,
  "error": {
    "code": "EMPLOYEE_NOT_FOUND",
    "message": "Employee does not exist"
  }
}

---

## Rule 8: Human-in-the-Loop

Require approval before:

- Payroll runs
- Salary revisions
- Employee termination
- Mass updates

---

## Rule 9: Rate Limiting

Protect against abuse.

Examples:

- Max 100 searches/minute
- Max 10 payroll actions/hour

---

## Rule 10: Compliance

Ensure compliance with:

- GDPR
- HIPAA (if applicable)
- Company HR policies
- Local labor regulations
