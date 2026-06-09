namespace HrmsAgentApi.Dtos;

public class TaskItemDto
{
    public int TaskId { get; set; }
    public int EmployeeId { get; set; }
    public string EmployeeName { get; set; } = "";
    public string Title { get; set; } = "";
    public string Description { get; set; } = "";
    public string Priority { get; set; } = "";
    public string Status { get; set; } = "";
    public string DueDate { get; set; } = "";
    public string AssignedBy { get; set; } = "";
    public string Category { get; set; } = "";
}
