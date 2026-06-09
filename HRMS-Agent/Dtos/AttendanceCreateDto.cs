namespace HrmsAgentApi.Dtos;

public class AttendanceCreateDto
{
    public int EmployeeId { get; set; }
    public string Date { get; set; } = "";
    public string Status { get; set; } = "";
    public string? CheckInTime { get; set; }
    public string? CheckOutTime { get; set; }
    public string? Notes { get; set; }
}
