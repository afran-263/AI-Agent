# AI Agent Tool Workflow

The HRMS Agent uses tools generated from the OpenAPI specification. These tools allow the AI agent to retrieve real employee and task data instead of generating responses from memory.

## Available Tools

### 1. GetEmployeeList

**Purpose**

Retrieves a list of employees from the HRMS system.

**API Endpoint**

```http
GET /api/hrms/employees
```

**Example User Prompt**

```text
List all employees
```

**Agent Workflow**

```text
User Prompt
      │
      ▼
Agent selects GetEmployeeList tool
      │
      ▼
GET /api/hrms/employees
      │
      ▼
HrmsController.GetEmployeeList()
      │
      ▼
HrmsDataService.GetAllEmployees()
      │
      ▼
Employee Data Returned
      │
      ▼
Agent formats response
```

---

### 2. GetEmployeeDetails

**Purpose**

Retrieves detailed information about a specific employee using the employee ID.

**API Endpoint**

```http
GET /api/hrms/employees/{id}
```

**Example User Prompt**

```text
Show details of employee 1
```

**Agent Workflow**

```text
User Prompt
      │
      ▼
Agent identifies Employee ID = 1
      │
      ▼
Selects GetEmployeeDetails tool
      │
      ▼
GET /api/hrms/employees/1
      │
      ▼
HrmsController.GetEmployeeDetails(1)
      │
      ▼
HrmsDataService.GetEmployeeById(1)
      │
      ▼
Employee Object Returned
      │
      ▼
Agent generates natural language response
```

---

### 3. GetTaskList

**Purpose**

Retrieves task information from the HRMS system.

**API Endpoint**

```http
GET /api/hrms/tasks
```

**Example User Prompt**

```text
Show tasks assigned to employee 1
```

**Agent Workflow**

```text
User Prompt
      │
      ▼
Agent selects GetTaskList tool
      │
      ▼
GET /api/hrms/tasks?employeeId=1
      │
      ▼
HrmsController.GetTaskList()
      │
      ▼
HrmsDataService.GetTasks()
      │
      ▼
Task Data Returned
      │
      ▼
Agent summarizes tasks
```

---

# End-to-End Tool Execution Flow

```text
User Prompt
      │
      ▼
Azure AI Foundry Agent
      │
      ▼
Tool Selection
      │
      ▼
OpenAPI Tool Definition
      │
      ▼
HTTP API Request
      │
      ▼
ASP.NET Controller
      │
      ▼
HRMS Data Service
      │
      ▼
Seed Data
      │
      ▼
JSON Response
      │
      ▼
Agent Formats Response
      │
      ▼
User
```

---

# How the Agent Discovers Tools

The tools are automatically generated from the OpenAPI specification

Each API operation contains an `operationId`.

Example:

```json
{
  "operationId": "GetEmployeeDetails"
}
```

Azure AI Foundry converts this operation into an AI Tool:

```text
Tool Name:
GetEmployeeDetails
```

When a user asks:

```text
What is the name of employee 1?
```

The agent:

1. Selects the **GetEmployeeDetails** tool.
2. Extracts `id = 1`.
3. Calls:

```http
GET /api/hrms/employees/1
```

4. Receives employee data.
5. Generates the final response.

---
