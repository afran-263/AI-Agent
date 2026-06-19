# API Mapping Document — Voyon Attendance Agent

## Overview

All data is fetched from the existing Voyon Folks HRMS REST APIs.
No direct database access occurs. The base URL is configured via `HRMS_BASE_URL`
in `.env`.

Implementation: `src/api/hrms_client.py` (HTTP layer) and `src/agent/tools.py` (tool layer).

---

## Authentication

| Step | Method | Endpoint | Notes |
|------|--------|----------|-------|
| Login | POST | `/m/api/Login/LoginUser` | Body: `{UserName, Password, DeviceId, DeviceType}`. Returns `{token/Token, refreshToken, employeeId, userId}` |
| Token Refresh | POST | `/m/api/Login/RefreshToken` | Body: `{RefreshToken}`. Returns new token pair |

All subsequent calls pass `Authorization: Bearer <token>` header.

---

## Tool → API Mapping

### 1. `get_present_employees(date_str, reporting_type)`

| Field | Value |
|-------|-------|
| HTTP Method | GET |
| Endpoint | `/m/api/Attendance/team-attendance` |
| Parameters | `employeeId={session_emp_id}&date={YYYY-MM-DD}&reportingType={0\|1\|2}` |
| Auth | JWT Bearer |
| Post-processing | Filter records where `_emp_status()` == `"Present"` |
| Execution path | Direct (`direct_tools` node) or LLM ReAct loop |

**Sample request:**
```
GET /m/api/Attendance/team-attendance?employeeId=130&date=2026-06-19&reportingType=0
Authorization: Bearer <jwt>
```

---

### 2. `get_absent_employees(date_str, reporting_type)`

| Field | Value |
|-------|-------|
| HTTP Method | GET |
| Endpoint | `/m/api/Attendance/team-attendance` |
| Same parameters as above | ✓ |
| Post-processing | Filter records where status NOT IN (Present, Holiday, WeeklyOff) |
| Execution path | Direct or LLM ReAct loop |

---

### 3. `get_attendance_summary(date_str, reporting_type)`

| Field | Value |
|-------|-------|
| HTTP Method | GET |
| Endpoint | `/m/api/Attendance/team-attendance` |
| Same parameters as above | ✓ |
| Post-processing | `_extract_summary_counts()` from `TeamAttendanceSummary` when present; otherwise count by `_emp_status()` |
| Execution path | **Direct** (`direct_tools` node) for `summary_query` intent |

**Output shape:**
```json
{
  "date": "2026-06-19",
  "total_employees": 85,
  "summary_by_status": {"Present": 72, "Absent": 5, "Leave": 6, "WeeklyOff/Holiday": 2}
}
```

---

### 4. `get_attendance_history(month, year, employee_id, employee_name)`

| Field | Value |
|-------|-------|
| Strategy 1 (primary) | `GET /m/api/Attendance/MonthlyAttendance` |
| Strategy 2 (fallback) | `GET /m/api/Attendance/AttendanceBasedOnDate` per day in month |
| Name resolution | `GET /m/api/Employee/search-employees/{name}/{page}` when `employee_name` given |
| Parameters | `employeeId`, `month` (1–12), `year` |
| Auth | JWT Bearer |
| Default employee | Session user's `employee_id` when neither `employee_id` nor `employee_name` provided |

**Strategy 1 — MonthlyAttendance:**
```
GET /m/api/Attendance/MonthlyAttendance?employeeId=1073&month=6&year=2026
Authorization: Bearer <jwt>
```

**Strategy 2 — Day-by-day fallback** (triggered when MonthlyAttendance returns HTTP 500):
```
GET /m/api/Attendance/AttendanceBasedOnDate?employeeId=1073&date=2026-06-01
GET /m/api/Attendance/AttendanceBasedOnDate?employeeId=1073&date=2026-06-02
... (one call per day up to today for current month)
```

Fallback response includes a computed `summary` block:
```json
{
  "employee_id": 1073,
  "employee_name": "Greeshma",
  "month": 6,
  "year": 2026,
  "summary": {
    "total_days": 19,
    "present": 5,
    "absent": 10,
    "leave": 0,
    "holiday": 2,
    "weekoff": 2
  },
  "attendance": [{"date": "2026-06-01", "details": {...}}, ...]
}
```

**Employee ID extraction:** `_extract_numeric_id()` reads `EmployeeId` / `employeeId` first.
String values in `Id` / `id` (employee codes like `"dcfv"`) are only used if they parse as positive integers.

---

### 5. `search_employee(query, date_str)`

| Field | Value |
|-------|-------|
| Strategy 1 (primary) | `GET /m/api/Employee/search-employees/{searchValue}/{currentPage}` |
| Strategy 2 (fallback) | `GET /m/api/Attendance/team-attendance` + client-side filter |
| Auth | JWT Bearer |
| Post-processing | `_employee_matches()` on name, code, or numeric ID |

**Sample request (primary):**
```
GET /m/api/Employee/search-employees/greeshma/1
Authorization: Bearer <jwt>
```

---

### 6. `get_my_attendance_today()`

| Field | Value |
|-------|-------|
| HTTP Method | GET |
| Endpoint | `/m/api/Attendance/AttendanceBasedOnDate` |
| Parameters | `employeeId={session_emp_id}&date={today}` |
| Auth | JWT Bearer |
| Execution path | **Direct** (`direct_tools` node) for `my_attendance` intent |

---

### 7. `get_employee_attendance_details(employee_id, date_str)`

| Field | Value |
|-------|-------|
| Strategy 1 (primary) | `GET /m/api/Attendance/AttendanceBasedOnDate` |
| Strategy 2 (fallback) | `GET /m/api/Attendance/team-attendance` — find employee in team list |
| Profile lookup | `GET /m/api/Employee/GetEmployeeDetails?employeeId={id}` |
| Parameters | `employeeId` (required), `date` (YYYY-MM-DD, defaults to today) |
| Auth | JWT Bearer |
| Typical flow | `search_employee` → resolve ID → `get_employee_attendance_details` |

**Sample request:**
```
GET /m/api/Attendance/AttendanceBasedOnDate?employeeId=1073&date=2026-06-19
Authorization: Bearer <jwt>
```

---

## Additional APIs Available in HrmsClient

## Additional APIs Available in HrmsClient

| Purpose | Method | Endpoint |
|---------|--------|----------|
| User status info | GET | `/m/api/Employee/user-status-info` |
| Employee profile | GET | `/m/api/Employee/GetEmployeeDetails?employeeId={id}` |
| All active employees | GET | `/m/api/Employee/AllActive` |
| Attendance summary list (reports) | POST | `/AttendanceApi/attendance-summary-list` (form) |

---

## Response Handling

All API responses are serialised to JSON strings via `_safe_json()` and passed to the LLM tool context.
The LLM interprets the data and generates a human-readable response.

If the API returns an error (4xx/5xx), the tool returns:
```json
{"error": "HRMS API returned HTTP 500 for /path. Details: ..."}
```
…and the LLM generates an apologetic response to the user.

For `get_attendance_history`, HTTP 500 on `MonthlyAttendance` triggers automatic
day-by-day fallback instead of returning an error to the user.

---

## Status Code Handling

| HTTP Status | Action |
|-------------|--------|
| 200 | Success — return parsed JSON |
| 401 | Raise `HrmsApiError` — session expired, redirect to login |
| 403 | Raise `HrmsApiError` — insufficient permissions |
| 404 | Raise `HrmsApiError` — resource not found |
| 500+ | Raise `HrmsApiError` — HRMS server error (history tool may fallback) |
| Timeout | `httpx` timeout after 30s → generic error response |
