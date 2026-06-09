using HrmsAgentApi.Models;
using HrmsAgentApi.Dtos;
using HrmsAgentApi.Services;
using Microsoft.AspNetCore.Mvc;

namespace HrmsAgentApi.Controllers;

[ApiController]

[Route("api/hrms/attendance")]
[Produces("application/json")]
public class AttendanceController : ControllerBase
{
    private readonly HrmsDataService _dataService;

    public AttendanceController(HrmsDataService dataService)
    {
        _dataService = dataService;
    }

    [HttpGet]
    [ProducesResponseType(typeof(ApiResponseDto<List<AttendanceRecordDto>>), 200)]
    public IActionResult GetAttendanceList(
        [FromQuery] int? employeeId = null,
        [FromQuery] int? AttendanceId = null,
        [FromQuery] string? date = null,
        [FromQuery] string? status = null)
    {
        var attendance = _dataService.GetAttendanceRecords(employeeId, AttendanceId,date, status);

        return Ok(new ApiResponseDto<List<AttendanceRecordDto>>
        {
            Success = true,
            Message = attendance.Count > 0
                ? $"Found {attendance.Count} attendance record(s)."
                : "No attendance records matched the filter criteria.",
            Data = attendance.Select(a => a.ToDto()).ToList(),
            TotalCount = attendance.Count
        });
    }

    [HttpPost]
    [ProducesResponseType(typeof(ApiResponseDto<AttendanceRecordDto>), 201)]
    [ProducesResponseType(typeof(ApiResponseDto<AttendanceRecordDto>), 400)]
    [ProducesResponseType(typeof(ApiResponseDto<AttendanceRecordDto>), 404)]
    public IActionResult MarkAttendance([FromBody] AttendanceCreateDto request)
    {
        if (request == null || request.EmployeeId <= 0 || string.IsNullOrWhiteSpace(request.Date) || string.IsNullOrWhiteSpace(request.Status))
        {
            return BadRequest(new ApiResponseDto<AttendanceRecordDto>
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
            return NotFound(new ApiResponseDto<AttendanceRecordDto>
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
            return BadRequest(new ApiResponseDto<AttendanceRecordDto>
            {
                Success = false,
                Message = "Unable to mark attendance. Please verify the request payload.",
                Data = null,
                TotalCount = 0
            });
        }

        return CreatedAtAction(nameof(GetAttendanceList), new { employeeId = attendance.EmployeeId, date = attendance.Date }, new ApiResponseDto<AttendanceRecordDto>
        {
            Success = true,
            Message = $"Attendance for {attendance.EmployeeName} on {attendance.Date} recorded successfully.",
            Data = attendance.ToDto(),
            TotalCount = 1
        });
    }
}
