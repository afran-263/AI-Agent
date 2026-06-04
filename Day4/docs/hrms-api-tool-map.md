# HRMS API Tool Map

| Tool | API Endpoint | Type | Risk Level | Approval Required |
|--------|-------------|--------|------------|-------------------|
| get_employee | GET /employees/{id} | Read | Low | No |
| search_employees | GET /employees | Read | Low | No |
| get_attendance | GET /attendance/{employeeId} | Read | Low | No |
| get_leave_balance | GET /leave-balance/{employeeId} | Read | Low | No |
| get_payroll | GET /payroll/{employeeId} | Read | Medium | No |
| create_employee | POST /employees | Write | Medium | No |
| update_employee | PUT /employees/{id} | Write | Medium | No |
| apply_leave | POST /leave | Write | Medium | No |
| approve_leave | POST /leave/{id}/approve | Write | High | Yes |
| reject_leave | POST /leave/{id}/reject | Write | High | Yes |
| update_salary | PUT /salary/{employeeId} | Write | High | Yes |
| process_payroll | POST /payroll/process | Write | Critical | Yes |
| deactivate_employee | POST /employees/{id}/deactivate | Write | High | Yes |
| delete_employee | DELETE /employees/{id} | Write | Critical | Yes |
