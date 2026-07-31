# CASPER Skill - Installation Summary

## Overview

The CASPER (Comprehensive Autonomous Security Penetration & Exploitation Research) skill has been successfully created as an enterprise-class global agent skill for the OpenCode Agent Skills framework.

## What Was Created

### File Structure
```
.opencode/skill/casper/
├── SKILL.md          # Main skill definition (13 KB, 458 lines)
└── README.md         # This file
```

### Skill Metadata

**Name:** casper  
**Description:** Enterprise-grade autonomous penetration testing framework for comprehensive web application and API security assessment using CLI tools  
**License:** MIT  
**Compatibility:** OpenCode  
**Version:** 3.0  
**Category:** Security  

## Capabilities Overview

The CASPER skill provides 7 major capability areas:

### 1. General Penetration Testing
- Web application security assessment
- REST, GraphQL, and gRPC API testing
- Authentication and session management
- WAF bypass techniques

**Reference:** casper/casper-pt.md

### 2. Authorization Bypass Testing
- Horizontal privilege escalation (IDOR)
- Vertical privilege escalation
- RBAC/ABAC bypass
- JWT manipulation
- Multi-tenant security testing

**References:** 
- casper/casper-authorization.md
- casper/casper-authorization-advanced.md

### 3. Injection Attack Testing
- SQL injection (all variants)
- NoSQL injection
- Command injection
- Template injection (SSTI)
- XML/XXE injection
- GraphQL injection

**Reference:** casper/casper-injection.md

### 4. Business Logic Testing
- Financial transaction manipulation
- Workflow bypass
- Race conditions
- E-commerce logic flaws
- Time-based vulnerabilities

**References:**
- casper/casper-business-logic.md
- casper/casper-business-logic-advanced.md

### 5. API-Specific Security
- Endpoint enumeration
- GraphQL introspection
- API authorization testing
- Rate limiting bypass

**Reference:** casper/casper-scan-api.md

### 6. Advanced Automation
- Python-based testing (casper/casper-pt-python.md)
- PowerShell-based testing (casper/casper-pt-powershell.md)
- Bash automation scripts

### 7. Professional Reporting
- Executive summaries
- Technical documentation
- CVSS scoring
- Remediation recommendations

**References:**
- casper/casper-pt-reporting-simple.md
- casper/casper-pt-reporting-advanced.md

## Source Material

The CASPER skill was created by analyzing and integrating 13 comprehensive security testing documents:

1. **casper-pt.md** - Core penetration testing methodology (727 lines)
2. **casper-authorization.md** - Authorization bypass fundamentals (672 lines)
3. **casper-authorization-advanced.md** - Advanced authorization techniques (100+ lines)
4. **casper-injection.md** - Injection vulnerability testing (1,069 lines)
5. **casper-business-logic.md** - Business logic flaw testing (579 lines)
6. **casper-business-logic-advanced.md** - Advanced business logic (100+ lines)
7. **casper-business-logic-python.md** - Python automation (100+ lines)
8. **casper-business-logic-powershell.md** - PowerShell automation (100+ lines)
9. **casper-scan-api.md** - Safe API scanning (76 lines)
10. **casper-pt-python.md** - Python penetration testing (100+ lines)
11. **casper-pt-powershell.md** - PowerShell penetration testing (100+ lines)
12. **casper-pt-reporting-simple.md** - Basic reporting (678 lines)
13. **casper-pt-reporting-advanced.md** - Advanced reporting (100+ lines)

**Total source content:** ~4,000+ lines of professional security testing methodologies

## How to Use

### Loading the Skill

In OpenCode, use the skill tool to load CASPER:

```
Use the skill tool to load casper
```

Or refer to it in your agent configuration:

```json
{
  "skills": {
    "casper": "allow"
  }
}
```

### Quick Examples

#### Authorization Testing
```bash
# Test horizontal privilege escalation
curl -s -H "Authorization: Bearer $USER1_TOKEN" \
  https://api.target.com/resources/user2_resource_id
```

#### Injection Testing
```bash
# SQL injection detection
curl -s "https://api.target.com/search?q=test' OR '1'='1"
```

#### Business Logic Testing
```bash
# Negative amount transfer
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -d '{"amount":-100,"to":"target"}' \
  https://bank.api.com/transfer
```

## Tool Requirements

### Essential Tools
- curl - HTTP client
- jq - JSON processor
- bash - Shell scripting
- grep/awk/sed - Text processing

### Optional Tools
- python3 - Advanced automation
- pwsh - Windows testing
- grpcurl - gRPC testing
- jwt-cli - Token manipulation

## Key Features

### Progressive Disclosure
The skill uses a layered approach:
1. SKILL.md provides high-level overview and quick start
2. Reference documents in casper/ provide detailed methodologies
3. Examples show practical application patterns

### Multi-Language Support
- **Bash** - Lightweight, cross-platform
- **Python** - Complex operations and data processing
- **PowerShell** - Windows and enterprise environments

### Comprehensive Coverage
- Web applications
- REST APIs
- GraphQL APIs
- gRPC services
- Financial systems
- E-commerce platforms
- SaaS applications

### Enterprise-Ready
- Professional reporting templates
- CVSS scoring
- Compliance mapping (PCI-DSS, GDPR, OWASP)
- Business impact analysis

## Ethical Guidelines

The skill emphasizes:
- **Legal authorization** - Always get written permission
- **Safe testing** - Use read-only operations when possible
- **Responsible disclosure** - Follow proper reporting procedures
- **Documentation** - Maintain detailed records
- **Professional standards** - Follow industry best practices

## Design Philosophy

### Core Principles
1. **CLI-First**: Maximize command-line tool potential
2. **Enterprise-Grade**: Professional, production-ready assessments
3. **Autonomous**: Designed for AI agent operation
4. **Comprehensive**: Cover all major vulnerability classes
5. **Practical**: Focus on real-world exploitation techniques

### Structure
- **Frontmatter**: Proper YAML with required fields
- **Overview**: Clear explanation of capabilities
- **Examples**: Practical, copy-paste ready code
- **References**: Links to detailed methodologies
- **Best Practices**: Safety and quality guidelines

## Success Metrics

The CASPER skill enables:
- ✅ **Complete security assessments** using only CLI tools
- ✅ **Professional reporting** with business impact analysis
- ✅ **Multi-domain testing** (financial, e-commerce, SaaS)
- ✅ **Automated vulnerability discovery** via scripting
- ✅ **Enterprise integration** with Python and PowerShell

## Next Steps

1. **Test the skill**: Load it in OpenCode and run basic tests
2. **Customize**: Adjust methodologies for your specific needs
3. **Extend**: Add custom scripts and tools to casper/
4. **Integrate**: Connect with other security tools and workflows

## Maintenance

### Version Updates
- Current: v3.0 (2026-01-07)
- Update metadata.updated field when making changes
- Document changes in version history section

### Adding Content
- Place new methodologies in casper/ directory
- Reference them in SKILL.md core capabilities
- Maintain consistent naming: casper-[topic]-[variant].md

## Support

For detailed methodologies, consult the reference documents in the casper/ directory. Each document provides:
- Comprehensive testing procedures
- Practical examples
- Tool-specific guidance
- Security best practices

---

**Created:** 2026-01-07  
**Framework:** OpenCode Agent Skills v1.0  
**Classification:** Production-Ready
