# Security Report — Smart Expense Management Portal

**Role:** Security Agent  
**Date:** 2026-11-07  
**Scope:** Application code, templates, configuration, dependency declarations, and the Docker image definition.  
**Method:** Static review against the OWASP Top 10 (2021) and the project rules. No application code was changed. No penetration test was run.

## 1. Security Review Summary

The portal is a small local expense ledger. It has no accounts, and anyone who can reach the process can read every expense and add new ones. That matches the current product decision, and it is the main risk if the process is reachable beyond the local machine. The Docker command listens on all interfaces, so publishing the container port makes the ledger network-reachable.

Input handling is in good shape for this size of application. Create and filter values are checked before use. Expense text is stored through SQLAlchemy bound parameters. Jinja renders titles with HTML escaping, and unexpected failures return a generic message while the detail stays in the server log. The HTML form uses an HttpOnly, SameSite=Lax CSRF cookie.

The review did not find a SQL injection or a reflected or stored cross-site scripting path in the application templates. The remaining work is to keep the app local until authentication exists, then add transport security, response headers, a non-root image, and pinned dependencies.

| Severity | Count | Theme |
| --- | --- | --- |
| High | 1 | Unauthenticated read and write, including when the container is published |
| Medium | 3 | Cleartext exposure, missing browser protections, container and dependency hardening |
| Low | 4 | Unsigned CSRF cookie, public API docs, plaintext database file, `.env` not ignored |
| Informational | 1 | No audit record of expense creation |

## 2. OWASP Risks

| OWASP 2021 | Risk in this project | Result |
| --- | --- | --- |
| A01 Broken Access Control | Pages and `/api/expenses` grant the same access to every caller. There is no owner, role, or session. | Open. Accepted for a local demo. High if the port is reachable by anyone else. |
| A02 Cryptographic Failures | SQLite is plaintext. The app does not terminate TLS. The CSRF cookie is not marked `Secure`. | Open when the app is used off the local machine. |
| A03 Injection | Queries are parameterized. Category filters are allow-listed. Templates escape rendered values. | Mitigated in the reviewed code. |
| A04 Insecure Design | One shared ledger and no login are explicit product choices. There is no limit on how many expenses a caller can add. | Accepted for the local release. Write volume is unbounded. |
| A05 Security Misconfiguration | Interactive API docs are enabled. Security headers are not set. The image runs as root and installs test packages. | Open. |
| A06 Vulnerable and Outdated Components | `requirements.txt` uses minimum versions, not pinned versions. Bootstrap is loaded from a CDN without an integrity check. | Open. |
| A07 Identification and Authentication Failures | No authentication exists. The JSON API does not require a token. | Open. Same exposure as A01. |
| A08 Software and Data Integrity Failures | CDN scripts are not pinned with Subresource Integrity. The CSRF value is a random token, not a signed token. | Open, with a smaller practical impact while SameSite=Lax holds. |
| A09 Security Logging and Monitoring Failures | Unexpected errors are logged on the server and hidden from the caller. Creates are not recorded in an audit log. | Partially met. |
| A10 Server-Side Request Forgery | The application does not fetch a URL supplied by the caller. | Not applicable. |

## 3. Severity Levels

### High

**H-1. Anyone who can reach the app can read and add expenses.**  
`GET /expenses`, `GET /dashboard`, `GET /api/expenses`, `GET /api/dashboard`, and both create endpoints have no authentication. `Dockerfile` starts Uvicorn with `--host 0.0.0.0`. A published container port exposes the full ledger on the network. This is an accepted local-demo decision, and it becomes a broken-access-control issue as soon as the service leaves the developer machine.

### Medium

**M-1. Traffic and the CSRF cookie are not protected in transit.**  
The application serves HTTP only. `_apply_csrf` sets `HttpOnly` and `SameSite=Lax` and does not set `Secure`. On a shared or remote network, a listener can read expense titles and amounts.

**M-2. Browser defenses and the CDN script are incomplete.**  
Responses do not set `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, or a frame policy. `base.html` loads Bootstrap CSS and JavaScript from `cdn.jsdelivr.net` without Subresource Integrity. A compromise of that CDN asset can run script in the portal origin.

**M-3. The image and dependency set are broader than the runtime needs.**  
The container runs as root. `requirements.txt` is installed in the image and includes `pytest` and `httpx`. Version floors such as `fastapi>=0.115` allow a future install to pick up a different release. That weakens repeatable builds and leaves more packages in the runtime image than the app uses.

### Low

**L-1. The CSRF token is an unsigned double-submit cookie.**  
The form token must match the cookie, and comparison uses `secrets.compare_digest`. The server does not sign the token. `SameSite=Lax` already withholds the cookie on a cross-site form post, so a remote site cannot complete a forged browser post in current browsers. The gap matters if a caller can plant the cookie, for example from a sibling subdomain.

**L-2. API documentation is public.**  
FastAPI exposes `/docs`, `/redoc`, and `/openapi.json` by default. They describe every route. They do not grant access beyond the routes themselves.

**L-3. The SQLite file is readable by anyone with access to the data directory.**  
`DATABASE_PATH` points at a normal file. Nothing encrypts it or restricts its permissions in application code. A copied volume or a local file read reveals every stored expense.

**L-4. `.gitignore` does not ignore `.env`.**  
No `.env` file is in the project, and the app reads `DATABASE_PATH` from the process environment. A later `.env` could still be committed because the ignore rules do not name it.

### Informational

**I-1. Expense creation is not written to an audit log.**  
Failed JSON bodies are logged without the payload. Unhandled exceptions are logged with `logger.exception`, and the client receives only "Something went wrong. Try again." Successful creates leave a database row and an access log line, not a security audit event.

## 4. Recommended Improvements

These are recommendations only. This review does not change the application.

1. Keep the current build on localhost. Before any shared or remote deployment, require authentication and bind the process to a trusted interface. Do not publish the container port until that control exists.
2. Terminate TLS in front of the container for any non-local deployment, and set the CSRF cookie `Secure` when the site is served over HTTPS.
3. Add a content security policy that limits scripts to known sources, plus `X-Content-Type-Options: nosniff` and a frame restriction. Prefer a local copy of Bootstrap, or add Subresource Integrity and a fallback if the CDN stays.
4. Run the container as a non-root user. Split runtime dependencies from test dependencies, and pin every installed version.
5. Add a modest request-size and write-rate limit on expense creation so one client cannot grow the SQLite file without bound.
6. Sign the CSRF token with a server-side secret if the app is ever hosted on a shared parent domain.
7. Disable `/docs`, `/redoc`, and `/openapi.json` outside local development.
8. Restrict permissions on the SQLite file and its directory. Add `.env` to `.gitignore` before any environment file is introduced.
9. Add an audit log for successful creates that records the time and category, not the full title, if the ledger later holds real employee spending.

## 5. Secure Coding Observations

These controls are present in the reviewed code and should stay in place.

- Create rules for title, amount, category, and date live in one module and are used by both the form and the JSON API. Unknown JSON fields are rejected. Amounts are parsed as decimals, limited to two places, and stored as integer cents.
- Category filters that are not in Travel, Meals, Supplies, Utilities, or Other are rejected before the query runs. The list is not returned for an invalid filter.
- Repository writes and reads use SQLAlchemy expressions. Expense titles are not concatenated into SQL. A repository test stores a title that contains quotes.
- Templates render expense fields with `{{ ... }}`. No `|safe` or equivalent unescaped output was found. Jinja autoescaping applies to the HTML templates.
- The HTML create form requires a matching CSRF cookie and form field. The cookie is `HttpOnly` and `SameSite=Lax`. The comparison rejects a length mismatch before `compare_digest`.
- Redirects go to fixed paths, `/dashboard` and `/expenses`. The host header is not used to build a redirect.
- Validation failures return field messages. Unhandled exceptions do not return a stack trace, SQL, a file path, or an environment value.
- The database path comes from `DATABASE_PATH` or a local default. The SQLite file is not copied into the image. `.gitignore` ignores `data/` and database files.
- The Docker build context excludes `.git`, tests, docs, and local database files.

**Residual acceptance:** lack of authentication is safe only while the process stays on the local machine. The Docker listen address does not enforce that boundary by itself.
