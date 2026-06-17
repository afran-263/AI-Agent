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
