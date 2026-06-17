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

