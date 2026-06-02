# API Tool Map – HRMS AI Agent

## Overview

This document defines the tools available to the HRMS AI Agent and the backend APIs used by each tool.

The AI agent never calls APIs directly. Instead, it selects a tool based on the user's request. The tool then invokes the corresponding API and returns the result to the agent.

---

# Employee Management

## Tool: create_employee

**Purpose**

Create a new employee profile.

**Connected API**

```http
 POST /api/employees
 ```

**Inputs**

```json
 {
 "name": "John Doe",
 "email": "john@example.com",
 "department": "Engineering"
 }
 ```

**Output**

```json
 {
 "employeeId": "EMP1023",
 "status": "Created"
 }
 ```

---

## Tool: get_employee

**Purpose**

Retrieve employee details.

**Connected API**

```http
 GET /api/employees/{employeeId}
 ```

---

## Tool: update_employee

**Purpose**

Update employee information.

**Connected API**

```http
 PUT /api/employees/{employeeId}
 ```

---

# Credential Management

## Tool: generate_credentials

**Purpose**

Generate employee username and temporary password.

**Connected API**

```http
 POST /api/auth/generate-credentials
 ```

---

## Tool: send_credentials

**Purpose**

Email employee credentials.

**Connected API**

```http
 POST /api/email/send-credentials
 ```

---

# Document Management

## Tool: upload_document

**Purpose**

Upload onboarding documents.

**Connected API**

```http
 POST /api/documents/upload
 ```

---

## Tool: verify_document

**Purpose**

Verify uploaded employee documents.

**Connected API**

```http
 POST /api/documents/verify
 ```

---

## Tool: get_document_status

**Purpose**

Retrieve document verification status.

**Connected API**

```http
 GET /api/documents/status/{employeeId}
 ```

---

# Onboarding

## Tool: start_onboarding

**Purpose**

Start onboarding workflow.

**Connected API**

```http
 POST /api/onboarding/start
 ```

---

## Tool: get_onboarding_status

**Purpose**

Retrieve onboarding progress.

**Connected API**

```http
 GET /api/onboarding/status/{employeeId}
 ```

---

## Tool: complete_onboarding

**Purpose**

Mark onboarding as completed.

**Connected API**

```http
 POST /api/onboarding/complete
 ```

---

# Task Management

## Tool: create_task

**Purpose**

Create onboarding tasks.

**Connected API**

```http
 POST /api/tasks
 ```

---

## Tool: assign_task

**Purpose**

Assign tasks to employees, managers, HR, or IT teams.

**Connected API**

```http
 POST /api/tasks/assign
 ```

---

## Tool: get_tasks

**Purpose**

Retrieve assigned tasks.

**Connected API**

```http
 GET /api/tasks
 ```

---

## Tool: update_task_status

**Purpose**

Update task progress.

**Connected API**

```http
 PATCH /api/tasks/{taskId}
 ```

---

# Notifications

## Tool: send_email

**Purpose**

Send email notifications.

**Connected API**

```http
 POST /api/notifications/email
 ```

---

## Tool: send_notification

**Purpose**

Send in-app notifications.

**Connected API**

```http
 POST /api/notifications/in-app
 ```

---

## Tool: send_reminder

**Purpose**

Send task reminders.

**Connected API**

```http
 POST /api/reminders/send
 ```

---

# Manager Operations

## Tool: get_team_onboarding_status

**Purpose**

View onboarding progress of team members.

**Connected API**

```http
 GET /api/managers/team-status
 ```

---

## Tool: approve_onboarding

**Purpose**

Approve employee onboarding completion.

**Connected API**

```http
 POST /api/managers/approve-onboarding
 ```

---

## Tool: assign_project

**Purpose**

Assign employees to projects.

**Connected API**

```http
 POST /api/projects/assign
 ```

---

# IT Operations

## Tool: create_company_email

**Purpose**

Create company email account.

**Connected API**

```http
 POST /api/it/create-email
 ```

---

## Tool: setup_system_access

**Purpose**

Provide access to company systems.

**Connected API**

```http
 POST /api/it/system-access
 ```

---

## Tool: complete_it_setup

**Purpose**

Mark IT setup as completed.

**Connected API**

```http
 POST /api/it/complete-setup
 ```

---

# ATS & Skill Matching

## Tool: extract_skills

**Purpose**

Extract skills from uploaded resumes.

**Connected API**

```http
 POST /api/ats/extract-skills
 ```

---

## Tool: rank_candidates

**Purpose**

Rank candidates based on job requirements.

**Connected API**

```http
 POST /api/ats/rank
 ```

---

## Tool: recommend_projects

**Purpose**

Recommend projects based on employee skills.

**Connected API**

```http
 POST /api/projects/recommend
 ```

---

# Knowledge Base (RAG)

## Tool: search_policies

**Purpose**

Search HR policies and company documents.

**Connected API**

```http
 POST /api/rag/search
 ```

---

## Tool: get_policy_answer

**Purpose**

Answer policy-related questions using RAG.

**Connected API**

```http
 POST /api/rag/answer
 ```

---

# Monitoring & Reporting

## Tool: get_activity_logs

**Purpose**

Retrieve activity logs.

**Connected API**

```http
 GET /api/logs
 ```

---

## Tool: generate_summary

**Purpose**

Generate onboarding summary reports.

**Connected API**

```http
 GET /api/reports/onboarding-summary
 ```

---

# Agent Execution Flow

```text
 User Request
 ↓
 Intent Detection
 ↓
 Tool Selection
 ↓
 API Execution
 ↓
 Result Validation
 ↓
 Response Generation
 ```

Example:

User: Create a new employee and start onboarding.

Selected Tools:

* create_employee
 * generate_credentials
 * send_credentials
 * start_onboarding
 * assign_task
 * send_notification

Result:
 Employee successfully onboarded.