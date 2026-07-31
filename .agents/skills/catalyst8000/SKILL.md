---
name: catalyst8000
description: Comprehensive Cisco Catalyst 8000 SD-WAN engineering skill. Covers Catalyst 8000v (Cat8000v) edge router configuration, IOS XE SD-WAN CLI, vManage/vSmart/vBond orchestration, OMP, TLOC, BFD, IPsec, application-aware routing, QoS, security, zero-touch provisioning, telemetry, automation via REST APIs, Python SDK (catalystwan), Terraform provider, Ansible, Sastre, and DevNet sandbox environments. Use when configuring, troubleshooting, or designing Cisco Catalyst SD-WAN networks.
---

# Cisco Catalyst 8000 SD-WAN Engineering Skill

You are an expert Cisco Catalyst SD-WAN network engineer. Use this skill to configure, troubleshoot, and design Cisco Catalyst SD-WAN networks using Catalyst 8000v edge routers, vManage, vSmart, vBond, and the full SD-WAN fabric.

## How to Use This Skill

1. Read the relevant reference documents from `references/` based on the task
2. Use the configuration templates and CLI/API patterns provided
3. Always verify IOS XE SD-WAN version compatibility before applying configurations
4. Follow the safety guidelines for production changes
5. Reference DevNet sandbox environments for testing

## Core Reference Documents

| Document | When to Use |
|----------|-------------|
| `references/platform-overview.md` | Catalyst 8000 architecture, components, SD-WAN fabric topology |
| `references/cli-basics.md` | IOS XE SD-WAN CLI, configuration modes, show commands |
| `references/vmanage.md` | vManage configuration, templates, policies, monitoring |
| `references/vsmart-vbond.md` | vSmart controller, vBond orchestrator, OMP, TLOC |
| `references/transport-tunnels.md` | IPsec tunnels, BFD, TLOC extensions, DTLS, transport interface |
| `references/omp-routing.md` | OMP protocol, route advertisement, TLOC routes, service routes |
| `references/application-aware-routing.md` | Data policies, app-aware routing, SLA classes, forward classes |
| `references/qos-security.md` | QoS policies, zone-based firewall, IPS, URL filtering, TLS inspection |
| `references/ztp-onboarding.md` | Zero-touch provisioning, device onboarding, bootstrap |
| `references/automation-apis.md` | REST APIs, Python SDK (catalystwan), Terraform, Ansible, Sastre |
| `references/telemetry-monitoring.md` | Streaming telemetry, vManage monitoring, SNMP, syslog |
| `references/troubleshooting.md` | Diagnostic commands, debugging, common issues |
| `references/devnet-sandbox.md` | DevNet sandbox environments, Always-On labs, testing workflows |

## Catalyst SD-WAN Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cisco SD-WAN Fabric                       │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ vManage  │  │  vSmart  │  │  vBond   │  │  vAnalytics│  │
│  │ (NMS)    │  │(Controller)│(Orchestrator)│(Analytics)  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘   │
│       │              │              │                       │
│  ┌────┴──────────────┴──────────────┴──────────────────┐   │
│  │              OMP / DTLS / IPsec                      │   │
│  └────┬──────────────┬──────────────┬──────────────────┘   │
│       │              │              │                       │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐                 │
│  │ Cat8000v │  │ Cat8000v │  │ Cat8000v │                 │
│  │ (Branch) │  │ (Branch) │  │ (Hub)    │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                             │
│  Transport Networks: MPLS, Internet, LTE, 5G               │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts

| Term | Description |
|------|-------------|
| **OMP** | Overlay Management Protocol - distributes routes, TLOCs, and services |
| **TLOC** | Transport Locator - unique identifier for a WAN edge router's transport interface |
| **vManage** | Network management system - single pane of glass for the SD-WAN fabric |
| **vSmart** | SD-WAN controller - distributes policies and OMP routes |
| **vBond** | SD-WAN orchestrator - initial connectivity and NAT traversal |
| **BFD** | Bidirectional Forwarding Detection - fast failure detection |
| **Data Policy** | Application-aware routing policy based on SLA classes |
| **Control Policy** | Policy that affects OMP route advertisement |
| **vEdge** | Legacy Viptela edge router (replaced by Catalyst 8000v) |
| **cEdge** | IOS XE-based edge router (Catalyst 8000v) |

## Safety Guidelines

1. **Always test in DevNet sandbox** before production
2. **Use feature templates** rather than CLI for consistency
3. **Validate templates** before attaching to devices
4. **Use maintenance windows** for policy changes
5. **Monitor BFD sessions** after any transport changes
6. **Document rollback procedures** before making changes
7. **Never change vBond/vSmart** without full fabric impact analysis

## DevNet Sandbox Environments

| Sandbox | Type | URL | Use Case |
|---------|------|-----|----------|
| **IOS XE on Cat8kv AlwaysOn** | Always-On | `https://devnetsandbox.cisco.com` | Cat8000v CLI, IOS XE SD-WAN features |
| **SD-WAN 20.10 AlwaysOn** | Always-On | `https://devnetsandbox.cisco.com` | Full SD-WAN fabric testing |
| **IOS XE on Cat8kv** | Reservable | `https://devnetsandbox.cisco.com` | Dedicated Cat8000v lab |
| **SD-WAN 20.10** | Reservable | `https://devnetsandbox.cisco.com` | Full SD-WAN lab with vManage |

## Documentation Sources

- **DevNet:** https://developer.cisco.com/
- **DevNet Sandboxes:** https://developer.cisco.com/site/sandbox/
- **DevNet Code Exchange:** https://developer.cisco.com/codeexchange/
- **SD-WAN Terraform Provider:** https://github.com/CiscoDevNet/terraform-provider-sdwan
- **Catalyst WAN SDK:** https://github.com/CiscoDevNet/catalystwan
- **Sastre:** https://github.com/CiscoDevNet/sastre
- **SD-WAN MCP Server:** https://github.com/CiscoDevNet/catalyst-sdwan-mcp-community
- **VIRL2 Client:** https://github.com/CiscoDevNet/virl2-client
