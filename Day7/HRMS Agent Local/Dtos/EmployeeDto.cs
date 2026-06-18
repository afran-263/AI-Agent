namespace HrmsAgentApi.Dtos;

public class EmployeeDto
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
    public string Department { get; set; } = "";
    public string Designation { get; set; } = "";
    public string Phone { get; set; } = "";
    public string JoiningDate { get; set; } = "";
    public string Status { get; set; } = "";
    public string ReportingManager { get; set; } = "";
    public decimal Salary { get; set; }
    public string Location { get; set; } = "";
}
