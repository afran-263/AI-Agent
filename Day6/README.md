

# AI Agent Write Tool Workflow

## Purpose

The Write Tool allows the HRMS AI Agent to create new records in the HRMS system instead of only retrieving information.

Unlike read tools such as `GetEmployeeDetails` or `GetTaskList`, a write tool modifies data by creating, updating, or deleting records.

---

## Example Write Tool

### CreateTask

**Purpose**

Create a new task and assign it to an employee.

### API Endpoint

```http
POST /api/hrms/tasks
```

### Tool Schema

```json
{
  "employeeId": "integer",
  "title": "string",
  "description": "string",
  "priority": "string",
  "status": "string",
  "dueDate": "string",
  "assignedBy": "string",
  "category": "string"
}
```

### Example Tool Call

```json
{
  "employeeId": 1,
  "title": "Implement Employee Attendance Dashboard",
  "description": "Develop dashboard for attendance tracking.",
  "priority": "High",
  "status": "Pending",
  "dueDate": "2026-07-15",
  "assignedBy": "Priya Menon",
  "category": "Development"
}
```

---

## Agent Workflow

### User Prompt

```text
Create a high-priority task for employee 1 to implement an attendance dashboard.
```

### Step 1 – Agent Understands Intent

The AI Agent determines that the user wants to create a new task.

```text
Intent: Create Task
```

### Step 2 – Agent Selects Tool

```text
Tool Selected:
CreateTask
```

### Step 3 – Agent Extracts Parameters

```json
{
  "employeeId": 1,
  "title": "Implement Employee Attendance Dashboard",
  "priority": "High"
}
```

### Step 4 – Tool Executes API

```http
POST /api/hrms/tasks
```

Request Body:

```json
{
  "employeeId": 1,
  "title": "Implement Employee Attendance Dashboard",
  "description": "Develop dashboard for attendance tracking.",
  "priority": "High",
  "status": "Pending",
  "dueDate": "2026-07-15",
  "assignedBy": "Priya Menon",
  "category": "Development"
}
```

### Step 5 – Controller Executes

```csharp
CreateTask(CreateTaskRequest request)
```

### Step 6 – Service Saves Data

```csharp
_dataService.AddTask(task);
```

### Step 7 – API Returns Response

```json
{
  "success": true,
  "message": "Task created successfully.",
  "taskId": 111
}
```

### Step 8 – Agent Responds

```text
Task created successfully.

Task ID: 111
Title: Implement Employee Attendance Dashboard
Assigned To: Arjun Nair
Priority: High
Due Date: 2026-07-15
```

---

## End-to-End Flow

```text
User Prompt
      │
      ▼
AI Agent
      │
      ▼
Select CreateTask Tool
      │
      ▼
POST /api/hrms/tasks
      │
      ▼
Controller
      │
      ▼
Service Layer
      │
      ▼
Database / Data Store
      │
      ▼
JSON Response
      │
      ▼
AI Agent
      │
      ▼
User
```

---

## Read Tool vs Write Tool

| Type       | Example            | HTTP Method | Purpose       |
| ---------- | ------------------ | ----------- | ------------- |
| Read Tool  | GetEmployeeDetails | GET         | Retrieve data |
| Read Tool  | GetTaskList        | GET         | Retrieve data |
| Write Tool | CreateTask         | POST        | Create data   |
| Write Tool | UpdateTask         | PUT         | Update data   |
| Write Tool | DeleteTask         | DELETE      | Remove data   |

---
