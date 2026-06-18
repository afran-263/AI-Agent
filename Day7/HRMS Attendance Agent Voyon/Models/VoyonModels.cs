using System.Text.Json.Serialization;

namespace HrmsAgentApi.Models;

// ─── Team Attendance ──────────────────────────────────────────────────────────

public record TeamAttendanceApiResponse(
    [property: JsonPropertyName("response")] TeamAttendanceData? Response,
    [property: JsonPropertyName("errorCode")] string? ErrorCode,
    [property: JsonPropertyName("messageEN")] string? MessageEN,
    [property: JsonPropertyName("messageAR")] string? MessageAR
);

public record TeamAttendanceData(
    [property: JsonPropertyName("reportedEmployees")] int ReportedEmployees,
    [property: JsonPropertyName("onLeave")]           int OnLeave,
    [property: JsonPropertyName("onWeeklyOff")]       int OnWeeklyOff,
    [property: JsonPropertyName("notReported")]       int NotReported,
    [property: JsonPropertyName("employeeDetails")]   List<VoyonEmployeeAttendance> EmployeeDetails
);

public record VoyonEmployeeAttendance(
    [property: JsonPropertyName("employeeName")]      string EmployeeName,
    [property: JsonPropertyName("employeeId")]        int EmployeeId,
    [property: JsonPropertyName("shortName")]         string ShortName,
    [property: JsonPropertyName("employeeCode")]      string EmployeeCode,
    [property: JsonPropertyName("employeeCategory")]  string EmployeeCategory,

    [property: JsonPropertyName("shiftStartTime")]    string ShiftStartTime,
    [property: JsonPropertyName("shiftEndTime")]      string ShiftEndTime,

    [property: JsonPropertyName("workedHours")]       string WorkedHours,
    [property: JsonPropertyName("breakHours")]        string? BreakHours,
    [property: JsonPropertyName("leaveHours")]        string? LeaveHours,

    [property: JsonPropertyName("checkinTime")]       string? CheckinTime,
    [property: JsonPropertyName("checkOutTime")]      string? CheckOutTime,

    [property: JsonPropertyName("isAbsent")]          bool IsAbsent,
    [property: JsonPropertyName("isLeave")]           bool IsLeave,

    [property: JsonPropertyName("leaveType")]         string? LeaveType,
    [property: JsonPropertyName("leaveReason")]       string? LeaveReason,

    [property: JsonPropertyName("isWeeklyOff")]       bool IsWeeklyOff,
    [property: JsonPropertyName("isPublicHoliday")]   bool IsPublicHoliday,

    [property: JsonPropertyName("holidayName")]       string? HolidayName,

    [property: JsonPropertyName("leaveStartDate")]    string? LeaveStartDate,
    [property: JsonPropertyName("leaveToDate")]       string? LeaveToDate,

    [property: JsonPropertyName("checkInLatitude")]   string? CheckInLatitude,
    [property: JsonPropertyName("checkInLongitude")]  string? CheckInLongitude,

    [property: JsonPropertyName("checkOutLatitude")]  string? CheckOutLatitude,
    [property: JsonPropertyName("checkOutLongitude")] string? CheckOutLongitude,

    [property: JsonPropertyName("checkInLocation")]   string? CheckInLocation,
    [property: JsonPropertyName("checkOutLocation")]  string? CheckOutLocation,

    [property: JsonPropertyName("employeePhoto")]     string? EmployeePhoto
);

// ─── Attendance Check-In / Check-Out ─────────────────────────────────────────
// POST /m/api/Attendance/AttendanceLog

public class AttendanceCheckInCheckOutModel
{
    [JsonPropertyName("Location")]
    public string Location { get; set; } = string.Empty;

    [JsonPropertyName("Comment")]
    public string Comment { get; set; } = string.Empty;

    [JsonPropertyName("IP")]
    public string IP { get; set; } = string.Empty;

    [JsonPropertyName("CheckInCheckOutTime")]
    public string CheckInCheckOutTime { get; set; } = string.Empty;

    [JsonPropertyName("AttendanceDate")]
    public string AttendanceDate { get; set; } = string.Empty;

    [JsonPropertyName("EmployeeId")]
    public int EmployeeId { get; set; }

    [JsonPropertyName("UserName")]
    public string UserName { get; set; } = string.Empty;

    [JsonPropertyName("CompanyId")]
    public int CompanyId { get; set; }

    [JsonPropertyName("ShiftId")]
    public int ShiftId { get; set; }

    [JsonPropertyName("IsCheckInorCheckOut")]
    public string IsCheckInorCheckOut { get; set; } = string.Empty;

    [JsonPropertyName("CheckInLatitude")]
    public int CheckInLatitude { get; set; }

    [JsonPropertyName("CheckOutLatitude")]
    public int CheckOutLatitude { get; set; }

    [JsonPropertyName("CheckInLongitude")]
    public int CheckInLongitude { get; set; }

    [JsonPropertyName("CheckOutLongitude")]
    public int CheckOutLongitude { get; set; }
    }

public record AttendanceLogApiResponse(
    [property: JsonPropertyName("response")]  object?  Response,
    [property: JsonPropertyName("errorCode")] string?  ErrorCode,
    [property: JsonPropertyName("messageEN")] string?  MessageEN,
    [property: JsonPropertyName("messageAR")] string?  MessageAR
);
