namespace HrmsAgentApi.Dtos;

public class TaskCreateDto
{
    public int EmployeeId { get; set; }
    public string Title { get; set; } = "";
    public string Description { get; set; } = "";
    public string Priority { get; set; } = "";
    public string? Status { get; set; }
    public string DueDate { get; set; } = "";
    public string AssignedBy { get; set; } = "";
    public string Category { get; set; } = "";
}
