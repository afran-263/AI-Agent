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

A tool schema is a structured contract that defines how an AI assistant can safely and correctly interact with a tool, API, database operation, or external system.

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

A complete tool schema typically contains:

```json
{
  "name": "",
  "description": "",
  "input_schema": {},
  "output_schema": {},
  "risk_level": "",
  "approval_required": false
}
```
* An **input schema** defines the structure of data a tool expects to receive before it can execute.
  
Example

Tool: get_employee
```json
{
  "type": "object",
  "properties": {
    "employee_id": {
      "type": "string"
    }
  },
  "required": ["employee_id"]
}
```
* An **output schema** defines the structure of data returned by the tool after execution.

Example

Tool: get_employee
```
{
  "type": "object",
  "properties": {
    "employee_id": { "type": "string" },
    "name": { "type": "string" },
    "department": { "type": "string" }
  }
}
```
---

## API-to-Tool Mapping

A tool usually wraps one backend API.
API-to-Tool Mapping is the process of converting backend APIs into AI-usable tools.
A backend system exposes functionality through APIs, while an AI assistant interacts through tools. Mapping creates a bridge between them.

Without Mapping
```
User
  ↓
Assistant
  ↓
Unknown Backend API
```
With Mapping
With Mapping
User
  ↓
Assistant
  ↓
Tool
  ↓
API
  ↓
Backend System

Example:

API:
POST /employees

Tool:
create_employee()

* Input schema mirrors API request body.

* Output schema mirrors API response.

## Basic Mapping Process
## Step 1: Identify APIs

Assume the HRMS backend exposes the following APIs:

```http
GET    /employees/{id}
GET    /employees
POST   /employees
PUT    /employees/{id}
DELETE /employees/{id}
```

These APIs provide functionality for retrieving, creating, updating, and deleting employee records.

---

## Step 2: Convert APIs into Tools

Each API endpoint is mapped to a corresponding tool that the AI can invoke.

| API Endpoint           | Tool Name        |
| ---------------------- | ---------------- |
| GET /employees/{id}    | get_employee     |
| GET /employees         | search_employees |
| POST /employees        | create_employee  |
| PUT /employees/{id}    | update_employee  |
| DELETE /employees/{id} | delete_employee  |

The tool names are designed to be descriptive and easy for the AI to understand.

---

## Step 3: Define Tool Schemas

Each tool requires an input schema that specifies the parameters needed to execute the underlying API.

### Example: `get_employee`

Backend API:

```http
GET /employees/{id}
```

Tool Definition:

```json
{
  "name": "get_employee",
  "description": "Retrieve employee details by employee ID",
  "input_schema": {
    "type": "object",
    "properties": {
      "employee_id": {
        "type": "string"
      }
    },
    "required": ["employee_id"]
  }
}
```

The schema acts as a contract between the AI and the backend service, ensuring that valid data is provided before execution.

---

## Step 4: Define Execution Logic

When a user asks for employee information, the AI invokes the appropriate tool.

### Tool Call

```json
{
  "tool": "get_employee",
  "employee_id": "EMP001"
}
```

### Mapping Layer

The tool layer converts the tool request into the corresponding API request.

```http
GET /employees/EMP001
```

### API Response

```json
{
  "id": "EMP001",
  "name": "John Doe",
  "department": "Engineering"
}
```

### Tool Output

```json
{
  "employee_id": "EMP001",
  "name": "John Doe",
  "department": "Engineering"
}
```

The AI then formats this information into a user-friendly response.

---

## End-to-End Flow

```text
User Request
      ↓
AI Assistant
      ↓
Tool Selection
(get_employee)
      ↓
Input Validation
      ↓
API Mapping
(GET /employees/EMP001)
      ↓
Backend HRMS
      ↓
API Response
      ↓
Tool Output
      ↓
AI Response to User
```

This mapping layer enables seamless integration between AI agents and enterprise HRMS systems while maintaining validation, consistency, and security.

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
