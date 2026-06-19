# Evaluation Test Report

- **Generated:** 2026-06-19T09:03:47.841638+00:00
- **Dataset version:** 1.3
- **Mode:** mocked
- **Summary:** 22/22 passed (100.0%)

## Results by case

### Case 1 — present_query [PASS]

| Field | Value |
|-------|-------|
| **Input** | Who is present today? |
| **Expected intent** | `present_query` |
| **Actual intent** | `present_query` (✓) |
| **Expected tools** | `get_present_employees` |
| **Tools executed** | `get_present_employees` (✓) |
| **Expected execution** | `direct_tools` |
| **Actual route** | `direct_tools` (✓) |
| **Expected parameters** | `{"date": "2026-06-19"}` |
| **Actual parameters** | `{"date": "2026-06-19"}` (✓) |
| **Answer** | Here is the result for your query. present employee |

### Case 2 — absent_query [PASS]

| Field | Value |
|-------|-------|
| **Input** | Who is absent today? |
| **Expected intent** | `absent_query` |
| **Actual intent** | `absent_query` (✓) |
| **Expected tools** | `get_absent_employees` |
| **Tools executed** | `get_absent_employees` (✓) |
| **Expected execution** | `direct_tools` |
| **Actual route** | `direct_tools` (✓) |
| **Expected parameters** | `{"date": "2026-06-19"}` |
| **Actual parameters** | `{"date": "2026-06-19"}` (✓) |
| **Answer** | Here is the result for your query. absent |

### Case 3 — absent_query [PASS]

| Field | Value |
|-------|-------|
| **Input** | Who didn't come to office on 2026-06-15? |
| **Expected intent** | `absent_query` |
| **Actual intent** | `absent_query` (✓) |
| **Expected tools** | `get_absent_employees` |
| **Tools executed** | `get_absent_employees` (✓) |
| **Expected execution** | `direct_tools` |
| **Actual route** | `direct_tools` (✓) |
| **Expected parameters** | `{"date": "2026-06-15"}` |
| **Actual parameters** | `{"date": "2026-06-15"}` (✓) |
| **Answer** | Here is the result for your query. absent June 15 |

### Case 4 — summary_query [PASS]

| Field | Value |
|-------|-------|
| **Input** | Show attendance summary for today |
| **Expected intent** | `summary_query` |
| **Actual intent** | `summary_query` (✓) |
| **Expected tools** | `get_attendance_summary` |
| **Tools executed** | `get_attendance_summary` (✓) |
| **Expected execution** | `direct_tools` |
| **Actual route** | `direct_tools` (✓) |
| **Expected parameters** | `{"date": "2026-06-19"}` |
| **Actual parameters** | `{"date": "2026-06-19"}` (✓) |
| **Answer** | Here is the result for your query. present absent total |

### Case 5 — summary_query [PASS]

| Field | Value |
|-------|-------|
| **Input** | Give me an overview of attendance this Monday |
| **Expected intent** | `summary_query` |
| **Actual intent** | `summary_query` (✓) |
| **Expected tools** | `get_attendance_summary` |
| **Tools executed** | `get_attendance_summary` (✓) |
| **Expected execution** | `direct_tools` |
| **Actual route** | `direct_tools` (✓) |
| **Expected parameters** | `{"date": "2026-06-15"}` |
| **Actual parameters** | `{"date": "2026-06-15"}` (✓) |
| **Answer** | Here is the result for your query. summary |

### Case 6 — history_query [PASS]

| Field | Value |
|-------|-------|
| **Input** | Show my attendance history for this month |
| **Expected intent** | `history_query` |
| **Actual intent** | `history_query` (✓) |
| **Expected tools** | `get_attendance_history` |
| **Tools executed** | `get_attendance_history` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{"month": 6, "year": 2026}` |
| **Actual parameters** | `{"month": 6, "year": 2026}` (✓) |
| **Tool arguments** | `{"get_attendance_history": {"month": 6, "year": 2026}}` |
| **Answer** | Processed your request. attendance month |

### Case 7 — history_query [PASS]

| Field | Value |
|-------|-------|
| **Input** | Show attendance history for employee 42 for May 2026 |
| **Expected intent** | `history_query` |
| **Actual intent** | `history_query` (✓) |
| **Expected tools** | `get_attendance_history` |
| **Tools executed** | `get_attendance_history` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{"month": 5, "year": 2026, "employee_id": 42}` |
| **Actual parameters** | `{"month": 5, "year": 2026, "employee_id": 42}` (✓) |
| **Tool arguments** | `{"get_attendance_history": {"month": 5, "year": 2026, "employee_id": 42}}` |
| **Answer** | Processed your request. May 2026 |

### Case 8 — history_query [PASS]

| Field | Value |
|-------|-------|
| **Input** | Show attendance history for Greeshma this month |
| **Expected intent** | `history_query` |
| **Actual intent** | `history_query` (✓) |
| **Expected tools** | `get_attendance_history` |
| **Tools executed** | `get_attendance_history` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{"employee_name": "Greeshma", "month": 6, "year": 2026}` |
| **Actual parameters** | `{"employee_name": "Greeshma", "month": 6, "year": 2026}` (✓) |
| **Tool arguments** | `{"get_attendance_history": {"month": 6, "year": 2026, "employee_name": "Greeshma"}}` |
| **Answer** | Processed your request. Greeshma present absent |

### Case 9 — search_employee [PASS]

| Field | Value |
|-------|-------|
| **Input** | Find employee named Sarah |
| **Expected intent** | `search_employee` |
| **Actual intent** | `search_employee` (✓) |
| **Expected tools** | `search_employee` |
| **Tools executed** | `search_employee` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{"employee_name": "Sarah"}` |
| **Actual parameters** | `{"employee_name": "Sarah"}` (✓) |
| **Tool arguments** | `{"search_employee": {"query": "Sarah"}}` |
| **Answer** | Processed your request. Sarah |

### Case 10 — search_employee [PASS]

| Field | Value |
|-------|-------|
| **Input** | Search for employee with code EMP042 |
| **Expected intent** | `search_employee` |
| **Actual intent** | `search_employee` (✓) |
| **Expected tools** | `search_employee` |
| **Tools executed** | `search_employee` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{"employee_name": "EMP042"}` |
| **Actual parameters** | `{"employee_name": "EMP042"}` (✓) |
| **Tool arguments** | `{"search_employee": {"query": "EMP042"}}` |
| **Answer** | Processed your request. EMP042 |

### Case 11 — my_attendance [PASS]

| Field | Value |
|-------|-------|
| **Input** | What is my attendance today? |
| **Expected intent** | `my_attendance` |
| **Actual intent** | `my_attendance` (✓) |
| **Expected tools** | `get_my_attendance_today` |
| **Tools executed** | `get_my_attendance_today` (✓) |
| **Expected execution** | `direct_tools` |
| **Actual route** | `direct_tools` (✓) |
| **Expected parameters** | `{"date": "2026-06-19"}` |
| **Actual parameters** | `{"date": "2026-06-19"}` (✓) |
| **Answer** | Here is the result for your query. status |

### Case 12 — my_attendance [PASS]

| Field | Value |
|-------|-------|
| **Input** | Have I checked in today? |
| **Expected intent** | `my_attendance` |
| **Actual intent** | `my_attendance` (✓) |
| **Expected tools** | `get_my_attendance_today` |
| **Tools executed** | `get_my_attendance_today` (✓) |
| **Expected execution** | `direct_tools` |
| **Actual route** | `direct_tools` (✓) |
| **Expected parameters** | `{"date": "2026-06-19"}` |
| **Actual parameters** | `{"date": "2026-06-19"}` (✓) |
| **Answer** | Here is the result for your query. check |

### Case 13 — employee_detail [PASS]

| Field | Value |
|-------|-------|
| **Input** | Show attendance details for Greeshma today |
| **Expected intent** | `employee_detail` |
| **Actual intent** | `employee_detail` (✓) |
| **Expected tools** | `search_employee, get_employee_attendance_details` |
| **Tools executed** | `search_employee, get_employee_attendance_details` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{"employee_name": "Greeshma", "date": "2026-06-19"}` |
| **Actual parameters** | `{"employee_name": "Greeshma", "date": "2026-06-19"}` (✓) |
| **Tool arguments** | `{"search_employee": {"query": "Greeshma"}, "get_employee_attendance_details": {"date_str": "2026-06-19"}}` |
| **Answer** | Processed your request. Greeshma status |

### Case 14 — employee_detail [PASS]

| Field | Value |
|-------|-------|
| **Input** | What time did John check in today? |
| **Expected intent** | `employee_detail` |
| **Actual intent** | `employee_detail` (✓) |
| **Expected tools** | `search_employee, get_employee_attendance_details` |
| **Tools executed** | `search_employee, get_employee_attendance_details` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{"employee_name": "John", "date": "2026-06-19"}` |
| **Actual parameters** | `{"employee_name": "John", "date": "2026-06-19"}` (✓) |
| **Tool arguments** | `{"search_employee": {"query": "John"}, "get_employee_attendance_details": {"date_str": "2026-06-19"}}` |
| **Answer** | Processed your request. check |

### Case 15 — unclear [PASS]

| Field | Value |
|-------|-------|
| **Input** | attendance |
| **Expected intent** | `unclear` |
| **Actual intent** | `unclear` (✓) |
| **Expected tools** | `—` |
| **Tools executed** | `—` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{}` |
| **Actual parameters** | `{}` (✓) |
| **Answer** | Processed your request. clarify help ? |

### Case 16 — unclear [PASS]

| Field | Value |
|-------|-------|
| **Input** | show me the data |
| **Expected intent** | `unclear` |
| **Actual intent** | `unclear` (✓) |
| **Expected tools** | `—` |
| **Tools executed** | `—` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{}` |
| **Actual parameters** | `{}` (✓) |
| **Answer** | Processed your request. which what clarify |

### Case 17 — out_of_scope [PASS]

| Field | Value |
|-------|-------|
| **Input** | What is my salary this month? |
| **Expected intent** | `out_of_scope` |
| **Actual intent** | `out_of_scope` (✓) |
| **Expected tools** | `—` |
| **Tools executed** | `—` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{}` |
| **Actual parameters** | `{}` (✓) |
| **Answer** | Processed your request. attendance scope |

### Case 18 — out_of_scope [PASS]

| Field | Value |
|-------|-------|
| **Input** | Apply for leave next week |
| **Expected intent** | `out_of_scope` |
| **Actual intent** | `out_of_scope` (✓) |
| **Expected tools** | `—` |
| **Tools executed** | `—` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{}` |
| **Actual parameters** | `{}` (✓) |
| **Answer** | Processed your request. attendance scope |

### Case 19 — present_query [PASS]

| Field | Value |
|-------|-------|
| **Input** | How many people came to work yesterday? |
| **Expected intent** | `present_query` |
| **Actual intent** | `present_query` (✓) |
| **Expected tools** | `get_present_employees` |
| **Tools executed** | `get_present_employees` (✓) |
| **Expected execution** | `direct_tools` |
| **Actual route** | `direct_tools` (✓) |
| **Expected parameters** | `{"date": "2026-06-18"}` |
| **Actual parameters** | `{"date": "2026-06-18"}` (✓) |
| **Answer** | Here is the result for your query. present yesterday |

### Case 20 — history_query [PASS]

| Field | Value |
|-------|-------|
| **Input** | Show attendance for John Smith for last month |
| **Expected intent** | `history_query` |
| **Actual intent** | `history_query` (✓) |
| **Expected tools** | `get_attendance_history` |
| **Tools executed** | `get_attendance_history` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{"employee_name": "John Smith"}` |
| **Actual parameters** | `{"employee_name": "John Smith"}` (✓) |
| **Tool arguments** | `{"get_attendance_history": {"employee_name": "John Smith"}}` |
| **Answer** | Processed your request. John Smith |

### Case 21 — multi_step [PASS]

| Field | Value |
|-------|-------|
| **Input** | Show her history this month |
| **Expected intent** | `history_query` |
| **Actual intent** | `history_query` (✓) |
| **Expected tools** | `get_attendance_history` |
| **Tools executed** | `get_attendance_history` (✓) |
| **Expected execution** | `agent_react` |
| **Actual route** | `agent` (✓) |
| **Expected parameters** | `{"employee_name": "Greeshma", "month": 6}` |
| **Actual parameters** | `{"employee_name": "Greeshma", "month": 6}` (✓) |
| **Tool arguments** | `{"get_attendance_history": {"month": 6, "employee_name": "Greeshma"}}` |
| **Answer** | Processed your request. Greeshma |

### Case 22 — error_handling [PASS]

| Field | Value |
|-------|-------|
| **Input** | Who is present on 2025-01-01? |
| **Expected intent** | `present_query` |
| **Actual intent** | `present_query` (✓) |
| **Expected tools** | `get_present_employees` |
| **Tools executed** | `get_present_employees` (✓) |
| **Expected execution** | `direct_tools` |
| **Actual route** | `direct_tools` (✓) |
| **Expected parameters** | `{"date": "2025-01-01"}` |
| **Actual parameters** | `{"date": "2025-01-01"}` (✓) |
| **Answer** | Here is the result for your query. no holiday present error |
