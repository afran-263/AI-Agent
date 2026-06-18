using System.Net.Http.Headers;
using System.Text.Json;
using HrmsAgentApi.Models;
using Microsoft.Extensions.Options;

namespace HrmsAgentApi.Services;

/// <summary>
/// Low-level HTTP client that calls Voyon Folks HRMS REST API.
/// Injects the pre-issued Bearer token on every request.
/// All methods return the raw API response deserialized — 
/// no local DB, no caching, no data invention.
/// </summary>
public class VoyonHrmsClient
{
    private readonly IHttpClientFactory _factory;
    private readonly VoyonHrmsOptions _opts;
    private readonly ILogger<VoyonHrmsClient> _logger;

    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public VoyonHrmsClient(
        IHttpClientFactory factory,
        IOptions<VoyonHrmsOptions> opts,
        ILogger<VoyonHrmsClient> logger)
    {
        _factory = factory;
        _opts = opts.Value;
        _logger = logger;
    }

    // ─── Team Attendance ──────────────────────────────────────────────────────
    // GET /m/api/Attendance/team-attendance
    //   ?employeeId=34110&date=2020-12-17 00:00:00.000&reportingType="1"

    public async Task<TeamAttendanceApiResponse> GetTeamAttendanceAsync(
        string date,
        string reportingType = "1",
        CancellationToken ct = default)
    {
        // Normalise date — accept "2024-06-10" or full datetime string
        var dateStr = date.Contains(' ') ? date : $"{date} 00:00:00.000";

        var url = $"/m/api/Attendance/team-attendance" +
                  $"?employeeId=34110" +
                  $"&date={Uri.EscapeDataString(dateStr)}" +
                  $"&reportingType={Uri.EscapeDataString($"\"{reportingType}\"")}";

        return await GetAsync<TeamAttendanceApiResponse>(url, ct)
            ?? new TeamAttendanceApiResponse(null, "EMPTY", "No data returned from Voyon.", null);
    }

    // ─── Absent employees for a date ──────────────────────────────────────────
    // Derived from team-attendance — filters isAbsent=true, isLeave=false

    public async Task<TeamAttendanceApiResponse> GetAbsentEmployeesAsync(
        string date,
        CancellationToken ct = default)
        => await GetTeamAttendanceAsync(date, ct: ct);

    // ─── Present employees for a date ─────────────────────────────────────────
    // Derived from team-attendance — filters checkinTime != null

    public async Task<TeamAttendanceApiResponse> GetPresentEmployeesAsync(
        string date,
        CancellationToken ct = default)
        => await GetTeamAttendanceAsync(date, ct: ct);

    // ─── Mark Attendance (Check-In / Check-Out) ───────────────────────────────
    // POST /m/api/Attendance/AttendanceLog

    public async Task<AttendanceLogApiResponse> PostAttendanceLogAsync(
        AttendanceCheckInCheckOutModel model,
        CancellationToken ct = default)
    {
        const string url = "/m/api/Attendance/AttendanceLog";
        return await PostAsync<AttendanceCheckInCheckOutModel, AttendanceLogApiResponse>(url, model, ct)
            ?? new AttendanceLogApiResponse(null, "EMPTY", "No response from Voyon.", null);
    }

    // ─── Private HTTP helpers ─────────────────────────────────────────────────

    private async Task<T?> GetAsync<T>(string url, CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(_opts.BearerToken))
            throw new InvalidOperationException(
                "VoyonHrms:BearerToken is not configured. " +
                "Run: dotnet user-secrets set \"VoyonHrms:BearerToken\" \"<token>\"");

        var client = _factory.CreateClient("VoyonFolks");
        client.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", _opts.BearerToken);

        _logger.LogInformation("Voyon API → GET {Url}", url);

        var response = await client.GetAsync(url, ct);

        var body = await response.Content.ReadAsStringAsync(ct);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError(
                "Voyon API error: {Status} | URL: {Url} | Body: {Body}",
                response.StatusCode, url, body);
            throw new HttpRequestException(
                $"Voyon Folks API returned {(int)response.StatusCode} {response.StatusCode}. " +
                $"Details: {body}");
        }

        _logger.LogDebug("Voyon API ← {Status} | {Url}", response.StatusCode, url);

        return JsonSerializer.Deserialize<T>(body, JsonOpts);
    }

    private async Task<TResponse?> PostAsync<TRequest, TResponse>(
        string url, TRequest payload, CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(_opts.BearerToken))
            throw new InvalidOperationException(
                "VoyonHrms:BearerToken is not configured. " +
                "Run: dotnet user-secrets set \"VoyonHrms:BearerToken\" \"<token>\"");

        var client = _factory.CreateClient("VoyonFolks");
        client.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", _opts.BearerToken);

        var json    = JsonSerializer.Serialize(payload, JsonOpts);
        _logger.LogInformation(
            "AttendanceLog Payload: {Json}",
            json);
        var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

        _logger.LogInformation("Voyon API → POST {Url}", url);

        var response = await client.PostAsync(url, content, ct);
        var body     = await response.Content.ReadAsStringAsync(ct);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError(
                "Voyon API error: {Status} | URL: {Url} | Body: {Body}",
                response.StatusCode, url, body);
            throw new HttpRequestException(
                $"Voyon Folks API returned {(int)response.StatusCode} {response.StatusCode}. " +
                $"Details: {body}");
        }

        _logger.LogDebug("Voyon API ← {Status} | {Url}", response.StatusCode, url);
        return JsonSerializer.Deserialize<TResponse>(body, JsonOpts);
    }
}

/// <summary>Strongly-typed options for Voyon Folks API connection.</summary>
public class VoyonHrmsOptions
{
    public const string Section = "VoyonHrms";
    public string BaseUrl { get; set; } = "https://voyonfolks-qa.azurewebsites.net";

    /// <summary>
    /// Pre-issued Bearer token.
    /// Local dev: dotnet user-secrets set "VoyonHrms:BearerToken" "eyJ..."
    /// Production: Azure Key Vault secret "VOYON-BEARERTOKEN"
    /// </summary>
    public string BearerToken { get; set; } = string.Empty;

}
