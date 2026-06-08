namespace HrmsAgentApi.Models;

public class Employee
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
    public string Department { get; set; } = "";
    public string Designation { get; set; } = "";
    public string Phone { get; set; } = "";
    public string JoiningDate { get; set; } = "";
    public string Status { get; set; } = "";
    public string ReportingManager { get; set; } = "";
    public decimal Salary { get; set; }
    public string Location { get; set; } = "";
}

public class EmployeeSummary
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Department { get; set; } = "";
    public string Designation { get; set; } = "";
    public string Status { get; set; } = "";
}

public class TaskItem
{
    public int TaskId { get; set; }
    public int EmployeeId { get; set; }
    public string EmployeeName { get; set; } = "";
    public string Title { get; set; } = "";
    public string Description { get; set; } = "";
    public string Priority { get; set; } = "";
    public string Status { get; set; } = "";
    public string DueDate { get; set; } = "";
    public string AssignedBy { get; set; } = "";
    public string Category { get; set; } = "";
}

public class TaskCreateRequest
{
    public int EmployeeId { get; set; }
    public string Title { get; set; } = "";
    public string Description { get; set; } = "";
    public string Priority { get; set; } = "";
    public string? Status { get; set; }
    public string DueDate { get; set; } = "";
    public string AssignedBy { get; set; } = "";
    public string Category { get; set; } = "";
}

public class TaskAssignRequest
{
    public int EmployeeId { get; set; }
    public string? AssignedBy { get; set; }
}

public class TaskStatusUpdateRequest
{
    public string Status { get; set; } = "";
}

public class AttendanceRecord
{
    public int AttendanceId { get; set; }
    public int EmployeeId { get; set; }
    public string EmployeeName { get; set; } = "";
    public string Date { get; set; } = "";
    public string Status { get; set; } = "";
    public string CheckInTime { get; set; } = "";
    public string CheckOutTime { get; set; } = "";
    public string Notes { get; set; } = "";
}

public class AttendanceCreateRequest
{
    public int EmployeeId { get; set; }
    public string Date { get; set; } = "";
    public string Status { get; set; } = "";
    public string? CheckInTime { get; set; }
    public string? CheckOutTime { get; set; }
    public string? Notes { get; set; }
}

// API response wrappers
public class ApiResponse<T>
{
    public bool Success { get; set; }
    public string Message { get; set; } = "";
    public T? Data { get; set; }
    public int TotalCount { get; set; }
}
