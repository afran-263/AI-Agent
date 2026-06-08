using HrmsAgentApi.Models;
using HrmsAgentApi.Services;
using Microsoft.AspNetCore.Mvc;

namespace HrmsAgentApi.Controllers;

[ApiController]
[Route("api/hrms")]
[Produces("application/json")]
public class HrmsController : ControllerBase
{
    private readonly HrmsDataService _dataService;

    public HrmsController(HrmsDataService dataService)
    {
        _dataService = dataService;
    }

    // ─────────────────────────────────────────────────────────────────
    //  TOOL 1 — GetEmployeeList
    // ─────────────────────────────────────────────────────────────────

    [HttpGet("employees")]
    [ProducesResponseType(typeof(ApiResponse<List<EmployeeSummary>>), 200)]
    public IActionResult GetEmployeeList(
        [FromQuery] string? department = null,
        [FromQuery] string? status = null)
    {
        var employees = _dataService.GetAllEmployees(department, status);

        return Ok(new ApiResponse<List<EmployeeSummary>>
        {
            Success = true,
            Message = employees.Count > 0
                ? $"Found {employees.Count} employee(s)."
                : "No employees matched the filter criteria.",
            Data = employees,
            TotalCount = employees.Count
        });
    }

    // ─────────────────────────────────────────────────────────────────
    //  TOOL 2 — GetEmployeeDetails
    // ─────────────────────────────────────────────────────────────────

    [HttpGet("employees/{id:int}")]
    [ProducesResponseType(typeof(ApiResponse<Employee>), 200)]
    [ProducesResponseType(typeof(ApiResponse<Employee>), 404)]
    public IActionResult GetEmployeeDetails(int id)
    {
        var employee = _dataService.GetEmployeeById(id);

        if (employee == null)
        {
            return NotFound(new ApiResponse<Employee>
            {
                Success = false,
                Message = $"No employee found with ID {id}. Please check the ID and try again.",
                Data = null,
                TotalCount = 0
            });
        }

        return Ok(new ApiResponse<Employee>
        {
            Success = true,
            Message = $"Employee details retrieved successfully for ID {id}.",
            Data = employee,
            TotalCount = 1
        });
    }

    // ─────────────────────────────────────────────────────────────────
    //  TOOL 3 — GetTaskList
    // ─────────────────────────────────────────────────────────────────

    [HttpGet("tasks")]
    [ProducesResponseType(typeof(ApiResponse<List<TaskItem>>), 200)]
    public IActionResult GetTaskList(
        [FromQuery] int? employeeId = null,
        [FromQuery] string? status = null,
        [FromQuery] string? priority = null)
    {
        List<TaskItem> tasks;

        if (employeeId.HasValue)
        {
            // Validate employee exists first
            var employee = _dataService.GetEmployeeById(employeeId.Value);
            if (employee == null)
            {
                return NotFound(new ApiResponse<List<TaskItem>>
                {
                    Success = false,
                    Message = $"No employee found with ID {employeeId}.",
                    Data = new List<TaskItem>(),
                    TotalCount = 0
                });
            }

            tasks = _dataService.GetTasksByEmployeeId(employeeId.Value);
            var message = tasks.Count > 0
                ? $"Found {tasks.Count} task(s) for {employee.Name}."
                : $"No tasks assigned to {employee.Name} yet.";

            return Ok(new ApiResponse<List<TaskItem>>
            {
                Success = true,
                Message = message,
                Data = tasks,
                TotalCount = tasks.Count
            });
        }

        // All tasks with optional filters
        tasks = _dataService.GetAllTasks(status, priority);
        return Ok(new ApiResponse<List<TaskItem>>
        {
            Success = true,
            Message = $"Retrieved {tasks.Count} task(s).",
            Data = tasks,
            TotalCount = tasks.Count
        });
    }

    // ─────────────────────────────────────────────────────────────────
    //  TOOL 4 — CreateTask
    // ─────────────────────────────────────────────────────────────────

    [HttpPost("tasks")]
    [ProducesResponseType(typeof(ApiResponse<TaskItem>), 201)]
    [ProducesResponseType(typeof(ApiResponse<TaskItem>), 400)]
    [ProducesResponseType(typeof(ApiResponse<TaskItem>), 404)]
    public IActionResult CreateTask([FromBody] TaskCreateRequest request)
    {
        if (request == null || request.EmployeeId <= 0 || string.IsNullOrWhiteSpace(request.Title))
        {
            return BadRequest(new ApiResponse<TaskItem>
            {
                Success = false,
                Message = "Invalid task request. EmployeeId and Title are required.",
                Data = null,
                TotalCount = 0
            });
        }

        var employee = _dataService.GetEmployeeById(request.EmployeeId);
        if (employee == null)
        {
            return NotFound(new ApiResponse<TaskItem>
            {
                Success = false,
                Message = $"No employee found with ID {request.EmployeeId}.",
                Data = null,
                TotalCount = 0
            });
        }

        var task = new TaskItem
        {
            EmployeeId = employee.Id,
            EmployeeName = employee.Name,
            Title = request.Title.Trim(),
            Description = request.Description?.Trim() ?? string.Empty,
            Priority = request.Priority?.Trim() ?? string.Empty,
            Status = string.IsNullOrWhiteSpace(request.Status) ? "Pending" : request.Status.Trim(),
            DueDate = request.DueDate?.Trim() ?? string.Empty,
            AssignedBy = request.AssignedBy?.Trim() ?? string.Empty,
            Category = request.Category?.Trim() ?? string.Empty
        };

        var createdTask = _dataService.AddTask(task);

        return CreatedAtAction(nameof(GetTaskList), new { employeeId = createdTask.EmployeeId }, new ApiResponse<TaskItem>
        {
            Success = true,
            Message = $"Task '{createdTask.Title}' created and assigned to {createdTask.EmployeeName}.",
            Data = createdTask,
            TotalCount = 1
        });
    }

    // ─────────────────────────────────────────────────────────────────
    //  TOOL 5 — AssignTask
    // ─────────────────────────────────────────────────────────────────

    [HttpPut("tasks/{taskId:int}/assign")]
    [ProducesResponseType(typeof(ApiResponse<TaskItem>), 200)]
    [ProducesResponseType(typeof(ApiResponse<TaskItem>), 400)]
    [ProducesResponseType(typeof(ApiResponse<TaskItem>), 404)]
    public IActionResult AssignTask(int taskId, [FromBody] TaskAssignRequest request)
    {
        if (request == null || request.EmployeeId <= 0)
        {
            return BadRequest(new ApiResponse<TaskItem>
            {
                Success = false,
                Message = "Invalid assign request. EmployeeId is required.",
                Data = null,
                TotalCount = 0
            });
        }

        var employee = _dataService.GetEmployeeById(request.EmployeeId);
        if (employee == null)
        {
            return NotFound(new ApiResponse<TaskItem>
            {
                Success = false,
                Message = $"No employee found with ID {request.EmployeeId}.",
                Data = null,
                TotalCount = 0
            });
        }

        var updatedTask = _dataService.AssignTask(taskId, request.EmployeeId);
        if (updatedTask == null)
        {
            return NotFound(new ApiResponse<TaskItem>
            {
                Success = false,
                Message = $"No task found with ID {taskId}.",
                Data = null,
                TotalCount = 0
            });
        }

        return Ok(new ApiResponse<TaskItem>
        {
            Success = true,
            Message = $"Task {taskId} reassigned to {updatedTask.EmployeeName}.",
            Data = updatedTask,
            TotalCount = 1
        });
    }

    // ─────────────────────────────────────────────────────────────────
    //  TOOL 6 — UpdateTaskStatus
    // ─────────────────────────────────────────────────────────────────

    [HttpPut("tasks/{taskId:int}/status")]
    [ProducesResponseType(typeof(ApiResponse<TaskItem>), 200)]
    [ProducesResponseType(typeof(ApiResponse<TaskItem>), 400)]
    [ProducesResponseType(typeof(ApiResponse<TaskItem>), 404)]
    public IActionResult UpdateTaskStatus(int taskId, [FromBody] TaskStatusUpdateRequest request)
    {
        if (request == null || string.IsNullOrWhiteSpace(request.Status))
        {
            return BadRequest(new ApiResponse<TaskItem>
            {
                Success = false,
                Message = "Invalid status update request. Status is required.",
                Data = null,
                TotalCount = 0
            });
        }

        var updatedTask = _dataService.UpdateTaskStatus(taskId, request.Status);
        if (updatedTask == null)
        {
            return NotFound(new ApiResponse<TaskItem>
            {
                Success = false,
                Message = $"No task found with ID {taskId}.",
                Data = null,
                TotalCount = 0
            });
        }

        return Ok(new ApiResponse<TaskItem>
        {
            Success = true,
            Message = $"Task {taskId} status updated to '{updatedTask.Status}'.",
            Data = updatedTask,
            TotalCount = 1
        });
    }

    // ─────────────────────────────────────────────────────────────────
    //  TOOL 7 — MarkAttendance
    // ─────────────────────────────────────────────────────────────────

    [HttpGet("attendance")]
    [ProducesResponseType(typeof(ApiResponse<List<AttendanceRecord>>), 200)]
    public IActionResult GetAttendanceList(
        [FromQuery] int? employeeId = null,
        [FromQuery] string? date = null,
        [FromQuery] string? status = null)
    {
        var attendance = _dataService.GetAttendanceRecords(employeeId, date, status);

        return Ok(new ApiResponse<List<AttendanceRecord>>
        {
            Success = true,
            Message = attendance.Count > 0
                ? $"Found {attendance.Count} attendance record(s)."
                : "No attendance records matched the filter criteria.",
            Data = attendance,
            TotalCount = attendance.Count
        });
    }

    /// <summary>
    /// Record or update attendance for an employee for a given date.
    /// </summary>
    [HttpPost("attendance")]
    [ProducesResponseType(typeof(ApiResponse<AttendanceRecord>), 201)]
    [ProducesResponseType(typeof(ApiResponse<AttendanceRecord>), 400)]
    [ProducesResponseType(typeof(ApiResponse<AttendanceRecord>), 404)]
    public IActionResult MarkAttendance([FromBody] AttendanceCreateRequest request)
    {
        if (request == null || request.EmployeeId <= 0 || string.IsNullOrWhiteSpace(request.Date) || string.IsNullOrWhiteSpace(request.Status))
        {
            return BadRequest(new ApiResponse<AttendanceRecord>
            {
                Success = false,
                Message = "Invalid attendance request. EmployeeId, Date, and Status are required.",
                Data = null,
                TotalCount = 0
            });
        }

        var employee = _dataService.GetEmployeeById(request.EmployeeId);
        if (employee == null)
        {
            return NotFound(new ApiResponse<AttendanceRecord>
            {
                Success = false,
                Message = $"No employee found with ID {request.EmployeeId}.",
                Data = null,
                TotalCount = 0
            });
        }

        var attendance = _dataService.MarkAttendance(request);
        if (attendance == null)
        {
            return BadRequest(new ApiResponse<AttendanceRecord>
            {
                Success = false,
                Message = "Unable to mark attendance. Please verify the request payload.",
                Data = null,
                TotalCount = 0
            });
        }

        return CreatedAtAction(nameof(GetAttendanceList), new { employeeId = attendance.EmployeeId, date = attendance.Date }, new ApiResponse<AttendanceRecord>
        {
            Success = true,
            Message = $"Attendance for {attendance.EmployeeName} on {attendance.Date} recorded successfully.",
            Data = attendance,
            TotalCount = 1
        });
    }
}
