# Security Section
 
This project follows security-first development practices.
All secrets are externalized and never hardcoded in source code.
 
## Secrets & Configuration
 
Sensitive values (JWT signing keys, database credentials, API keys) are stored
in **Azure Key Vault** and fetched at runtime using `DefaultAzureCredential`.
No secrets are committed to Git.
 
| Secret | Storage Location |
|--------|-----------------|
| JWT signing key | Azure Key Vault → `JwtSecret` |
| Database connection string | Azure Key Vault → `DatabaseUrl` |
| Azure credentials | Environment variables (local) / Managed Identity (production) |
 
## Local Development Setup
 
1. Copy the environment template:
```bash
   cp .env.example .env
```
 
2. Fill in your local values in `.env` (never commit this file).
 
3. Ensure you are logged into Azure:
```bash
   az login
```
 
4. Run the application — secrets are loaded from Azure Key Vault automatically:
```bash
   dotnet run
```
 
## Verifying No Secrets in Git
 
Before pushing, scan for accidentally committed secrets:
 
```bash
gitleaks detect --source . --verbose
```
 
The pre-commit hook also runs this automatically on every `git commit`.
 
## Authentication
 
API endpoints are protected with **JWT Bearer authentication**.
 
- Access tokens expire in **15 minutes**
- Tokens are signed with HS256 using a key stored in Azure Key Vault
- Algorithm `none` is explicitly blocked
- All token claims (issuer, audience, expiry) are validated on every request
 
To access a protected endpoint:
 
````
POST /auth/login       → returns access token
GET  /api/profile      → requires Authorization: Bearer <token>
````
 
## Security Checklist
 
- [x] No secrets in source code or `appsettings.json`
- [x] `.env` is in `.gitignore` and never committed
- [x] `.env.example` committed with placeholder values only
- [x] Secrets fetched from Azure Key Vault at runtime
- [x] JWT tokens are short-lived (15 min) and algorithm-whitelisted
- [x] All API endpoints require authentication by default
- [x] Role-based access control applied to sensitive endpoints
- [x] `gitleaks` pre-commit hook blocks accidental secret commits
- [x] Git history verified clean — no secrets in past commits
- [x] Separate secrets per environment (dev / staging / prod)
- [x] No secrets logged, even partially
````
