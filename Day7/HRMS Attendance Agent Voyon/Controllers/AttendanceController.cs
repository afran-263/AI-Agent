using HrmsAgentApi.Dtos;
using HrmsAgentApi.Services;
using Microsoft.AspNetCore.Mvc;
using HrmsAgentApi.Models;

namespace HrmsAgentApi.Controllers;

/// <summary>
/// Attendance endpoints exposed to Azure AI Foundry as agent tools.
/// All data is fetched live from Voyon Folks HRMS using the configured Bearer token.
/// use this tool to get team attendance details and individual employee attendance details in that team.
/// </summary>
[ApiController]
[Route("api/hrms/attendance")]
[Produces("application/json")]
public class AttendanceController : ControllerBase
{
    private readonly VoyonHrmsClient _voyon;
    private readonly ILogger<AttendanceController> _logger;

    public AttendanceController(
        VoyonHrmsClient voyon,
        ILogger<AttendanceController> logger)
    {
        _voyon = voyon;
        _logger = logger;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // GET /api/hrms/attendance/team
    // ─────────────────────────────────────────────────────────────────────────

    /// <summary>Get full team attendance report for a manager on a specific date.</summary>
    /// <remarks>
    /// Returns present/absent/leave/weekly-off counts and per-employee details.
    /// Source: GET /m/api/Attendance/team-attendance on Voyon Folks HRMS.
    /// </remarks>
    [HttpGet("team")]
    [ProducesResponseType(typeof(ApiResponseDto<TeamAttendanceDto>), 200)]
    [ProducesResponseType(typeof(ApiResponseDto<object>), 400)]
    [ProducesResponseType(typeof(ApiResponseDto<object>), 502)]
    public async Task<IActionResult> GetTeamAttendance(
        [FromQuery] string? date = null,
        [FromQuery] string reportingType = "1",
        CancellationToken ct = default)
    {
        // Manager ID is fixed — never passed by the caller
        const int employeeId = 34110;

        var resolvedDate = date ?? DateTime.Today.ToString("yyyy-MM-dd");

        try
        {
            var raw = await _voyon.GetTeamAttendanceAsync(resolvedDate, reportingType, ct);

            if (raw.Response is null)
                return Ok(new ApiResponseDto<TeamAttendanceDto>
                {
                    Success = false,
                    Message = raw.MessageEN ?? "No data returned from Voyon Folks.",
                    Data = null, TotalCount = 0
                });

            var dto = new TeamAttendanceDto
            {
                Date             = resolvedDate,
                ManagerId        = employeeId,
                ReportedCount    = raw.Response.ReportedEmployees,
                AbsentCount      = raw.Response.NotReported,
                OnLeaveCount     = raw.Response.OnLeave,
                OnWeeklyOffCount = raw.Response.OnWeeklyOff,
                Employees        = raw.Response.EmployeeDetails.Select(e => new EmployeeAttendanceDto
                {
                    EmployeeId = e.EmployeeId,
                    EmployeeName = e.EmployeeName,
                    EmployeeCode = e.EmployeeCode,

                    ShiftStartTime = e.ShiftStartTime,
                    ShiftEndTime = e.ShiftEndTime,

                    WorkedHours = e.WorkedHours,
                    BreakHours = e.BreakHours,
                    LeaveHours = e.LeaveHours,

                    CheckInTime = e.CheckinTime,
                    CheckOutTime = e.CheckOutTime,

                    LeaveStartDate = e.LeaveStartDate,
                    LeaveToDate = e.LeaveToDate,

                    CheckInLatitude = e.CheckInLatitude,
                    CheckInLongitude = e.CheckInLongitude,

                    CheckOutLatitude = e.CheckOutLatitude,
                    CheckOutLongitude = e.CheckOutLongitude,

                    CheckInLocation = e.CheckInLocation,
                    CheckOutLocation = e.CheckOutLocation,

                    Status =
                        e.IsPublicHoliday ? $"Public Holiday ({e.HolidayName})" :
                        e.IsWeeklyOff ? "Weekly Off" :
                        e.IsLeave ? $"On Leave ({e.LeaveType})" :
                        e.IsAbsent ? "Absent" :
                        e.CheckinTime != null ? "Present" :
                        "Not Reported"
                }).ToList()
            };

            return Ok(new ApiResponseDto<TeamAttendanceDto>
            {
                Success = true,
                Message = $"Team attendance for {resolvedDate}: " +
                          $"{dto.ReportedCount} present, {dto.AbsentCount} absent, " +
                          $"{dto.OnLeaveCount} on leave.",
                Data       = dto,
                TotalCount = dto.Employees.Count
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "GetTeamAttendance failed for employeeId={Id}", employeeId);
            return StatusCode(502, new ApiResponseDto<object>
            {
                Success = false,
                Message = $"Failed to fetch data from Voyon Folks: {ex.Message}",
                Data = null, TotalCount = 0
            });
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // GET /api/hrms/attendance/absent
    // ─────────────────────────────────────────────────────────────────────────

    /// <summary>Get employees who are absent (not on leave) on a given date.</summary>
    /// <remarks>
    /// Fetches team-attendance and filters isAbsent=true, isLeave=false, isWeeklyOff=false.
    /// </remarks>
    [HttpGet("absent")]
    [ProducesResponseType(typeof(ApiResponseDto<List<EmployeeAttendanceDto>>), 200)]
    [ProducesResponseType(typeof(ApiResponseDto<object>), 400)]
    [ProducesResponseType(typeof(ApiResponseDto<object>), 502)]
    public async Task<IActionResult> GetAbsentEmployees(
        [FromQuery] string? date = null,
        CancellationToken ct = default)
    {
        // Manager ID is fixed — never passed by the caller
        const int employeeId = 34110;

        var resolvedDate = date ?? DateTime.Today.ToString("yyyy-MM-dd");

        try
        {
            var raw = await _voyon.GetTeamAttendanceAsync(resolvedDate, ct: ct);

            if (raw.Response is null)
                return Ok(new ApiResponseDto<List<EmployeeAttendanceDto>>
                {
                    Success = false,
                    Message = raw.MessageEN ?? "No data from Voyon Folks.",
                    Data = null, TotalCount = 0
                });

            var absent = raw.Response.EmployeeDetails
                .Where(e => e.IsAbsent && !e.IsLeave && !e.IsWeeklyOff && !e.IsPublicHoliday)
                .Select(e => new EmployeeAttendanceDto
                {
                    EmployeeId   = e.EmployeeId,
                    EmployeeName = e.EmployeeName,
                    EmployeeCode = e.EmployeeCode,
                    ShiftStartTime = e.ShiftStartTime,
                    ShiftEndTime = e.ShiftEndTime,
                    Status       = "Absent"
                }).ToList();

            return Ok(new ApiResponseDto<List<EmployeeAttendanceDto>>
            {
                Success    = true,
                Message    = absent.Count > 0
                    ? $"{absent.Count} employee(s) absent on {resolvedDate}."
                    : $"No employees absent on {resolvedDate}.",
                Data       = absent,
                TotalCount = absent.Count
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "GetAbsentEmployees failed for employeeId={Id}", employeeId);
            return StatusCode(502, new ApiResponseDto<object>
            {
                Success = false,
                Message = $"Failed to fetch data from Voyon Folks: {ex.Message}",
                Data = null, TotalCount = 0
            });
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // GET /api/hrms/attendance/present
    // ─────────────────────────────────────────────────────────────────────────

    /// <summary>Get employees who have checked in on a given date.</summary>
    /// <remarks>
    /// Fetches team-attendance and filters for employees where checkinTime is not null.
    /// </remarks>
    [HttpGet("present")]
    [ProducesResponseType(typeof(ApiResponseDto<List<EmployeeAttendanceDto>>), 200)]
    [ProducesResponseType(typeof(ApiResponseDto<object>), 400)]
    [ProducesResponseType(typeof(ApiResponseDto<object>), 502)]
    public async Task<IActionResult> GetPresentEmployees(
        [FromQuery] string? date = null,
        CancellationToken ct = default)
    {
        // Manager ID is fixed — never passed by the caller
        const int employeeId = 34110;

        var resolvedDate = date ?? DateTime.Today.ToString("yyyy-MM-dd");

        try
        {
            var raw = await _voyon.GetTeamAttendanceAsync(resolvedDate, ct: ct);

            if (raw.Response is null)
                return Ok(new ApiResponseDto<List<EmployeeAttendanceDto>>
                {
                    Success = false,
                    Message = raw.MessageEN ?? "No data from Voyon Folks.",
                    Data = null, TotalCount = 0
                });

            var present = raw.Response.EmployeeDetails
                .Where(e => !e.IsAbsent && e.CheckinTime != null)
                .Select(e => new EmployeeAttendanceDto
                {
                    EmployeeId   = e.EmployeeId,
                    EmployeeName = e.EmployeeName,
                    EmployeeCode = e.EmployeeCode,
                    ShiftStartTime = e.ShiftStartTime,
                    ShiftEndTime = e.ShiftEndTime,
                    CheckInTime = e.CheckinTime,
                    CheckOutTime = e.CheckOutTime,
                    WorkedHours  = e.WorkedHours,
                    Status       = "Present"
                }).ToList();

            return Ok(new ApiResponseDto<List<EmployeeAttendanceDto>>
            {
                Success    = true,
                Message    = $"{present.Count} employee(s) present on {resolvedDate}.",
                Data       = present,
                TotalCount = present.Count
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "GetPresentEmployees failed for employeeId={Id}", employeeId);
            return StatusCode(502, new ApiResponseDto<object>
            {
                Success = false,
                Message = $"Failed to fetch data from Voyon Folks: {ex.Message}",
                Data = null, TotalCount = 0
            });
        }
    }

    [HttpPost("mark")]
    [ProducesResponseType(typeof(ApiResponseDto<MarkAttendanceResultDto>), 200)]
    [ProducesResponseType(typeof(ApiResponseDto<object>), 400)]
    [ProducesResponseType(typeof(ApiResponseDto<object>), 502)]
    public async Task<IActionResult> MarkAttendance(
        [FromBody] MarkAttendanceRequestDto request,
        CancellationToken ct = default)
    {
        var resolvedDate = !string.IsNullOrWhiteSpace(request.AttendanceDate)
            ? request.AttendanceDate
            : DateTime.Today.ToString("yyyy-MM-dd");

        // ── 1. Use GetTeamAttendanceAsync exactly as GetTeamAttendance does ───
        var raw = await _voyon.GetTeamAttendanceAsync(resolvedDate, reportingType: "1", ct);

        if (raw.Response is null)
            return StatusCode(502, new ApiResponseDto<object>
            {
                Success = false,
                Message = raw.MessageEN ?? "No team roster returned from Voyon Folks.",
                Data = null, TotalCount = 0
            });

        // ── 2. Map to EmployeeAttendanceDto exactly as GetTeamAttendance does ─
        var employees = raw.Response.EmployeeDetails.Select(e => new EmployeeAttendanceDto
        {
            EmployeeId       = e.EmployeeId,
            EmployeeName     = e.EmployeeName,
            EmployeeCode     = e.EmployeeCode,
            ShiftStartTime   = e.ShiftStartTime,
            ShiftEndTime     = e.ShiftEndTime,
            WorkedHours      = e.WorkedHours,
            BreakHours       = e.BreakHours,
            LeaveHours       = e.LeaveHours,
            CheckInTime      = e.CheckinTime,
            CheckOutTime     = e.CheckOutTime,
            LeaveStartDate   = e.LeaveStartDate,
            LeaveToDate      = e.LeaveToDate,
            CheckInLatitude  = e.CheckInLatitude,
            CheckInLongitude = e.CheckInLongitude,
            CheckOutLatitude = e.CheckOutLatitude,
            CheckOutLongitude= e.CheckOutLongitude,
            CheckInLocation  = e.CheckInLocation,
            CheckOutLocation = e.CheckOutLocation,
            Status =
                e.IsPublicHoliday ? $"Public Holiday ({e.HolidayName})" :
                e.IsWeeklyOff     ? "Weekly Off" :
                e.IsLeave         ? $"On Leave ({e.LeaveType})" :
                e.IsAbsent        ? "Absent" :
                e.CheckinTime != null ? "Present" :
                "Not Reported"
        }).ToList();

        // ── 3. Match employee by ID or Name from the mapped list ──────────────
        EmployeeAttendanceDto? matched = null;

        if (request.EmployeeId > 0)
        {
            matched = employees.FirstOrDefault(e => e.EmployeeId == request.EmployeeId);

            if (matched is null)
                return BadRequest(new ApiResponseDto<object>
                {
                    Success = false,
                    Message = $"Employee with ID {request.EmployeeId} not found in the team roster for {resolvedDate}.",
                    Data = null, TotalCount = 0
                });
        }
        else if (!string.IsNullOrWhiteSpace(request.UserName))
        {
            matched = employees.FirstOrDefault(e =>
                e.EmployeeName.Contains(request.UserName, StringComparison.OrdinalIgnoreCase));

            if (matched is null)
                return BadRequest(new ApiResponseDto<object>
                {
                    Success = false,
                    Message = $"No employee matching '{request.UserName}' found in the team roster for {resolvedDate}.",
                    Data = null, TotalCount = 0
                });
        }
        else
        {
            return BadRequest(new ApiResponseDto<object>
            {
                Success = false,
                Message = "Please provide either EmployeeId or UserName to identify the employee.",
                Data = null, TotalCount = 0
            });
        }

        // ── 4. Build Voyon attendance model using resolved employee details ────

        // Use the time provided by the caller, or default to now
        var checkTime = !string.IsNullOrWhiteSpace(request.CheckInCheckOutTime)
            ? request.CheckInCheckOutTime
            : DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

        // Use the date provided by the caller, or default to today
        var attendanceDate = !string.IsNullOrWhiteSpace(request.AttendanceDate)
            ? request.AttendanceDate
            : DateTime.Today.ToString("yyyy-MM-dd");

        // Normalise IsCheckInorCheckOut — accept "CI", "CheckIn", "checkin", "check-in" → "CheckIn"
        //                                          "CO", "CheckOut", "checkout", "check-out" → "CheckOut"
        var actionRaw = request.IsCheckInorCheckOut ?? "CheckIn";
        var isCheckIn = actionRaw.Replace("-", "").Replace("_", "")
                            .StartsWith("ci", StringComparison.OrdinalIgnoreCase)
                        || actionRaw.Replace("-", "").Replace("_", "")
                            .StartsWith("checkin", StringComparison.OrdinalIgnoreCase);
        var normalizedAction = isCheckIn ? "CheckIn" : "CheckOut";

        var voyonModel = new AttendanceCheckInCheckOutModel
        {
            Location            = string.Empty,
            Comment             = string.Empty,
            IP                  = string.Empty,
            CheckInCheckOutTime = checkTime,        // ← use caller-supplied time, not DateTime.Now
            AttendanceDate      = attendanceDate,   // ← use caller-supplied date, not DateTime.Today

            EmployeeId = matched.EmployeeId,
            UserName   = matched.EmployeeName,

            CompanyId = 389,   // hardcoded from JWT / appsettings — never taken from caller
            ShiftId   = 0,

            IsCheckInorCheckOut = normalizedAction, // ← safe normalised value

            CheckInLatitude  = 0,
            CheckOutLatitude = 0,
            CheckInLongitude = 0,
            CheckOutLongitude = 0
        };

        // ── 5. POST to Voyon AttendanceLog ────────────────────────────────────
        try
        {
            var result = await _voyon.PostAttendanceLogAsync(voyonModel, ct);
            var action = normalizedAction == "CheckOut" ? "Check-Out" : "Check-In";

            return Ok(new ApiResponseDto<MarkAttendanceResultDto>
            {
                Success    = true,
                Message    = result.MessageEN ?? $"{action} recorded for {matched.EmployeeName}.",
                Data       = new MarkAttendanceResultDto
                {
                    EmployeeId          = matched.EmployeeId,
                    EmployeeName        = matched.EmployeeName,
                    AttendanceDate      = resolvedDate,
                    CheckInCheckOutTime = checkTime,
                    Action              = action,
                    VoyonMessage        = result.MessageEN ?? string.Empty
                },
                TotalCount = 1
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "MarkAttendance: PostAttendanceLog failed for employee={Id}", matched.EmployeeId);
            return StatusCode(502, new ApiResponseDto<object>
            {
                Success = false,
                Message = $"Failed to mark attendance in Voyon Folks: {ex.Message}",
                Data = null, TotalCount = 0
            });
        }
    }

}
