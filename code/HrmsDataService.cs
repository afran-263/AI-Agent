using HrmsAgentApi.Models;

namespace HrmsAgentApi.Services;

public class HrmsDataService
{
    private readonly List<Employee> _employees;
    private readonly List<TaskItem> _tasks;
    private readonly List<AttendanceRecord> _attendance;

    public HrmsDataService()
    {
        _employees = SeedEmployees();
        _tasks = SeedTasks();
        _attendance = SeedAttendance();
    }

    // ─────────────────────────────────────────────
    //  PUBLIC METHODS (used by controllers)
    // ─────────────────────────────────────────────

    public List<EmployeeSummary> GetAllEmployees(string? department = null, string? status = null)
    {
        var query = _employees.AsQueryable();

        if (!string.IsNullOrWhiteSpace(department))
            query = query.Where(e => e.Department.Equals(department, StringComparison.OrdinalIgnoreCase));

        if (!string.IsNullOrWhiteSpace(status))
            query = query.Where(e => e.Status.Equals(status, StringComparison.OrdinalIgnoreCase));

        return query.Select(e => new EmployeeSummary
        {
            Id = e.Id,
            Name = e.Name,
            Department = e.Department,
            Designation = e.Designation,
            Status = e.Status
        }).ToList();
    }

    public Employee? GetEmployeeById(int id) =>
        _employees.FirstOrDefault(e => e.Id == id);

    public List<TaskItem> GetTasksByEmployeeId(int employeeId) =>
        _tasks.Where(t => t.EmployeeId == employeeId).ToList();

    public List<TaskItem> GetAllTasks(string? status = null, string? priority = null)
    {
        var query = _tasks.AsQueryable();

        if (!string.IsNullOrWhiteSpace(status))
            query = query.Where(t => t.Status.Equals(status, StringComparison.OrdinalIgnoreCase));

        if (!string.IsNullOrWhiteSpace(priority))
            query = query.Where(t => t.Priority.Equals(priority, StringComparison.OrdinalIgnoreCase));

        return query.ToList();
    }

    public TaskItem AddTask(TaskItem newTask)
    {
        newTask.TaskId = _tasks.Any() ? _tasks.Max(t => t.TaskId) + 1 : 101;
        var employee = GetEmployeeById(newTask.EmployeeId);
        newTask.EmployeeName = employee?.Name ?? string.Empty;

        _tasks.Add(newTask);
        return newTask;
    }

    public TaskItem? AssignTask(int taskId, int employeeId)
    {
        var task = _tasks.FirstOrDefault(t => t.TaskId == taskId);
        if (task == null)
            return null;

        var employee = GetEmployeeById(employeeId);
        if (employee == null)
            return null;

        task.EmployeeId = employee.Id;
        task.EmployeeName = employee.Name;
        return task;
    }

    public TaskItem? UpdateTaskStatus(int taskId, string status)
    {
        var task = _tasks.FirstOrDefault(t => t.TaskId == taskId);
        if (task == null || string.IsNullOrWhiteSpace(status))
            return null;

        task.Status = status.Trim();
        return task;
    }

    public List<AttendanceRecord> GetAttendanceRecords(int? employeeId = null, string? date = null, string? status = null)
    {
        var query = _attendance.AsQueryable();

        if (employeeId.HasValue)
            query = query.Where(a => a.EmployeeId == employeeId.Value);

        if (!string.IsNullOrWhiteSpace(date))
            query = query.Where(a => a.Date.Equals(date, StringComparison.OrdinalIgnoreCase));

        if (!string.IsNullOrWhiteSpace(status))
            query = query.Where(a => a.Status.Equals(status, StringComparison.OrdinalIgnoreCase));

        return query.ToList();
    }

    public AttendanceRecord AddAttendanceRecord(AttendanceRecord record)
    {
        record.AttendanceId = _attendance.Any() ? _attendance.Max(a => a.AttendanceId) + 1 : 1;
        var employee = GetEmployeeById(record.EmployeeId);
        record.EmployeeName = employee?.Name ?? string.Empty;
        _attendance.Add(record);
        return record;
    }

    public AttendanceRecord? MarkAttendance(AttendanceCreateRequest request)
    {
        if (request == null || request.EmployeeId <= 0 || string.IsNullOrWhiteSpace(request.Date) || string.IsNullOrWhiteSpace(request.Status))
            return null;

        var employee = GetEmployeeById(request.EmployeeId);
        if (employee == null)
            return null;

        var existing = _attendance.FirstOrDefault(a => a.EmployeeId == request.EmployeeId &&
                                                     a.Date.Equals(request.Date, StringComparison.OrdinalIgnoreCase));

        if (existing != null)
        {
            existing.Status = request.Status.Trim();
            existing.CheckInTime = request.CheckInTime?.Trim() ?? string.Empty;
            existing.CheckOutTime = request.CheckOutTime?.Trim() ?? string.Empty;
            existing.Notes = request.Notes?.Trim() ?? string.Empty;
            return existing;
        }

        var attendance = new AttendanceRecord
        {
            EmployeeId = employee.Id,
            EmployeeName = employee.Name,
            Date = request.Date.Trim(),
            Status = request.Status.Trim(),
            CheckInTime = request.CheckInTime?.Trim() ?? string.Empty,
            CheckOutTime = request.CheckOutTime?.Trim() ?? string.Empty,
            Notes = request.Notes?.Trim() ?? string.Empty
        };

        return AddAttendanceRecord(attendance);
    }

    // ─────────────────────────────────────────────
    //  SEED DATA 
    // ─────────────────────────────────────────────

    private static List<Employee> SeedEmployees() => new()
    {
        new Employee
        {
            Id = 1, Name = "Arjun Nair", Email = "arjun.nair@hrms.com",
            Department = "Engineering", Designation = "Senior Software Engineer",
            Phone = "+91-9876543210", JoiningDate = "2020-06-15",
            Status = "Active", ReportingManager = "Priya Menon",
            Salary = 85000, Location = "Kochi, Kerala"
        },
        new Employee
        {
            Id = 2, Name = "Priya Menon", Email = "priya.menon@hrms.com",
            Department = "Engineering", Designation = "Engineering Manager",
            Phone = "+91-9876543211", JoiningDate = "2018-03-01",
            Status = "Active", ReportingManager = "Rajesh Kumar",
            Salary = 120000, Location = "Kochi, Kerala"
        },
        new Employee
        {
            Id = 3, Name = "Deepa Krishnan", Email = "deepa.krishnan@hrms.com",
            Department = "Human Resources", Designation = "HR Business Partner",
            Phone = "+91-9876543212", JoiningDate = "2019-09-10",
            Status = "Active", ReportingManager = "Sunita Rao",
            Salary = 70000, Location = "Thiruvananthapuram, Kerala"
        },
        new Employee
        {
            Id = 4, Name = "Mohammed Farhan", Email = "mohammed.farhan@hrms.com",
            Department = "Finance", Designation = "Financial Analyst",
            Phone = "+91-9876543213", JoiningDate = "2021-01-20",
            Status = "Active", ReportingManager = "Anil Thomas",
            Salary = 65000, Location = "Kozhikode, Kerala"
        },
        new Employee
        {
            Id = 5, Name = "Sneha Pillai", Email = "sneha.pillai@hrms.com",
            Department = "Marketing", Designation = "Digital Marketing Specialist",
            Phone = "+91-9876543214", JoiningDate = "2022-04-05",
            Status = "Active", ReportingManager = "Kavitha Nambiar",
            Salary = 60000, Location = "Thrissur, Kerala"
        },
        new Employee
        {
            Id = 6, Name = "Rajesh Kumar", Email = "rajesh.kumar@hrms.com",
            Department = "Engineering", Designation = "CTO",
            Phone = "+91-9876543215", JoiningDate = "2016-07-01",
            Status = "Active", ReportingManager = "CEO",
            Salary = 250000, Location = "Bangalore, Karnataka"
        },
        new Employee
        {
            Id = 7, Name = "Anita George", Email = "anita.george@hrms.com",
            Department = "Operations", Designation = "Operations Coordinator",
            Phone = "+91-9876543216", JoiningDate = "2020-11-15",
            Status = "Active", ReportingManager = "Binu Varghese",
            Salary = 55000, Location = "Ernakulam, Kerala"
        },
        new Employee
        {
            Id = 8, Name = "Vivek Sharma", Email = "vivek.sharma@hrms.com",
            Department = "Engineering", Designation = "DevOps Engineer",
            Phone = "+91-9876543217", JoiningDate = "2021-08-20",
            Status = "On Leave", ReportingManager = "Priya Menon",
            Salary = 78000, Location = "Kochi, Kerala"
        },
        new Employee
        {
            Id = 9, Name = "Lakshmi Devi", Email = "lakshmi.devi@hrms.com",
            Department = "Human Resources", Designation = "HR Manager",
            Phone = "+91-9876543218", JoiningDate = "2017-05-12",
            Status = "Active", ReportingManager = "Sunita Rao",
            Salary = 90000, Location = "Kochi, Kerala"
        },
        new Employee
        {
            Id = 10, Name = "Arun Chandran", Email = "arun.chandran@hrms.com",
            Department = "Finance", Designation = "Senior Accountant",
            Phone = "+91-9876543219", JoiningDate = "2019-02-28",
            Status = "Active", ReportingManager = "Anil Thomas",
            Salary = 72000, Location = "Palakkad, Kerala"
        }
    };

    private static List<AttendanceRecord> SeedAttendance() => new()
    {
        new AttendanceRecord
        {
            AttendanceId = 1,
            EmployeeId = 1,
            EmployeeName = "Arjun Nair",
            Date = "2026-06-08",
            Status = "Present",
            CheckInTime = "09:05",
            CheckOutTime = "18:00",
            Notes = "Work from office"
        },
        new AttendanceRecord
        {
            AttendanceId = 2,
            EmployeeId = 2,
            EmployeeName = "Priya Menon",
            Date = "2026-06-08",
            Status = "Present",
            CheckInTime = "09:00",
            CheckOutTime = "18:10",
            Notes = "Team planning day"
        }
    };

    private static List<TaskItem> SeedTasks() => new()
    {
        new TaskItem
        {
            TaskId = 101, EmployeeId = 1, EmployeeName = "Arjun Nair",
            Title = "Implement REST API for Payroll Module",
            Description = "Build and test the payroll calculation REST API endpoints including overtime and deductions.",
            Priority = "High", Status = "In Progress",
            DueDate = "2025-07-15", AssignedBy = "Priya Menon", Category = "Development"
        },
        new TaskItem
        {
            TaskId = 102, EmployeeId = 1, EmployeeName = "Arjun Nair",
            Title = "Code Review – Leave Management PR",
            Description = "Review and approve the pull request for the leave management feature submitted by junior devs.",
            Priority = "Medium", Status = "Pending",
            DueDate = "2025-07-08", AssignedBy = "Priya Menon", Category = "Review"
        },
        new TaskItem
        {
            TaskId = 103, EmployeeId = 2, EmployeeName = "Priya Menon",
            Title = "Q3 Sprint Planning",
            Description = "Prepare sprint backlog and conduct planning session for all engineering teams.",
            Priority = "High", Status = "Completed",
            DueDate = "2025-07-01", AssignedBy = "Rajesh Kumar", Category = "Management"
        },
        new TaskItem
        {
            TaskId = 104, EmployeeId = 3, EmployeeName = "Deepa Krishnan",
            Title = "New Employee Onboarding – Batch July 2025",
            Description = "Coordinate orientation, system access setup, and buddy assignment for 5 new joiners.",
            Priority = "High", Status = "In Progress",
            DueDate = "2025-07-10", AssignedBy = "Lakshmi Devi", Category = "HR"
        },
        new TaskItem
        {
            TaskId = 105, EmployeeId = 4, EmployeeName = "Mohammed Farhan",
            Title = "Monthly Financial Reconciliation – June 2025",
            Description = "Reconcile all expense reports, vendor invoices, and payroll entries for June.",
            Priority = "High", Status = "In Progress",
            DueDate = "2025-07-07", AssignedBy = "Anil Thomas", Category = "Finance"
        },
        new TaskItem
        {
            TaskId = 106, EmployeeId = 5, EmployeeName = "Sneha Pillai",
            Title = "Social Media Campaign – Product Launch",
            Description = "Create and schedule posts across LinkedIn, Instagram, and Twitter for the new product launch.",
            Priority = "Medium", Status = "Pending",
            DueDate = "2025-07-20", AssignedBy = "Kavitha Nambiar", Category = "Marketing"
        },
        new TaskItem
        {
            TaskId = 107, EmployeeId = 7, EmployeeName = "Anita George",
            Title = "Vendor Contract Renewal – IT Equipment",
            Description = "Review and renew annual contracts with IT hardware vendors before expiry.",
            Priority = "Medium", Status = "Pending",
            DueDate = "2025-07-25", AssignedBy = "Binu Varghese", Category = "Operations"
        },
        new TaskItem
        {
            TaskId = 108, EmployeeId = 8, EmployeeName = "Vivek Sharma",
            Title = "CI/CD Pipeline Migration to GitHub Actions",
            Description = "Migrate existing Jenkins pipelines to GitHub Actions for all microservices.",
            Priority = "High", Status = "On Hold",
            DueDate = "2025-08-01", AssignedBy = "Priya Menon", Category = "DevOps"
        },
        new TaskItem
        {
            TaskId = 109, EmployeeId = 9, EmployeeName = "Lakshmi Devi",
            Title = "Performance Appraisal Cycle – H1 2025",
            Description = "Initiate and track the H1 2025 performance appraisal for all departments.",
            Priority = "High", Status = "In Progress",
            DueDate = "2025-07-31", AssignedBy = "Sunita Rao", Category = "HR"
        },
        new TaskItem
        {
            TaskId = 110, EmployeeId = 10, EmployeeName = "Arun Chandran",
            Title = "GST Filing – Q1 FY2026",
            Description = "Prepare and submit GST returns for the first quarter of FY2026.",
            Priority = "High", Status = "Completed",
            DueDate = "2025-07-20", AssignedBy = "Anil Thomas", Category = "Finance"
        }
    };
}
