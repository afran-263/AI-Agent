namespace HrmsAgentApi.Models;

public class EmployeeSummary
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Department { get; set; } = "";
    public string Designation { get; set; } = "";
    public string Status { get; set; } = "";
    public decimal Salary { get; set; }
}
