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
