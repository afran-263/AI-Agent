using HrmsAgentApi.Models;
using HrmsAgentApi.Dtos;
using HrmsAgentApi.Services;
using Microsoft.AspNetCore.Mvc;

namespace HrmsAgentApi.Controllers;

[ApiController]
[Route("api/hrms/tasks")]
[Produces("application/json")]
public class TaskController : ControllerBase
{
    private readonly HrmsDataService _dataService;

    public TaskController(HrmsDataService dataService)
    {
        _dataService = dataService;
    }

    [HttpGet]
    [ProducesResponseType(typeof(ApiResponseDto<List<TaskItemDto>>), 200)]
    public IActionResult GetTaskList(
        [FromQuery] int? employeeId = null,
        [FromQuery] string? status = null,
        [FromQuery] string? priority = null)
    {
        if (employeeId.HasValue)
        {
            var employee = _dataService.GetEmployeeById(employeeId.Value);
            if (employee == null)
            {
                return NotFound(new ApiResponseDto<List<TaskItemDto>>
                {
                    Success = false,
                    Message = $"No employee found with ID {employeeId}.",
                    Data = new List<TaskItemDto>(),
                    TotalCount = 0
                });
            }

            var tasks = _dataService.GetTasksByEmployeeId(employeeId.Value);
            var message = tasks.Count > 0
                ? $"Found {tasks.Count} task(s) for {employee.Name}."
                : $"No tasks assigned to {employee.Name} yet.";

            return Ok(new ApiResponseDto<List<TaskItemDto>>
            {
                Success = true,
                Message = message,
                Data = tasks.Select(t => t.ToDto()).ToList(),
                TotalCount = tasks.Count
            });
        }

        var allTasks = _dataService.GetAllTasks(status, priority);
        return Ok(new ApiResponseDto<List<TaskItemDto>>
        {
            Success = true,
            Message = $"Retrieved {allTasks.Count} task(s).",
            Data = allTasks.Select(t => t.ToDto()).ToList(),
            TotalCount = allTasks.Count
        });
    }

    [HttpPost]
    [ProducesResponseType(typeof(ApiResponseDto<TaskItemDto>), 201)]
    [ProducesResponseType(typeof(ApiResponseDto<TaskItemDto>), 400)]
    [ProducesResponseType(typeof(ApiResponseDto<TaskItemDto>), 404)]
    public IActionResult CreateTask([FromBody] TaskCreateDto request)
    {
        if (request == null || request.EmployeeId <= 0 || string.IsNullOrWhiteSpace(request.Title))
        {
            return BadRequest(new ApiResponseDto<TaskItemDto>
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
            return NotFound(new ApiResponseDto<TaskItemDto>
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

        return CreatedAtAction(nameof(GetTaskList), new { employeeId = createdTask.EmployeeId }, new ApiResponseDto<TaskItemDto>
        {
            Success = true,
            Message = $"Task '{createdTask.Title}' created and assigned to {createdTask.EmployeeName}.",
            Data = createdTask.ToDto(),
            TotalCount = 1
        });
    }

    [HttpPut("{taskId:int}/assign")]
    [ProducesResponseType(typeof(ApiResponseDto<TaskItemDto>), 200)]
    [ProducesResponseType(typeof(ApiResponseDto<TaskItemDto>), 400)]
    [ProducesResponseType(typeof(ApiResponseDto<TaskItemDto>), 404)]
    public IActionResult AssignTask(int taskId, [FromBody] TaskAssignDto request)
    {
        if (request == null || request.EmployeeId <= 0)
        {
            return BadRequest(new ApiResponseDto<TaskItemDto>
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
            return NotFound(new ApiResponseDto<TaskItemDto>
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
            return NotFound(new ApiResponseDto<TaskItemDto>
            {
                Success = false,
                Message = $"No task found with ID {taskId}.",
                Data = null,
                TotalCount = 0
            });
        }

        return Ok(new ApiResponseDto<TaskItemDto>
        {
            Success = true,
            Message = $"Task {taskId} reassigned to {updatedTask.EmployeeName}.",
            Data = updatedTask.ToDto(),
            TotalCount = 1
        });
    }

    [HttpPut("{taskId:int}/status")]
    [ProducesResponseType(typeof(ApiResponseDto<TaskItemDto>), 200)]
    [ProducesResponseType(typeof(ApiResponseDto<TaskItemDto>), 400)]
    [ProducesResponseType(typeof(ApiResponseDto<TaskItemDto>), 404)]
    public IActionResult UpdateTaskStatus(int taskId, [FromBody] TaskStatusUpdateDto request)
    {
        if (request == null || string.IsNullOrWhiteSpace(request.Status))
        {
            return BadRequest(new ApiResponseDto<TaskItemDto>
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
            return NotFound(new ApiResponseDto<TaskItemDto>
            {
                Success = false,
                Message = $"No task found with ID {taskId}.",
                Data = null,
                TotalCount = 0
            });
        }

        return Ok(new ApiResponseDto<TaskItemDto>
        {
            Success = true,
            Message = $"Task {taskId} status updated to '{updatedTask.Status}'.",
            Data = updatedTask.ToDto(),
            TotalCount = 1
        });
    }
}
