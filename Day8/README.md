# Secrets Management

No secret is stored in the repository. `appsettings.json` holds only empty strings for
sensitive fields. Real values are loaded at startup from `src/.env` via
[DotNetEnv](https://github.com/tonerdo/dotnet-env):

```csharp
// Program.cs — fires before WebApplication.CreateBuilder
DotNetEnv.Env.TraversePath().NoClobber().Load();
```

`src/.env` is blocked from git by `AIAgent/.gitignore`:

```
.env
.env.local
.env.*.local
```

**Priority order** (highest wins):

```
OS / Azure App Service environment variable
  └─ src/.env                    (local dev)
       └─ appsettings.json       (empty defaults — safe to commit)
```

---

## Authentication Flow

Every chat request follows this path. A request that fails any checkpoint never
reaches the HRMS API.

```
POST /api/agent/chat
       │
       ├─[A] [Authorize] attribute ──────── no cookie → HTTP 401
       │
       ├─[B] GetSession()  ─────────────── hrms_jwt claim missing → HTTP 401
       │
       ├─[C] EnsureFreshTokenAsync() ────── JWT expires in < 5 min → RefreshToken call
       │                                    refresh failed → SignOut → HTTP 401
       │
       ├─[D] AllowedTools HashSet ──────── tool name not on list → reject + LogWarning
       │
       └─[E] session.EmployeeId pinned ──── model args never used for identity
```

### A — Cookie Authentication (`Program.cs`)

The portal uses a server-issued `HttpOnly` cookie. JavaScript cannot read, copy, or forge it.

```csharp
builder.Services.AddAuthentication("AiAgentCookie")
    .AddCookie("AiAgentCookie", options =>
    {
        options.Cookie.HttpOnly    = true;
        options.Cookie.SameSite    = SameSiteMode.Lax;
        options.SlidingExpiration  = true;
        options.ExpireTimeSpan     = TimeSpan.FromHours(8);
        options.LoginPath          = "/Login";
    });
```

### B — HRMS JWT Presence (`AgentController.cs`)

The HRMS JWT is stored as a claim inside the cookie at login. Its presence is verified
explicitly before the orchestrator is touched.

```csharp
var session = GetSession();                   // null if hrms_jwt claim absent
if (session is null) return Unauthorized(…);
```

### C — Token Freshness + Auto-Refresh (`AgentController.cs`)

Before every chat the JWT `exp` field is inspected. If the token will expire within
5 minutes, a silent refresh is attempted using the stored `refresh_token` claim.
On failure the cookie is cleared and the client receives `401`.

```csharp
session = await EnsureFreshTokenAsync(session);
if (session is null) return Unauthorized(…);
```

### D — Tool-Name Allowlist (`AgentOrchestrator.cs`)

The AI model's output is untrusted. Before any HRMS API call is made the tool name is
checked against a compile-time `HashSet`. Any name not on the list — including any
fabricated by a prompt-injection attempt — is rejected and security-logged.

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
    _logger.LogWarning("Security: disallowed tool '{Tool}' for EmployeeId={Id}. Rejected.",
        toolCall.FunctionName, session.EmployeeId);
    return "{\"error\":\"Tool not permitted.\"}";
}
```

### E — Identity Pinning (`AgentOrchestrator.cs`)

`employee_id` is absent from every tool schema. The model is never given an opportunity
to supply it. Every HRMS call uses `session.EmployeeId` — sealed into the server-side
cookie at login — so the model cannot request another user's data regardless of what
it outputs.

```csharp
var empId = session.EmployeeId;   // always from the authenticated session

"get_leave_balances" => await _hrmsApi.GetAsync(
    $"/m/api/Leave/{empId}/LeaveBalances?balanceAsOn=…",
    session.JwtToken),
```

---

## Per-User Bearer Token on Every HRMS Call

The HRMS JWT is never shared. Each outbound HTTP request carries the token belonging to
the signed-in user, set by `HrmsApiClient.GetAsync`:

```csharp
request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", jwtToken);
```

HRMS independently validates the token signature. The AI Agent has no signing key —
it only forwards the token that HRMS issued at login.

The `Authorization` header is never emitted to logs. `HrmsApiClient` uses
`HttpRequestMessage` directly; no delegating handler traces headers.

---

## CSRF Protection

Anti-forgery is enforced with a custom header name:

```csharp
builder.Services.AddAntiforgery(options => options.HeaderName = "X-CSRF-TOKEN");
```

---

## Error Handling

Internal exception details never reach the HTTP response. `ex.Message` is logged
server-side only; the client receives a generic message:

```csharp
catch (Exception ex)
{
    _logger.LogError(ex, "Unhandled error in Chat for EmployeeId={Id}", session.EmployeeId);
    return StatusCode(500, new ChatResponse
    {
        Error = "An unexpected error occurred. Please try again."
    });
}
```

---

## Security Control Reference

| Control | Blocks | File |
|---|---|---|
| `[Authorize]` on controller | Unauthenticated callers | `AgentController.cs:12` |
| `GetSession()` null-check | Missing HRMS JWT claim | `AgentController.cs:34` |
| `EnsureFreshTokenAsync()` | Expired JWT reaching HRMS | `AgentController.cs:38` |
| `AllowedTools` HashSet | Prompt-injected tool names | `AgentOrchestrator.cs:28` |
| `session.EmployeeId` pinning | Cross-user data access (IDOR) | `AgentOrchestrator.cs:197` |
| `HttpOnly` cookie | Token theft via JavaScript | `Program.cs:20` |
| `.env` + `.gitignore` | Secrets in source control | `.gitignore:2` |
| `NoClobber()` | `.env` overriding prod env vars | `Program.cs:7` |
| Generic 500 response | Internal detail leakage | `AgentController.cs:50` |

