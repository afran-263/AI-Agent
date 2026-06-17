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
