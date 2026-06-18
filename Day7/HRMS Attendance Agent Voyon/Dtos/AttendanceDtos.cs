namespace HrmsAgentApi.Dtos;

// ─── Response wrapper ─────────────────────────────────────────────────────────

public class ApiResponseDto<T>
{
    public bool    Success    { get; set; }
    public string  Message    { get; set; } = "";
    public T?      Data       { get; set; }
    public int     TotalCount { get; set; }
}

// ─── Team Attendance ──────────────────────────────────────────────────────────

public class TeamAttendanceDto
{
    public string Date             { get; set; } = "";
    public int    ManagerId        { get; set; }
    public int    ReportedCount    { get; set; }
    public int    AbsentCount      { get; set; }
    public int    OnLeaveCount     { get; set; }
    public int    OnWeeklyOffCount { get; set; }
    public List<EmployeeAttendanceDto> Employees { get; set; } = [];
}

public record EmployeeAttendanceDto
{
    public int     EmployeeId       { get; init; }
    public string  EmployeeName     { get; init; } = "";
    public string  EmployeeCode     { get; init; } = "";
    public string  ShiftStartTime   { get; init; } = "";
    public string  ShiftEndTime     { get; init; } = "";
    public string  WorkedHours      { get; init; } = "";
    public string? BreakHours       { get; init; }
    public string? LeaveHours       { get; init; }
    public string? CheckInTime      { get; init; }
    public string? CheckOutTime     { get; init; }
    public string? LeaveStartDate   { get; init; }
    public string? LeaveToDate      { get; init; }
    public string? CheckInLatitude  { get; init; }
    public string? CheckInLongitude { get; init; }
    public string? CheckOutLatitude { get; init; }
    public string? CheckOutLongitude{ get; init; }
    public string? CheckInLocation  { get; init; }
    public string? CheckOutLocation { get; init; }
    public string  Status           { get; init; } = "";
}

// ─── Mark Attendance (Check-In / Check-Out) ───────────────────────────────────

/// <summary>
/// Agent-facing request to mark attendance for an employee.
/// Supply either EmployeeId (int) OR UserName (partial name string) to identify the employee.
/// The manager ID is hardcoded as 34110 — do NOT ask the user for it.
/// CompanyId is hardcoded as 389 and ShiftId as 0 — do NOT ask the user for them.
/// IsCheckInorCheckOut: "CheckIn" = Check-In, "CheckOut" = Check-Out.
///   Also accepts "CI", "checkin", "check-in" (→ CheckIn) and "CO", "checkout", "check-out" (→ CheckOut).
///   Defaults to "CheckIn" if omitted.
/// AttendanceDate and CheckInCheckOutTime default to today/now if not provided.
/// </summary>
public class MarkAttendanceRequestDto
{
    public string? Location { get; set; }
    public string? Comment { get; set; }
    public string? IP { get; set; }
    public string? CheckInCheckOutTime { get; set; }
    public string? AttendanceDate { get; set; }
    public int EmployeeId { get; set; }
    public string? UserName { get; set; }
    public int CompanyId { get; set; }
    public int ShiftId { get; set; }

    /// <summary>Must be "CheckIn" for Check-In or "CheckOut" for Check-Out. Also accepts "CI"/"CO" and case-insensitive variants.</summary>
    public string? IsCheckInorCheckOut { get; set; }

    public double CheckInLatitude { get; set; }
    public double CheckOutLatitude { get; set; }
    public double CheckInLongitude { get; set; }
    public double CheckOutLongitude { get; set; }
}

/// <summary>Result returned to the agent after marking attendance.</summary>
public record MarkAttendanceResultDto
{
    public int    EmployeeId          { get; init; }
    public string EmployeeName        { get; init; } = "";
    public string AttendanceDate      { get; init; } = "";
    public string CheckInCheckOutTime { get; init; } = "";
    public string Action              { get; init; } = "";   // "Check-In" or "Check-Out"
    public string VoyonMessage        { get; init; } = "";
}
