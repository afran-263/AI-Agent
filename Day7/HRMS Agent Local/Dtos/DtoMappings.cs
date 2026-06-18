using HrmsAgentApi.Dtos;

namespace HrmsAgentApi.Models;

public static class DtoMappings
{
    public static EmployeeSummaryDto ToDto(this EmployeeSummary summary) => new()
    {
        Id = summary.Id,
        Name = summary.Name,
        Department = summary.Department,
        Designation = summary.Designation,
    };

    public static EmployeeDto ToDto(this Employee employee) => new()
    {
        Id = employee.Id,
        Name = employee.Name,
        Email = employee.Email,
        Department = employee.Department,
        Designation = employee.Designation,
        Phone = employee.Phone,
        JoiningDate = employee.JoiningDate,
        Status = employee.Status,
        ReportingManager = employee.ReportingManager,
        Salary = employee.Salary,
        Location = employee.Location
    };

    public static TaskItemDto ToDto(this TaskItem task) => new()
    {
        TaskId = task.TaskId,
        EmployeeId = task.EmployeeId,
        EmployeeName = task.EmployeeName,
        Title = task.Title,
        Description = task.Description,
        Priority = task.Priority,
        Status = task.Status,
        DueDate = task.DueDate,
        AssignedBy = task.AssignedBy,
        Category = task.Category
    };

    public static AttendanceRecordDto ToDto(this AttendanceRecord attendance) => new()
    {
        AttendanceId = attendance.AttendanceId,
        EmployeeId = attendance.EmployeeId,
        EmployeeName = attendance.EmployeeName,
        Date = attendance.Date,
        Status = attendance.Status,
        CheckInTime = attendance.CheckInTime,
        CheckOutTime = attendance.CheckOutTime,
        Notes = attendance.Notes
    };

  
}
