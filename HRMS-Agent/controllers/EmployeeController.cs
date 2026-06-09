using HrmsAgentApi.Models;
using HrmsAgentApi.Dtos;
using HrmsAgentApi.Services;
using Microsoft.AspNetCore.Mvc;

namespace HrmsAgentApi.Controllers;

[ApiController]
[Route("api/hrms/employees")]
[Produces("application/json")]
public class EmployeeController : ControllerBase
{
    private readonly HrmsDataService _dataService;

    public EmployeeController(HrmsDataService dataService)
    {
        _dataService = dataService;
    }

    [HttpGet]
    [ProducesResponseType(typeof(ApiResponseDto<List<EmployeeSummaryDto>>), 200)]
    public IActionResult GetEmployeeList(
        [FromQuery] string? department = null,
        [FromQuery] string? status = null,
        [FromQuery] string? salary = null)
    {
        var employees = _dataService.GetAllEmployees(department, status, salary);

        return Ok(new ApiResponseDto<List<EmployeeSummaryDto>>
        {
            Success = true,
            Message = employees.Count > 0
                ? $"Found {employees.Count} employee(s)."
                : "No employees matched the filter criteria.",
            Data = employees.Select(e => e.ToDto()).ToList(),
            TotalCount = employees.Count
        });
    }

    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(ApiResponseDto<EmployeeDto>), 200)]
    [ProducesResponseType(typeof(ApiResponseDto<EmployeeDto>), 404)]
    public IActionResult GetEmployeeDetails(int id)
    {
        var employee = _dataService.GetEmployeeById(id);

        if (employee == null)
        {
            return NotFound(new ApiResponseDto<EmployeeDto>
            {
                Success = false,
                Message = $"No employee found with ID {id}. Please check the ID and try again.",
                Data = null,
                TotalCount = 0
            });
        }

        return Ok(new ApiResponseDto<EmployeeDto>
        {
            Success = true,
            Message = $"Employee details retrieved successfully for ID {id}.",
            Data = employee.ToDto(),
            TotalCount = 1
        });
    }
}
