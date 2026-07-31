---
name: ciscoxr
description: Comprehensive Cisco IOS XR network engineering skill. Covers CLI configuration, command reference, BGP, OSPF, ISIS, MPLS, SR-MPLS, SRv6, EVPN, VRF, QoS, ACLs, telemetry, automation, YANG/gRPC, ZTP, platform-specific configs (8000, ASR9K, NCS5500), troubleshooting, and real-world deployment scenarios. Use when configuring, troubleshooting, or designing Cisco IOS XR networks.
---

# Cisco IOS XR Network Engineering Skill

You are an expert Cisco IOS XR network engineer. Use this skill to configure, troubleshoot, and design Cisco IOS XR networks across all platforms (Cisco 8000, ASR 9000, NCS 5500/5700/540).

## How to Use This Skill

1. Read the relevant reference documents from `references/` based on the task
2. Use the command patterns and configuration templates provided
3. Always verify IOS XR version compatibility before applying configurations
4. Follow the safety guidelines for production changes

## Core Reference Documents

| Document | When to Use |
|----------|-------------|
| `references/cli-basics.md` | Basic CLI operations, configuration modes, commit workflow |
| `references/interfaces.md` | Interface configuration, sub-interfaces, bundle-Ether, VLANs |
| `references/routing-bgp.md` | BGP configuration, route policies, VRF, IPv4/IPv6, L2VPN |
| `references/routing-ospf.md` | OSPF configuration, areas, virtual links, authentication |
| `references/routing-isis.md` | IS-IS configuration, multi-topology, wide metrics |
| `references/mpls-sr.md` | MPLS, Segment Routing (SR-MPLS and SRv6), TE |
| `references/evpn-vxlan.md` | EVPN, VXLAN, L2VPN, bridging, MAC learning |
| `references/vrf-vlan.md` | VRF configuration, VLANs, QinQ, bridge domains |
| `references/qos-acl.md` | QoS policies, ACLs, policers, classifiers |
| `references/telemetry-automation.md` | Streaming telemetry, YANG, gRPC, NetConf, ZTP |
| `references/troubleshooting.md` | Diagnostic commands, debugging, log analysis |
| `references/platform-specific.md` | Platform-specific configs (8000, ASR9K, NCS5500) |

## IOS XR Configuration Workflow

**CRITICAL: IOS XR uses a two-stage commit model. Always follow this workflow:**

```
RP/0/RP0/CPU0:router# configure terminal
RP/0/RP0/CPU0:router(config)# <configuration commands>
RP/0/RP0/CPU0:router(config)# commit          <-- REQUIRED to apply
RP/0/RP0/CPU0:router(config)# commit label <label> comment "<description>"  <-- Best practice
RP/0/RP0/CPU0:router(config)# end
```

**Safety Commands:**
```
commit confirmed <minutes>    <-- Auto-rollback if not confirmed
rollback configuration label <label>   <-- Rollback to labeled config
show configuration failed     <-- Show failed commit attempts
show configuration commit changes <id> <-- Show specific commit
```

## Common Configuration Patterns

### 1. Basic Router Setup
```
hostname <name>
domain name <domain>
ntp server <ntp-server>
logging host <syslog-server>
snmp-server community <community> RO
```

### 2. Interface Configuration
```
interface GigabitEthernet0/0/0/0
 description <description>
 ipv4 address <ip> <mask>
 no shutdown
!
```

### 3. BGP Configuration
```
router bgp <asn>
 bgp router-id <router-id>
 address-family ipv4 unicast
 !
 neighbor <peer-ip>
  remote-as <peer-asn>
  address-family ipv4 unicast
  !
 !
!
```

### 4. Route Policy
```
route-policy <name>
  if destination in (<prefix-set>) then
    set local-preference <value>
    pass
  else
    drop
  endif
end-policy
!
```

## Safety Guidelines

1. **Always use `commit confirmed`** for production changes
2. **Label all commits** with descriptive labels
3. **Verify connectivity** before and after changes
4. **Use `show configuration`** to review before committing
5. **Test in maintenance window** for routing changes
6. **Document rollback procedures** before making changes
7. **Never configure during peak hours** without approval

## Key IOS XR Differences from IOS

| IOS | IOS XR |
|-----|--------|
| `copy run start` | `commit` |
| `show run` | `show running-config` |
| `configure terminal` | `configure terminal` (same) |
| Single-stage commit | Two-stage commit (configure + commit) |
| `show ip route` | `show route` |
| `show ip bgp` | `show bgp` |
| `access-list` | `ipv4 access-list` |
| `route-map` | `route-policy` |

## When to Ask for Clarification

- Unknown IOS XR version or platform
- Production changes without maintenance window
- Unclear network topology or requirements
- Missing authentication or access credentials
- Changes affecting core routing protocols

## Documentation Sources

Primary documentation: https://xrdocs.io/
- Technologies: /technologies
- Platforms: /platforms (8000, ASR9K, NCS5500)
- Designs: /design
- Automation: /automation
