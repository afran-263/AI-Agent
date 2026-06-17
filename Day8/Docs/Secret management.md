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
