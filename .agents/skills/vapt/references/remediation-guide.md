# Step-by-Step Remediation Guide

Detailed, actionable remediation instructions for every common vulnerability class. Each fix includes exact commands, configuration snippets, and verification steps.

## Vulnerability Classification and Remediation Priority

| Severity | Response Time | Description |
|----------|---------------|-------------|
| **Critical** | 24-48 hours | Remote code execution, authentication bypass, data exposure |
| **High** | 1 week | Privilege escalation, significant data access |
| **Medium** | 2 weeks | Limited data exposure, DoS, info disclosure |
| **Low** | 1 month | Minor info leaks, non-exploitable findings |
| **Informational** | Next release | Best practice improvements |

---

## Network & Infrastructure Remediation

### 1. Open/Unnecessary Services

**Problem**: Unnecessary services exposed to network, increasing attack surface.

**Step-by-Step Fix**:

**Linux**:
```bash
# Step 1: List all listening services
ss -tlnp
netstat -tlnp

# Step 2: Disable unnecessary services
systemctl disable --now avahi-daemon
systemctl disable --now cups
systemctl disable --now rpcbind
systemctl disable --now nfs-server

# Step 3: Block at firewall
iptables -A INPUT -p tcp --dport 111 -j DROP  # rpcbind
iptables -A INPUT -p tcp --dport 5353 -j DROP  # mDNS
iptables-save > /etc/iptables/rules.v4

# Step 4: Verify
ss -tlnp  # Only expected services listening
nmap -sT target  # Only expected ports open
```

**Windows**:
```powershell
# Step 1: List listening ports
netstat -an | findstr LISTENING

# Step 2: Disable services via Group Policy
# Computer Config → Admin Templates → Network → Network Connections
# → "Prohibit installation and use of Internet Connection Sharing"

# Step 3: Windows Firewall rules
netsh advfirewall firewall add rule name="Block_Telnet" dir=in action=block protocol=TCP localport=23
netsh advfirewall firewall add rule name="Block_FTP" dir=in action=block protocol=TCP localport=21

# Step 4: Verify
netstat -an | findstr LISTENING
```

**Verification**: `nmap -sT target` shows only expected service ports.

---

### 2. Weak Password Policies

**Problem**: Passwords too short, no complexity, no lockout, no history.

**Step-by-Step Fix**:

**Windows Domain (GPO)**:
```powershell
# Step 1: Create Password Settings Object (PSO) for fine-grained policy
New-ADFineGrainedPasswordPolicy -Name "StrongPolicy" `
    -Precedence 10 `
    -MinPasswordLength 14 `
    -ComplexityEnabled $true `
    -PasswordHistoryLength 24 `
    -MaxPasswordAge 90.00:00:00 `
    -MinPasswordAge 1.00:00:00 `
    -LockoutThreshold 5 `
    -LockoutDuration 0:30:00 `
    -LockoutObservationWindow 0:15:00

# Step 2: Apply to group
Add-ADFineGrainedPasswordPolicySubject -Identity "StrongPolicy" -Subjects "Domain Users"

# Step 3: Verify
Get-ADFineGrainedPasswordPolicy -Identity "StrongPolicy"
Get-ADUserResultantPasswordPolicy -Identity testuser
```

**Linux (PAM)**:
```bash
# Step 1: Install pwquality
apt install libpam-pwquality  # Debian/Ubuntu

# Step 2: Configure /etc/security/pwquality.conf
minlen = 14
minclass = 4          # Require all 4 character classes
dcredit = -1          # At least 1 digit
ucredit = -1          # At least 1 uppercase
lcredit = -1          # At least 1 lowercase
ocredit = -1          # At least 1 special character
maxrepeat = 3         # Max 3 consecutive identical characters
maxsequence = 3       # Max 3 consecutive sequence characters
enforce_for_root      # Apply to root too

# Step 3: Configure /etc/login.defs
PASS_MAX_DAYS   90
PASS_MIN_DAYS   1
PASS_WARN_AGE   14

# Step 4: Configure account lockout in /etc/pam.d/common-auth
auth required pam_faillock.so preauth deny=5 unlock_time=1800
auth [default=die] pam_faillock.so authfail deny=5 unlock_time=1800

# Step 5: Force password change on next login for all users
chage -d 0 username  # Per user
# Or: for user in $(cut -d: -f1 /etc/passwd); do chage -d 0 $user; done

# Step 6: Verify
chage -l username
pam_tally2 --user=username
```

**Verification**: Attempt weak password → rejected; 5 failed attempts → account locked; password expires at 90 days.

---

### 3. Missing Security Headers

**Problem**: HTTP security headers not set, enabling clickjacking, XSS, MITM.

**Step-by-Step Fix**:

**Nginx**:
```nginx
# Add to /etc/nginx/conf.d/security-headers.conf

# HSTS (HTTP Strict Transport Security)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;

# X-Frame-Options (legacy CSP frame-ancestors)
add_header X-Frame-Options "DENY" always;

# X-Content-Type-Options
add_header X-Content-Type-Options "nosniff" always;

# X-XSS-Protection (legacy, but still useful)
add_header X-XSS-Protection "1; mode=block" always;

# Referrer-Policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions-Policy
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;

# Cross-Origin headers
add_header Cross-Origin-Opener-Policy "same-origin" always;
add_header Cross-Origin-Resource-Policy "same-origin" always;
add_header Cross-Origin-Embedder-Policy "require-corp" always;

# Reload
nginx -t && systemctl reload nginx
```

**Apache**:
```apache
# Add to /etc/apache2/conf-available/security-headers.conf
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
Header always set Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'"
Header always set X-Frame-Options "DENY"
Header always set X-Content-Type-Options "nosniff"
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Permissions-Policy "camera=(), microphone=(), geolocation=()"

# Enable and reload
a2enconf security-headers
systemctl reload apache2
```

**IIS**:
```xml
<!-- Add to web.config -->
<system.webServer>
  <httpProtocol>
    <customHeaders>
      <add name="Strict-Transport-Security" value="max-age=31536000; includeSubDomains; preload" />
      <add name="Content-Security-Policy" value="default-src 'self'; frame-ancestors 'none'" />
      <add name="X-Frame-Options" value="DENY" />
      <add name="X-Content-Type-Options" value="nosniff" />
      <add name="X-XSS-Protection" value="1; mode=block" />
      <add name="Referrer-Policy" value="strict-origin-when-cross-origin" />
      <add name="Permissions-Policy" value="camera=(), microphone=(), geolocation=()" />
    </customHeaders>
  </httpProtocol>
</system.webServer>
```

**Verification**: `curl -sI https://target.com | grep -iE "strict-transport|content-security|x-frame|x-content-type|referrer-policy|permissions-policy"`

---

### 4. SMB Signing Not Required

**Problem**: SMB signing not enforced, enabling SMB relay attacks.

**Step-by-Step Fix**:
```powershell
# Step 1: Enable SMB signing requirement via GPO
# Computer Configuration → Windows Settings → Security Settings → Local Policies → Security Options
# "Microsoft network client: Digitally sign communications (always)" → Enabled
# "Microsoft network server: Digitally sign communications (always)" → Enabled

# Step 2: Or via registry
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" -Name "RequireSecuritySignature" -Value 1 -Type DWord
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" -Name "RequireSecuritySignature" -Value 1 -Type DWord

# Step 3: Restart SMB service
Restart-Service LanmanServer -Force

# Step 4: Verify
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" -Name RequireSecuritySignature
nxc smb target -u admin -p 'P@ss' --check-signing
```

**Verification**: `nxc smb target --check-signing` shows signing required.

---

### 5. LDAP Signing Not Required

**Problem**: LDAP signing not enforced, enabling LDAP relay attacks.

**Step-by-Step Fix**:
```powershell
# Step 1: Enable LDAP signing via GPO
# Computer Config → Windows Settings → Security → Local Policies → Security Options
# "Domain controller: LDAP server signing requirements" → Set to "Require signing"

# Step 2: Enable Channel Binding
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" -Name "LdapEnforceChannelBinding" -Value 2 -Type DWord

# Step 3: Restart AD DS
Restart-Service NTDS -Force

# Step 4: Verify
nxc ldap target -u admin -p 'P@ss' --check-ldap-signing
```

**Verification**: `nxc ldap target --check-ldap-signing` shows signing required.

---

## Web Application Remediation

### 6. SQL Injection

**Problem**: User input concatenated into SQL queries without parameterization.

**Step-by-Step Fix**:

**Python (psycopg2)**:
```python
# BEFORE (vulnerable):
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# AFTER (secure):
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

**Python (SQLAlchemy ORM)**:
```python
# BEFORE (vulnerable):
session.execute(text(f"SELECT * FROM users WHERE id = {user_id}"))

# AFTER (secure):
session.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})
```

**Java (PreparedStatement)**:
```java
// BEFORE (vulnerable):
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery("SELECT * FROM users WHERE id = " + userId);

// AFTER (secure):
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
stmt.setInt(1, userId);
ResultSet rs = stmt.executeQuery();
```

**PHP (PDO)**:
```php
// BEFORE (vulnerable):
$result = $pdo->query("SELECT * FROM users WHERE id = " . $_GET['id']);

// AFTER (secure):
$stmt = $pdo->prepare('SELECT * FROM users WHERE id = :id');
$stmt->execute(['id' => $_GET['id']]);
$result = $stmt->fetchAll();
```

**Node.js (Sequelize)**:
```javascript
// BEFORE (vulnerable):
const users = await sequelize.query(`SELECT * FROM users WHERE id = ${req.params.id}`);

// AFTER (secure):
const users = await sequelize.query('SELECT * FROM users WHERE id = ?', {
  replacements: [req.params.id]
});
```

**Verification**: `' OR '1'='1` returns error or empty result, not all records.

---

### 7. Cross-Site Scripting (XSS)

**Problem**: User input rendered in browser without encoding/sanitization.

**Step-by-Step Fix**:

**Python (Jinja2 auto-escaping)**:
```python
# Enable auto-escaping (default in Flask with .html templates)
app = Flask(__name__)
app.jinja_env.autoescape = True

# Manual escaping
from markupsafe import escape
render_template_string("Hello {{ name|escape }}", name=user_input)
```

**Python (Bleach for rich text)**:
```python
import bleach

# Allow only safe HTML tags
clean_html = bleach.clean(
    user_input,
    tags=['b', 'i', 'a', 'p', 'br', 'ul', 'ol', 'li'],
    attributes={'a': ['href', 'title']},
    strip=True
)
```

**React (default auto-escaping)**:
```jsx
// React auto-escapes by default — SAFE
<div>{userInput}</div>

// DANGEROUS — Never use unless absolutely necessary
<div dangerouslySetInnerHTML={{__html: userInput}} />

// If HTML needed, sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(userInput)}} />
```

**PHP**:
```php
// Output encoding
echo htmlspecialchars($user_input, ENT_QUOTES, 'UTF-8');

// For rich text
$clean = strip_tags($user_input, '<b><i><a><p>');
```

**Content Security Policy (defense-in-depth)**:
```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
```

**Verification**: `<script>alert(1)</script>` renders as escaped text, not executes.

---

### 8. Insecure Direct Object References (IDOR)

**Problem**: No server-side ownership validation on resource access.

**Step-by-Step Fix**:

**Python (Flask)**:
```python
# BEFORE (vulnerable):
@app.route('/api/documents/<int:doc_id>')
def get_document(doc_id):
    doc = Document.query.get(doc_id)
    return jsonify(doc.to_dict())

# AFTER (secure):
@app.route('/api/documents/<int:doc_id>')
@login_required
def get_document(doc_id):
    doc = Document.query.get(doc_id)
    if doc.owner_id != current_user.id:
        abort(403)  # Forbidden
    return jsonify(doc.to_dict())
```

**Node.js (Express)**:
```javascript
// BEFORE (vulnerable):
app.get('/api/documents/:id', async (req, res) => {
  const doc = await Document.findById(req.params.id);
  res.json(doc);
});

// AFTER (secure):
app.get('/api/documents/:id', authenticate, authorize('document:read'), async (req, res) => {
  const doc = await Document.findById(req.params.id);
  if (doc.ownerId !== req.user.id) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  res.json(doc);
});
```

**Verification**: Accessing another user's document returns 403 Forbidden.

---

### 9. Server-Side Request Forgery (SSRF)

**Problem**: Application fetches user-supplied URLs without validation.

**Step-by-Step Fix**:

**Python**:
```python
import ipaddress
import urllib.parse

BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('0.0.0.0/8'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
    ipaddress.ip_network('fe80::/10'),
]

ALLOWED_DOMAINS = ['api.partner.com', 'cdn.partner.com']

def validate_url(url):
    """Validate URL is safe for server-side fetching."""
    parsed = urllib.parse.urlparse(url)
    
    # Block non-HTTPS schemes
    if parsed.scheme not in ['https']:
        raise ValueError(f"Scheme {parsed.scheme} not allowed")
    
    # Block internal IPs
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        for network in BLOCKED_NETWORKS:
            if ip in network:
                raise ValueError(f"Internal IP {ip} blocked")
    except ValueError:
        pass  # Hostname not IP, check domain allowlist below
    
    # Domain allowlist
    if parsed.hostname not in ALLOWED_DOMAINS:
        raise ValueError(f"Domain {parsed.hostname} not in allowlist")
    
    return True

# Usage
try:
    validate_url(user_url)
    response = requests.get(user_url, timeout=5)
except ValueError as e:
    return jsonify({"error": str(e)}), 400
```

**Verification**: Requests to `http://169.254.169.254/`, `http://localhost/`, non-allowlisted domains return 400.

---

### 10. Missing Authentication on API Endpoints

**Problem**: API endpoints accessible without authentication.

**Step-by-Step Fix**:

**Node.js (Express middleware)**:
```javascript
// Global auth middleware
app.use('/api', (req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET);
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid token' });
  }
});

// Role-based middleware
const requireRole = (...roles) => (req, res, next) => {
  if (!roles.includes(req.user.role)) {
    return res.status(403).json({ error: 'Insufficient permissions' });
  }
  next();
};

// Apply to specific routes
app.get('/api/admin/users', requireRole('admin'), listUsers);
app.delete('/api/admin/users/:id', requireRole('admin'), deleteUser);
```

**Verification**: Unauthenticated requests return 401; low-privilege users get 403 on admin routes.

---

## macOS-Specific Remediation

### 11. macOS Security Hardening

**Step-by-Step Fix**:
```bash
# Step 1: Enable FileVault (full disk encryption)
fdesetup enable

# Step 2: Enable firewall
/usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
/usr/libexec/ApplicationFirewall/socketfilterfw --setblockall off
/usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on

# Step 3: Disable unnecessary services
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.ftp-proxy.plist 2>/dev/null
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.screensharing.agent.plist 2>/dev/null

# Step 4: Set login window to require username and password
sudo defaults write /Library/Preferences/com.apple.loginwindow SHOWFULLNAME -bool true

# Step 5: Enable secure virtual memory
sudo defaults write /Library/Preferences/com.apple.virtualMemory UseEncryptedSwap -bool yes

# Step 6: Set screen lock
defaults write com.apple.screensaver askForPassword -int 1
defaults write com.apple.screensaver askForPasswordDelay -int 0

# Step 7: Verify
fdesetup status
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

**Verification**: FileVault active; firewall on; SSH only with key auth; screen lock enabled.

---

## General Hardening Checklist

### All Systems
- [ ] Disable unnecessary services
- [ ] Enforce strong password policy (14+ chars, complexity, lockout)
- [ ] Enable MFA on all accounts
- [ ] Apply all security patches within 48 hours of release
- [ ] Enable logging and monitoring
- [ ] Implement network segmentation
- [ ] Configure intrusion detection
- [ ] Regular vulnerability scanning (monthly minimum)
- [ ] Incident response plan documented and tested

### Linux
- [ ] SSH: key-based auth only, no root login, fail2ban
- [ ] Firewall: ufw/nftables with default-deny
- [ ] AppArmor/SELinux enforced
- [ ] /tmp mounted noexec
- [ ] Automatic security updates: `unattended-upgrades`

### Windows
- [ ] SMBv1 disabled, SMB signing required
- [ ] LDAP signing + channel binding required
- [ ] LAPS deployed for local admin passwords
- [ ] Windows Defender with real-time protection
- [ ] AppLocker/WDAC application control
- [ ] PowerShell constrained language mode
- [ ] Credential Guard enabled

### Web Applications
- [ ] All security headers present (HSTS, CSP, X-Frame-Options, etc.)
- [ ] Parameterized queries everywhere
- [ ] Input validation server-side
- [ ] Output encoding for user input
- [ ] CSRF tokens on all state-changing requests
- [ ] Rate limiting on authentication endpoints
- [ ] Session management (regenerate on login, proper timeout)
- [ ] TLS 1.2+ only with strong cipher suites