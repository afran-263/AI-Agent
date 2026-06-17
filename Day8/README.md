## Table of Contents

1. [JWT & API Token Usage](#1-jwt--api-token-usage)
2. [Environment Variables](#2-environment-variables)
3. [Secret Management](#3-secret-management)
4. [Least Privilege](#4-least-privilege)
5. [Tool-Level Authorization](#5-tool-level-authorization)

---

## 1. JWT & API Token Usage

### What is a JWT?

A JSON Web Token (JWT) is a **digital passport**. When a user logs in, the server creates a small, self-contained package of information about that user — who they are, what role they hold, and when the token expires — and hands it back to them. Every subsequent request the user makes carries this token, so the server can instantly verify the identity without hitting a database every single time.

### How is it Structured?

A JWT has three parts, separated by dots:

```
HEADER.PAYLOAD.SIGNATURE
```

| Part | What it contains |
|------|-----------------|
| **Header** | The algorithm used to sign the token (e.g. HS256) |
| **Payload** | The actual data — user ID, role, expiry time |
| **Signature** | A cryptographic seal that detects any tampering |

If anyone modifies even a single character of the token, the signature becomes invalid and the server rejects it entirely.

### Standard Claims Inside the Payload

The payload carries standardized fields called **claims** — a common language that any compliant server can understand:

| Claim | Meaning |
|-------|---------|
| `sub` | Who the token belongs to (user ID) |
| `iss` | Who issued it (e.g. `myapp.com`) |
| `aud` | Who should accept it (e.g. `api.myapp.com`) |
| `exp` | When it expires (Unix timestamp) |
| `jti` | A unique ID used for revocation |

### How Authentication Works End-to-End

Think of it like **checking into a hotel**:

1. You show your ID at the front desk → **Login with email & password**
2. They hand you a key card valid for 15 minutes → **Short-lived access token**
3. They lock a master key in a safe you carry → **Refresh token in an httpOnly cookie**
4. Your key card opens doors without calling the front desk each time → **Stateless API requests**
5. When your key card expires, you use the master key to get a new one → **Silent token refresh**
6. On checkout, the master key is cancelled → **Logout + token blocklist**

```
Client → POST /auth/login { email, password }
Server → Returns: Access Token (15 min) + Refresh Token (7 days, httpOnly cookie)

Client → GET /api/profile  [Authorization: Bearer <access_token>]
Server → Verifies signature, checks expiry, returns data

Client → Access token expires → POST /auth/refresh (cookie sent automatically)
Server → Issues new access token
```

### Why Short-Lived Access Tokens?

Because if a token is stolen, the attacker's window to misuse it is tiny. The refresh token — stored in an `httpOnly` cookie that JavaScript cannot read — is the long-lived credential kept safe from browser-based attacks like XSS.

### Token Storage Rules

| Location | Safe? | Why |
|----------|-------|-----|
| `httpOnly` cookie | ✅ Yes | JavaScript cannot access it |
| In-memory (app state) | ✅ Yes | Cleared on page refresh |
| `localStorage` | ❌ No | Readable by any JavaScript — XSS risk |
| `sessionStorage` | ❌ No | Same XSS risk as localStorage |

### Best Practices

- Keep access tokens short-lived (15 minutes is a good default)
- Store refresh tokens in `httpOnly`, `Secure`, `SameSite=Strict` cookies
- Always verify the signature server-side — never trust the payload blindly
- Explicitly whitelist signing algorithms — never allow `alg: none`
- Use HTTPS everywhere — a token transmitted in plaintext is a credential in plaintext
- Maintain a revocation blocklist (e.g. Redis) for logout and compromised tokens

---

## 2. Environment Variables

### What Problem Do They Solve?

Hardcoding sensitive values — passwords, API keys, connection strings — directly into source code means those secrets enter your **Git history forever**. Anyone who ever accesses your repository can see them, now or in the future.

Environment variables move those values **outside the code entirely**. The code simply asks the environment for the value at runtime, without knowing or caring where it came from.

```csharp
// ❌ Secret lives in your Git history forever
var connectionString = "Server=prod.db.com;Password=Sup3rS3cr3t!";

// ✅ Secret lives only in the runtime environment
var connectionString = Environment.GetEnvironmentVariable("DATABASE_URL");
```

### The .env Workflow

The standard pattern involves three files working together:

**`.env`** — your real secrets, lives only on your machine or server, **never committed**
```
DATABASE_URL=postgres://user:pass@localhost:5432/mydb
JWT_SECRET=supersecretkey
API_KEY=sk-abc123
```

**`.env.example`** — a template with placeholder values, **safe to commit**
```
DATABASE_URL=postgres://user:pass@localhost:5432/dbname
JWT_SECRET=your_jwt_signing_secret
API_KEY=your_api_key_here
```

**`.gitignore`** — ensures the real `.env` can never accidentally be committed
```
.env
.env.local
.env.production
*.pem
*.key
```

At startup, your application loads `.env` and then validates that every required variable is present. This **fail-fast** approach means a missing secret crashes the app immediately with a clear error rather than causing a mysterious failure deep inside a running system.

### Per-Environment Configuration

The same codebase behaves differently in development, staging, and production simply by having different variable values — no code changes needed:

| Variable | Development | Staging | Production |
|----------|-------------|---------|------------|
| `DB_HOST` | `localhost` | `staging-db.internal` | `prod-db.internal` |
| `LOG_LEVEL` | `verbose` | `info` | `error` |
| `STRIPE_MODE` | `test` | `test` | `live` |

### Best Practices

- Add `.env` to `.gitignore` **before your very first commit** — once a secret is in Git history, it is very difficult to fully erase
- Keep `.env.example` up to date so new team members know exactly what variables they need
- Use separate secrets per environment — never reuse a production key in development
- Never log environment variables, even partially — a log file is often less protected than a secrets store
- In CI/CD pipelines, use the platform's built-in secrets store (e.g. GitHub Actions Secrets) instead of `.env` files

---

## 3. Secret Management

### Why Isn't .env Enough for Production?

A `.env` file is a flat text file. It has no access controls, no audit trail, no automatic rotation, and no way to grant different services access to different secrets. In a production system with many services, many developers, and regulatory requirements, you need a dedicated **secrets manager**.

### The Secret Lifecycle

Every secret goes through six stages. Managing them deliberately at each stage is what separates a secure system from a vulnerable one:

```
Create → Distribute → Use → Rotate → Audit → Revoke
```

**Create** — Secrets must be generated with cryptographic randomness, never typed by hand. They should be tagged with metadata: who owns them, what they're for, and when they expire.

**Distribute** — Services should **pull** secrets from a vault at runtime using their own identity, rather than having secrets pushed to them at deployment time. This means secrets are never baked into Docker images or CI pipelines.

**Use** — Secrets should exist only in memory while being used. They should never appear in logs, error messages, or API responses — not even a prefix or a partial value.

**Rotate** — Secrets should be changed regularly, and the rotation should happen with zero downtime. The strategy is a brief overlap window where both the old and new secret are valid, giving all running services time to pick up the new value before the old one is invalidated.

**Audit** — Every access to a secret should be logged: who accessed it, from where, and when. Anomalous patterns — unusual hours, unknown IP addresses, unexpected services — should trigger alerts.

**Revoke** — When an employee leaves, a service is decommissioned, or a breach is suspected, the secret is immediately invalidated. Audit logs help identify every system that was using it so those systems can be updated.

### Secrets Management Tools

| Tool | Best For | Complexity |
|------|----------|------------|
| HashiCorp Vault | Self-hosted, enterprise environments | High |
| AWS Secrets Manager | AWS-native workloads | Medium |
| Azure Key Vault | Azure-native workloads | Medium |
| GCP Secret Manager | GCP-native workloads | Medium |
| GitHub Actions Secrets | CI/CD pipelines | Low |
| Doppler | Developer teams, multi-environment | Low |

### Dynamic Secrets (Advanced)

The most secure approach eliminates permanent credentials entirely. Instead of a fixed database password, a service requests temporary credentials from a vault, which creates a brand-new database user specifically for that request — valid for one hour, then automatically deleted.

```
Service  →  Vault:    "I need database credentials"
Vault    →  Database: Creates temporary user, valid for 1 hour
Vault    →  Service:  Here are your credentials
(1 hour later)
Vault    →  Database: Deletes the temporary user
```

Even if those credentials are intercepted, they expire within the hour. There is no permanent password to steal.

### Best Practices

- Never store secrets in source code, config files, or Docker images
- Automate secret rotation — manual rotation gets skipped under deadline pressure
- Use separate secrets for each environment
- Prefer short-lived, dynamic credentials over long-lived static ones
- Regularly scan your codebase with tools like `truffleHog` or `gitleaks` to catch accidentally committed secrets

---

## 4. Least Privilege

### The Core Principle

Every user, service, process, and API token should have the **minimum permissions required to do exactly its job** — nothing more. This limits the **blast radius** of any compromise.

> If an attacker compromises a read-only analytics service, they can read data. They cannot delete records, drop tables, or move to other systems. Least privilege turns a potential catastrophe into a contained incident.

### In Practice: Database Permissions

Instead of one all-powerful database user, you create separate users for separate responsibilities:

```sql
-- Analytics service: can only read
GRANT SELECT ON app_db.* TO 'analytics_service';

-- Order service: can only write to its own table
GRANT INSERT, UPDATE ON app_db.orders TO 'order_service';

-- Auth service: can only touch the users table
GRANT SELECT, INSERT ON app_db.users TO 'auth_service';

-- Migration tool: full access, used only when running migrations
GRANT ALL ON app_db.* TO 'migrator';
```

### In Practice: API Token Scopes

Fine-grained tokens mean a compromised CI/CD token cannot delete repositories, and a compromised read token cannot push code:

```
GITHUB_CI_TOKEN      → read repository only
GITHUB_DEPLOY_TOKEN  → write packages only
GITHUB_AUDIT_TOKEN   → read audit logs only
```

### Two Models for Access Control

**Role-Based Access Control (RBAC)** is the simpler approach. You define roles (viewer, editor, admin), assign permissions to each role, and give users a role. It is easy to understand, audit, and explain to non-technical stakeholders. Most applications should start here.

**Attribute-Based Access Control (ABAC)** is more powerful. Access decisions are made in real time based on the combination of who the user is, what resource they are accessing, and the context of the situation. For example: a manager can approve an expense only if the amount is within their personal limit *and* the current time is within business hours. ABAC handles complex, context-sensitive rules that RBAC cannot express.

```csharp
// RBAC: simple role check
if (user.Role == "admin") { /* allow */ }

// ABAC: contextual check combining multiple factors
bool canApprove = user.Role == "manager"
    && expense.Amount <= user.ApprovalLimit
    && DateTime.Now.Hour >= 9 && DateTime.Now.Hour < 17;
```

### Privilege Review Checklist

Permissions tend to accumulate over time — people change roles, projects end, but access rights linger. Regular review prevents this drift:

- **Quarterly access reviews** — audit and remove permissions no longer needed
- **Immediate offboarding** — revoke all credentials the moment someone leaves
- **No shared credentials** — every service and every person gets their own identity
- **Separation of duties** — no single account can both request and approve a sensitive change
- **Just-in-time access** — prefer granting elevated access temporarily when needed, rather than permanently

---

## 5. Tool-Level Authorization

### Why This Matters Especially for AI and Automation

When a human uses an API key, they make deliberate, conscious choices. When an automated agent uses the same key, it can take hundreds of actions per second based on instructions it receives — and those instructions could potentially be manipulated by malicious content it processes (known as **prompt injection**). A single compromised instruction with a full-access key could cause irreversible damage.

### The Confused Deputy Problem

The "deputy" (an agent or automation script) has authority delegated to it by you, but a third party tricks the deputy into using that authority in ways you never intended.

```
Without scoped keys:
You → Agent (full API key) → Deletes all records   ← catastrophic

With scoped keys:
You → Agent (read-only key) → Tries to delete → 403 Forbidden ✅
```

### Scoped Keys Per Tool

Instead of one key that does everything, each tool gets its own narrowly-scoped key:

```
EMAIL_TOOL_KEY     → can send emails only, cannot read inbox
CALENDAR_TOOL_KEY  → can read events only, cannot create or delete
DOCS_TOOL_KEY      → can read specific folders only
ANALYTICS_TOOL_KEY → can read reports only, no raw data access
```

Even if one tool is compromised, the attacker gains only that narrow capability.

### Tool Manifests

A tool manifest is a formal declaration of what each tool is permitted to do. Before any request is executed, the system checks it against the manifest. If the tool attempts something not listed — even if it has valid credentials — the request is denied.

```yaml
tools:
  - name: send_email
    allowed_actions: [send]
    constraints:
      allowed_domains: ["@mycompany.com"]
      max_recipients: 1
      rate_limit: 10/hour

  - name: search_docs
    allowed_actions: [read, search]
    constraints:
      folders: ["/docs/public", "/docs/internal"]
      excludes: ["/docs/confidential"]
```

### Authorization Decision Flow

Every incoming tool request passes through a series of gates before being allowed:

```
Request received
    ↓
Is this tool registered in the manifest?   → No  → 403 Denied
    ↓ Yes
Is this action in the allowed list?        → No  → 403 Denied
    ↓ Yes
Do all constraints pass?                   → No  → 403 Denied
    ↓ Yes
Is the rate limit not exceeded?            → No  → 429 Too Many Requests
    ↓ Yes
Is this a destructive/elevated action?     → Yes → Require fresh user confirmation
    ↓ No
Allow → Log → Audit Trail
```

### Rate Limiting Per Tool

Rate limits contain damage from bugs or runaway loops. An email tool limited to 10 emails per hour cannot be exploited to spam thousands of contacts, even if something goes wrong:

```
Email tool:    max 10 requests / hour
Search tool:   max 30 requests / minute
Delete tool:   max 5 requests / hour  +  requires re-authorization
```

### Re-Authorization for Destructive Actions

Irreversible actions — deleting records, sending bulk messages, transferring funds — should always require **fresh confirmation from the user**, even if the tool already holds a valid key. This keeps a human in the loop for anything that cannot be undone:

```csharp
// Before deleting, always ask the user to confirm explicitly
var confirmed = await RequestUserConfirmation(userId, action: "delete", resource: recordId);
if (!confirmed) throw new ForbiddenException("User did not confirm elevated action");

// Only then proceed
await db.Records.DeleteAsync(recordId);
await auditLog.WriteAsync(/* ... */);
```

### Best Practices

- One scoped key per tool — never share credentials between tools
- Declare every tool's capabilities in a manifest; reject anything not declared
- Request the narrowest OAuth scopes that the tool actually needs
- Apply per-tool rate limits to contain runaway loops or malicious exploitation
- Log every tool call with enough context to reconstruct exactly what happened
- Require re-authorization for any destructive or sensitive operation
- Periodically review tool authorizations and revoke those no longer in use

---

## Summary

These five topics build on each other as layers of a defence-in-depth strategy:

| Layer | What it protects |
|-------|-----------------|
| **JWT & Tokens** | Proves who is making a request, limits the window of stolen credential misuse |
| **Environment Variables** | Keeps secrets out of source code and version history |
| **Secret Management** | Centralizes, rotates, and audits secrets across all services |
| **Least Privilege** | Limits what any one identity can do if compromised |
| **Tool-Level Authorization** | Constrains automated agents to only their declared capabilities |

> Apply these principles from day one — retrofitting security into an existing system is always harder, riskier, and more expensive than building it in from the start.
