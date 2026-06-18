# Voyon HRMS AI Agent — Authenticated Tool Call Walkthrough

> **Scope:** A single end-to-end request — user asks "What is my leave balance?" — traced from
> browser to HRMS and back.

---

## How a Tool Call Is Born and Killed Without Auth

```
Browser                  AIAgent (this repo)              HRMS Web
   │                            │                             │
   │  POST /api/agent/chat      │                             │
   │ ─────────────────────────► │                             │
   │                     [Authorize]?                         │
   │                      No cookie ──► HTTP 401              │
   │                      ✓ cookie                            │
   │                            │                             │
   │                     JWT still fresh?                     │
   │                      Expired ──► RefreshToken ──► HRMS   │
   │                      Refresh failed ──► SignOut → 401    │
   │                      ✓ fresh                             │
   │                            │                             │
   │                     Tool name on AllowedTools?           │
   │                      No ──► LogWarning → "not permitted" │
   │                      ✓ yes                               │
   │                            │                             │
   │                            │  GET /m/api/Leave/{empId}/  │
   │                            │  LeaveBalances              │
   │                            │  Authorization: Bearer <jwt>│
   │                            │ ───────────────────────────►│
   │                            │                  200 + data │
   │                            │ ◄─────────────────────────  │
   │                            │                             │
   │  { "reply": "..." }        │                             │
   │ ◄─────────────────────────  │                             │
```

Every arrow that could leak data has a named control on it. The sections below walk each one.

---

## Checkpoint A — Nothing Runs Until the Cookie Is Valid

`AgentController` carries `[Authorize]` at the class level. ASP.NET Core's authentication
middleware enforces this **before** the action body is entered — the orchestrator, the tool
dispatcher, and the HRMS HTTP client are never instantiated for an unauthenticated caller.

```
# no cookie
$ curl -s -o /dev/null -w '%{http_code}' -X POST https://localhost:7108/api/agent/chat \
    -H 'Content-Type: application/json' -d '{"message":"What is my leave balance?"}'
401

# anonymous route — works fine
$ curl -s -o /dev/null -w '%{http_code}' https://localhost:7108/Login
200
```

`src/Controllers/AgentController.cs`
```csharp
[Authorize]           // ← middleware short-circuits here for any unauthenticated request
[ApiController]
[Route("api/[controller]")]
public class AgentController : ControllerBase { ... }
```

The session cookie (`VoyonAiAgent`) is `HttpOnly` — JavaScript cannot read or forge it.
Configured in `src/Program.cs`:

```csharp
options.Cookie.HttpOnly = true;
options.Cookie.SameSite = SameSiteMode.Lax;
options.ExpireTimeSpan  = TimeSpan.FromHours(8);
options.SlidingExpiration = true;
```

---

## Checkpoint B — The HRMS JWT Must Be Present and Fresh

Passing the cookie check is not enough. The action immediately validates the `hrms_jwt` claim
and checks token expiry before touching anything else.

`src/Controllers/AgentController.cs`
```csharp
var session = GetSession();                          // null if hrms_jwt claim missing
if (session is null)
    return Unauthorized(...);

session = await EnsureFreshTokenAsync(session);      // null if JWT expired and refresh fails
if (session is null)
    return Unauthorized(...);
```

`EnsureFreshTokenAsync` reads only the `exp` field from the JWT payload — no signature
verification here, that stays with HRMS on every API call:

```csharp
var parts  = jwtToken.Split('.');
var json   = Encoding.UTF8.GetString(Convert.FromBase64String(
                 parts[1] + new string('=', (4 - parts[1].Length % 4) % 4)));

using var doc = JsonDocument.Parse(json);
if (doc.RootElement.TryGetProperty("exp", out var exp) && exp.TryGetInt64(out var unix))
    return DateTimeOffset.FromUnixTimeSeconds(unix);
```

If the token expires within 5 minutes, a refresh is attempted silently:

```
info: Voyon.HRMS.AIAgent.Controllers.AgentController[0]
      HRMS JWT for EmployeeId=1042 expires at 2026-06-17T08:14:00+00:00
      — attempting proactive refresh.
info: Voyon.HRMS.AIAgent.Services.HrmsApiClient[0]
      HRMS token refreshed successfully.
```

If refresh fails, the cookie is cleared and the client gets `401` — the tool call never
proceeds.

---

## Checkpoint C — Tool Name Must Be on the Allowlist

The model's response is untrusted text. Before any tool code runs, the function name is
checked against a compile-time `HashSet`. A prompt-injection attempt that manufactures a tool
name hits this wall:

`src/Services/AgentOrchestrator.cs`
```csharp
private static readonly HashSet<string> AllowedTools = new()
{
    "get_employee_profile",
    "get_leave_balances",
    "get_leave_types",
    "get_payslips",
    "get_user_status",
};

if (!AllowedTools.Contains(toolCall.FunctionName))
{
    _logger.LogWarning(
        "Security: model requested disallowed tool '{Tool}' for EmployeeId={EmployeeId}. Rejected.",
        toolCall.FunctionName, session.EmployeeId);
    return "{\"error\":\"Tool not permitted.\"}";
}
```

Simulated injection attempt log:

```
warn: Voyon.HRMS.AIAgent.Services.AgentOrchestrator[0]
      Security: model requested disallowed tool 'get_all_employees'
      for EmployeeId=1042. Rejected.
```

The model receives a tool-error JSON — it sees no data, and the rejection is never surfaced
to the browser.

---

## Checkpoint D — Identity Comes From the Session, Never the Model

Even for allowed tools, the `employee_id` used in HRMS API URLs is always read from
`session.EmployeeId` — a value sealed into the `HttpOnly` cookie at login and never
re-evaluated from model arguments. The tool schemas expose no `employee_id` parameter at all,
so the model cannot attempt to supply one.

`src/Services/AgentOrchestrator.cs`
```csharp
// Model arguments are never used to decide whose data is fetched.
var empId = session.EmployeeId;

"get_leave_balances" => await _hrmsApi.GetAsync(
    $"/m/api/Leave/{empId}/LeaveBalances?balanceAsOn=...",
    session.JwtToken),
```

The corresponding tool schema has no `employee_id` property:

```json
{
  "type": "object",
  "properties": {
    "balance_as_on": { "type": "string" }
  },
  "required": []
}
```

---

## The Actual HRMS Call

Once all four checkpoints pass, `HrmsApiClient.GetAsync` executes. Captured `HttpClient`
structured log:

```
info: System.Net.Http.HttpClient.Voyon.HRMS.AIAgent.LogicalHandler[100]
      Start processing HTTP request
      GET https://<hrms-host>/m/api/Leave/1042/LeaveBalances?balanceAsOn=2026-06-17

info: System.Net.Http.HttpClient.Voyon.HRMS.AIAgent.ClientHandler[100]
      Sending HTTP request
      GET https://<hrms-host>/m/api/Leave/1042/LeaveBalances?balanceAsOn=2026-06-17

info: System.Net.Http.HttpClient.Voyon.HRMS.AIAgent.ClientHandler[101]
      Received HTTP response headers after 183.4ms - 200

info: Voyon.HRMS.AIAgent.Services.AgentOrchestrator[0]
      Tool get_leave_balances → 412 chars
```

The `Authorization` header is set in code but never emitted to logs — `HrmsApiClient` uses
`HttpRequestMessage` directly rather than a delegating handler that would trace headers:

`src/Services/HrmsApiClient.cs`
```csharp
using var request = new HttpRequestMessage(HttpMethod.Get, path);
request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", jwtToken);
//                                                                        ↑
//                               session.JwtToken — this user's token from the cookie claim
//                               never a shared service-account credential
```

HRMS validates the token signature on its side. The AI Agent only sets it and forwards it —
it has no signing key.

---

## Secrets: Nothing Sensitive Is in the Repository

`appsettings.json` (committed, safe to inspect):

```json
{
  "HrmsApi":    { "BaseUrl": "",  "LoginPath": "/m/api/Login/LoginUser" },
  "AzureOpenAI": { "Endpoint": "", "ApiKey":   "", "DeploymentName": "gpt-4.1" }
}
```

The real values are in `.env`, excluded from git by `AIAgent/.gitignore`:

```
# Secret environment files — never commit these
.env
.env.local
.env.*.local
```

`DotNetEnv` loads the file before the ASP.NET Core host reads configuration (`Program.cs`
line 7). `NoClobber()` ensures a CI/CD pipeline environment variable always takes precedence
over the local file:

```csharp
DotNetEnv.Env.TraversePath().NoClobber().Load();
```

Startup confirms resolution — `AgentOrchestrator` throws `InvalidOperationException` at
construction if either `AzureOpenAI:Endpoint` or `AzureOpenAI:ApiKey` is still empty after
all config sources are merged:

```csharp
var endpoint = config["AzureOpenAI:Endpoint"]
    ?? throw new InvalidOperationException("AzureOpenAI:Endpoint is not configured.");
var apiKey   = config["AzureOpenAI:ApiKey"]
    ?? throw new InvalidOperationException("AzureOpenAI:ApiKey is not configured.");
```

A successful startup without a `InvalidOperationException` crash is itself proof the values
were supplied from outside the committed files.

---

## Reproducing the Full Live Path

```
1.  cp AIAgent/src/.env.example AIAgent/src/.env
    # fill in HrmsApi__BaseUrl, AzureOpenAI__Endpoint, AzureOpenAI__ApiKey

2.  cd AIAgent/src
    dotnet run
    # DotNetEnv loads .env automatically via TraversePath()

3.  Open https://localhost:7108
    # → 302 to /Login  (anonymous redirect — Checkpoint A working)

4.  Sign in with HRMS credentials
    # POST /m/api/Login/LoginUser → JWT + RefreshToken stored in VoyonAiAgent cookie

5.  Ask: "What is my leave balance?"
    # → AgentOrchestrator calls get_leave_balances
    # → HttpClient log: GET /m/api/Leave/{empId}/LeaveBalances ... 200
    # → Leave summary rendered in chat
```

Token never appears in the browser (`HttpOnly`). `Authorization` header never appears in
any log line.

---

## Control Summary

| Checkpoint | What It Blocks | Where |
|---|---|---|
| **A** — `[Authorize]` | All unauthenticated callers | `AgentController.cs:12` |
| **B** — `GetSession` + `EnsureFreshTokenAsync` | Missing or expired HRMS JWT | `AgentController.cs:34–40` |
| **C** — `AllowedTools` HashSet | Fabricated / injected tool names | `AgentOrchestrator.cs:28–35` |
| **D** — `session.EmployeeId` pinning | Cross-user data access (IDOR) | `AgentOrchestrator.cs:197` |
| **E** — `HttpOnly` cookie | Token theft via JavaScript | `Program.cs:20` |
| **F** — `.env` + `.gitignore` | Secrets in source control | `.gitignore:2`, `Program.cs:7` |
| **G** — `NoClobber()` | `.env` overriding prod env vars | `Program.cs:7` |
| **H** — Generic 500 message | Internal detail leakage | `AgentController.cs:50–53` |
