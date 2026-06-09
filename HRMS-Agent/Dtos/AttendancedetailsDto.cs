namespace HrmsAgentApi.Dtos;

public class AttendanceDetailsDto
{
    public int AttendanceId { get; set; }
    public int EmployeeId { get; set; }
    public string EmployeeName { get; set; } = "";
    public string Date { get; set; } = "";
    public string Status { get; set; } = "";
    public string CheckInTime { get; set; } = "";
    public string CheckOutTime { get; set; } = "";
}
