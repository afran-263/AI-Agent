# HRMS Tool Schemas

## 1. get_employee

```json
{
  "name": "get_employee",
  "description": "Retrieve employee details by employee ID",
  "risk_level": "low",
  "approval_required": false,

  "input_schema": {
    "type": "object",
    "properties": {
      "employee_id": {
        "type": "string"
      }
    },
    "required": ["employee_id"]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "name": {"type": "string"},
      "email": {"type": "string"},
      "department": {"type": "string"},
      "designation": {"type": "string"}
    }
  }
}
```

---

## 2. search_employees

```json
{
  "name": "search_employees",
  "description": "Search employees using filters",
  "risk_level": "low",
  "approval_required": false,

  "input_schema": {
    "type": "object",
    "properties": {
      "department": {"type": "string"},
      "designation": {"type": "string"},
      "status": {"type": "string"}
    }
  },

  "output_schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "employee_id": {"type": "string"},
        "name": {"type": "string"},
        "department": {"type": "string"}
      }
    }
  }
}
```

---

## 3. get_attendance

```json
{
  "name": "get_attendance",
  "description": "Retrieve attendance records",
  "risk_level": "low",
  "approval_required": false,

  "input_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "start_date": {"type": "string"},
      "end_date": {"type": "string"}
    },
    "required": ["employee_id"]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "attendance_records": {
        "type": "array"
      }
    }
  }
}
```

---

## 4. get_leave_balance

```json
{
  "name": "get_leave_balance",
  "description": "Get employee leave balances",
  "risk_level": "low",
  "approval_required": false,

  "input_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"}
    },
    "required": ["employee_id"]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "annual_leave": {"type": "integer"},
      "sick_leave": {"type": "integer"},
      "casual_leave": {"type": "integer"}
    }
  }
}
```

---

## 5. get_payroll

```json
{
  "name": "get_payroll",
  "description": "Retrieve payroll information",
  "risk_level": "medium",
  "approval_required": false,

  "input_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "pay_period": {"type": "string"}
    },
    "required": ["employee_id"]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "basic_salary": {"type": "number"},
      "allowances": {"type": "number"},
      "deductions": {"type": "number"},
      "net_salary": {"type": "number"}
    }
  }
}
```

---

## 6. create_employee

```json
{
  "name": "create_employee",
  "description": "Create a new employee record",
  "risk_level": "medium",
  "approval_required": false,

  "input_schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "email": {"type": "string"},
      "phone": {"type": "string"},
      "department": {"type": "string"},
      "designation": {"type": "string"}
    },
    "required": [
      "name",
      "email",
      "department",
      "designation"
    ]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "status": {"type": "string"}
    }
  }
}
```

---

## 7. update_employee

```json
{
  "name": "update_employee",
  "description": "Update employee details",
  "risk_level": "medium",
  "approval_required": false,

  "input_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "name": {"type": "string"},
      "email": {"type": "string"},
      "phone": {"type": "string"}
    },
    "required": ["employee_id"]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "status": {"type": "string"}
    }
  }
}
```

---

## 8. apply_leave

```json
{
  "name": "apply_leave",
  "description": "Submit a leave request",
  "risk_level": "medium",
  "approval_required": false,

  "input_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "leave_type": {"type": "string"},
      "start_date": {"type": "string"},
      "end_date": {"type": "string"},
      "reason": {"type": "string"}
    },
    "required": [
      "employee_id",
      "leave_type",
      "start_date",
      "end_date"
    ]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "leave_id": {"type": "string"},
      "status": {"type": "string"}
    }
  }
}
```

---

## 9. approve_leave

```json
{
  "name": "approve_leave",
  "description": "Approve a leave request",
  "risk_level": "high",
  "approval_required": true,

  "input_schema": {
    "type": "object",
    "properties": {
      "leave_id": {"type": "string"},
      "approver_id": {"type": "string"}
    },
    "required": [
      "leave_id",
      "approver_id"
    ]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "leave_id": {"type": "string"},
      "status": {"type": "string"}
    }
  }
}
```

---

## 10. reject_leave

```json
{
  "name": "reject_leave",
  "description": "Reject a leave request",
  "risk_level": "high",
  "approval_required": true,

  "input_schema": {
    "type": "object",
    "properties": {
      "leave_id": {"type": "string"},
      "approver_id": {"type": "string"},
      "reason": {"type": "string"}
    },
    "required": [
      "leave_id",
      "approver_id"
    ]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "leave_id": {"type": "string"},
      "status": {"type": "string"}
    }
  }
}
```

---

## 11. update_salary

```json
{
  "name": "update_salary",
  "description": "Update employee salary",
  "risk_level": "high",
  "approval_required": true,

  "input_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "new_salary": {"type": "number"},
      "effective_date": {"type": "string"}
    },
    "required": [
      "employee_id",
      "new_salary"
    ]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "old_salary": {"type": "number"},
      "new_salary": {"type": "number"},
      "updated_at": {"type": "string"}
    }
  }
}
```

---

## 12. process_payroll

```json
{
  "name": "process_payroll",
  "description": "Process payroll for a pay period",
  "risk_level": "critical",
  "approval_required": true,

  "input_schema": {
    "type": "object",
    "properties": {
      "pay_period": {
        "type": "string"
      }
    },
    "required": ["pay_period"]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "batch_id": {"type": "string"},
      "processed_employees": {"type": "integer"},
      "status": {"type": "string"}
    }
  }
}
```

---

## 13. deactivate_employee

```json
{
  "name": "deactivate_employee",
  "description": "Deactivate employee account",
  "risk_level": "high",
  "approval_required": true,

  "input_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "reason": {"type": "string"}
    },
    "required": ["employee_id"]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "status": {"type": "string"}
    }
  }
}
```

---

## 14. delete_employee

```json
{
  "name": "delete_employee",
  "description": "Permanently delete employee record",
  "risk_level": "critical",
  "approval_required": true,

  "input_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "deletion_reason": {"type": "string"}
    },
    "required": ["employee_id"]
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "employee_id": {"type": "string"},
      "status": {"type": "string"}
    }
  }
}
```


# HRMS Tool Input and Output Schemas

## 1. get_employee

### Input Schema

```json
{
  "employee_id": "string"
}
```

### Output Schema

```json
{
  "employee_id": "string",
  "name": "string",
  "email": "string",
  "department": "string",
  "designation": "string",
  "status": "string"
}
```

---

## 2. search_employees

### Input Schema

```json
{
  "department": "string",
  "designation": "string",
  "status": "string"
}
```

### Output Schema

```json
{
  "employees": [
    {
      "employee_id": "string",
      "name": "string",
      "department": "string",
      "designation": "string"
    }
  ]
}
```

---

## 3. get_attendance

### Input Schema

```json
{
  "employee_id": "string",
  "start_date": "string",
  "end_date": "string"
}
```

### Output Schema

```json
{
  "employee_id": "string",
  "attendance_records": [
    {
      "date": "string",
      "check_in": "string",
      "check_out": "string",
      "status": "Present | Absent | Leave"
    }
  ]
}
```

---

## 4. get_leave_balance

### Input Schema

```json
{
  "employee_id": "string"
}
```

### Output Schema

```json
{
  "employee_id": "string",
  "annual_leave": "integer",
  "sick_leave": "integer",
  "casual_leave": "integer"
}
```

---

## 5. get_payroll

### Input Schema

```json
{
  "employee_id": "string",
  "pay_period": "string"
}
```

### Output Schema

```json
{
  "employee_id": "string",
  "basic_salary": "number",
  "allowances": "number",
  "deductions": "number",
  "net_salary": "number"
}
```

---

## 6. create_employee

### Input Schema

```json
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "department": "string",
  "designation": "string",
  "joining_date": "string"
}
```

### Output Schema

```json
{
  "employee_id": "string",
  "status": "created"
}
```

---

## 7. update_employee

### Input Schema

```json
{
  "employee_id": "string",
  "name": "string",
  "email": "string",
  "phone": "string",
  "department": "string",
  "designation": "string"
}
```

### Output Schema

```json
{
  "employee_id": "string",
  "status": "updated"
}
```

---

## 8. apply_leave

### Input Schema

```json
{
  "employee_id": "string",
  "leave_type": "string",
  "start_date": "string",
  "end_date": "string",
  "reason": "string"
}
```

### Output Schema

```json
{
  "leave_id": "string",
  "status": "pending"
}
```

---

## 9. approve_leave

### Input Schema

```json
{
  "leave_id": "string",
  "approver_id": "string"
}
```

### Output Schema

```json
{
  "leave_id": "string",
  "status": "approved",
  "approved_by": "string"
}
```

---

## 10. reject_leave

### Input Schema

```json
{
  "leave_id": "string",
  "approver_id": "string",
  "reason": "string"
}
```

### Output Schema

```json
{
  "leave_id": "string",
  "status": "rejected"
}
```

---

## 11. update_salary

### Input Schema

```json
{
  "employee_id": "string",
  "new_salary": "number",
  "effective_date": "string"
}
```

### Output Schema

```json
{
  "employee_id": "string",
  "old_salary": "number",
  "new_salary": "number",
  "updated_at": "string"
}
```

---

## 12. process_payroll

### Input Schema

```json
{
  "pay_period": "string"
}
```

### Output Schema

```json
{
  "batch_id": "string",
  "processed_employees": "integer",
  "status": "completed"
}
```

---

## 13. deactivate_employee

### Input Schema

```json
{
  "employee_id": "string",
  "reason": "string"
}
```

### Output Schema

```json
{
  "employee_id": "string",
  "status": "deactivated"
}
```

---

## 14. delete_employee

### Input Schema

```json
{
  "employee_id": "string",
  "deletion_reason": "string"
}
```

### Output Schema

```json
{
  "employee_id": "string",
  "status": "deleted"
}
```

---
