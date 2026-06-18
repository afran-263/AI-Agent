# HRMS Agent API

A RESTful ASP.NET Core API for managing employees, attendance, and tasks. This API is designed to be consumed by applications, AI agents, and HRMS integrations.

## Features

### Employee Management

* Get all employees
* Filter employees by department, status, and salary
* Retrieve employee details by ID

### Attendance Management

* View attendance records
* Filter attendance by employee, attendance ID, date, and status
* Mark employee attendance

### Task Management

* View all tasks
* Filter tasks by employee, status, and priority
* Create tasks
* Assign and reassign tasks to employees
* Update task status

### Local Data Storage

* Stores employee, attendance, and task data locally within the application
* Retrieves data directly from local system storage
* No external database dependency required
* Suitable for development, testing, demos, and AI agent integrations

## Available Endpoints

### Employees

* `GET /api/hrms/employees`
* `GET /api/hrms/employees/{id}`

### Attendance

* `GET /api/hrms/attendance`
* `POST /api/hrms/attendance`

### Tasks

* `GET /api/hrms/tasks`
* `POST /api/hrms/tasks`
* `PUT /api/hrms/tasks/{taskId}/assign`
* `PUT /api/hrms/tasks/{taskId}/status`
