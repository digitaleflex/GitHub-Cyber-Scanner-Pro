# IOS XR CLI Basics and Configuration Modes

## Accessing the Router

### Connection Methods
```bash
# SSH (recommended)
ssh admin@<router-ip>

# Console (out-of-band)
screen /dev/ttyUSB0 9600

# Telnet (not recommended for production)
telnet <router-ip>
```

### Default Login
- Username: `admin`
- Password: `admin` (change immediately)

## CLI Modes

### Executive Mode (Default)
```
RP/0/RP0/CPU0:router#
```
- View-only commands
- `show`, `ping`, `traceroute`, `clear`
- Cannot modify configuration

### Configuration Mode
```
RP/0/RP0/CPU0:router# configure terminal
RP/0/RP0/CPU0:router(config)#
```
- Enter with `configure terminal` or `conf t`
- All configuration commands available
- Changes are NOT applied until `commit`

### Sub-Configuration Modes
```
RP/0/RP0/CPU0:router(config)# router bgp 65001
RP/0/RP0/CPU0:router(config-bgp)#
  neighbor 10.0.0.1
RP/0/RP0/CPU0:router(config-bgp-nbr)#
    remote-as 65002
RP/0/RP0/CPU0:router(config-bgp-nbr)#
```

### Exiting Modes
```
end          <-- Exit to exec mode, discarding uncommitted changes
commit       <-- Apply changes and stay in config mode
commit end   <-- Apply changes and exit to exec mode
abort        <-- Discard all uncommitted changes
```

## Two-Stage Commit Model

### Basic Commit
```
RP/0/RP0/CPU0:router(config)# commit
```

### Commit with Label and Comment
```
RP/0/RP0/CPU0:router(config)# commit label BGP-PEER-ADD comment "Adding BGP peer to 10.0.0.1"
```

### Confirmed Commit (Auto-Rollback)
```
RP/0/RP0/CPU0:router(config)# commit confirmed 5
```
- Automatically rolls back after 5 minutes if not confirmed
- Confirm with: `commit confirmed`

### Rollback
```
# Rollback to last committed config
RP/0/RP0/CPU0:router# rollback configuration last 1

# Rollback to specific label
RP/0/RP0/CPU0:router# rollback configuration label BGP-PEER-ADD

# Rollback to specific commit ID
RP/0/RP0/CPU0:router# rollback configuration commit-id 1000000001
```

## Viewing Configuration

### Show Running Config
```
show running-config                    <-- Full config
show running-config router bgp         <-- BGP only
show running-config interface          <-- Interfaces only
show running-config | include <text>   <-- Filter output
show running-config | section <text>   <-- Show section
show running-config committed          <-- Last committed config
show running-config uncommitted        <-- Uncommitted changes
show configuration failed              <-- Failed commits
```

### Commit History
```
show configuration commit list         <-- All commits
show configuration commit list detail  <-- Detailed commit info
show configuration commit changes 1000000001  <-- Changes in specific commit
```

## Essential Show Commands

### System Status
```
show version                   <-- IOS XR version, uptime
show inventory                 <-- Hardware inventory
show platform                  <-- Platform status
show processes cpu             <-- CPU utilization
show processes memory          <-- Memory usage
show controllers fabric plane  <-- Fabric plane status
show redundancy                <-- RP redundancy status
```

### Interface Status
```
show interfaces                <-- All interfaces
show interfaces brief          <-- Brief summary
show interfaces <name>         <-- Specific interface
show ipv4 interface brief      <-- IPv4 interface summary
show ipv6 interface brief      <-- IPv6 interface summary
show bundle                    <-- Bundle-Ether status
```

### Routing
```
show route                     <-- Routing table
show route <prefix>            <-- Specific route
show route summary             <-- Route summary
show protocols                 <-- Running protocols
show cdp neighbors             <-- CDP neighbors
show lldp neighbors            <-- LLDP neighbors
```

### BGP
```
show bgp summary               <-- BGP neighbor summary
show bgp <neighbor>            <-- BGP neighbor details
show bgp <prefix>              <-- Specific prefix
show bgp neighbors             <-- All BGP neighbors
show bgp vpnv4 unicast summary <-- VPNv4 summary
```

## Configuration Management

### Save Configuration
```
# IOS XR auto-saves on commit (no copy run start needed)
# But you can export config:
show running-config > tftp://<server>/config.txt
```

### Load Configuration
```
load configuration from <file>
load configuration replace <file>
load configuration merge <file>
```

### Configuration Archive
```
archive
 log config
  logging enable
  notify syslog
  path tftp://<server>/archive
  maximum 100
 !
!
```

## User Management

### Create User
```
username admin
 group root-lr
 group cisco-support
 secret <password>
!
```

### User Groups
- `root-lr`: Root system access
- `root-system`: Full system access
- `cisco-support`: TAC support access
- `netops`: Network operations
- `read-only`: View-only access

### AAA Configuration
```
aaa authentication login default local
aaa authorization exec default local
aaa accounting exec default start-stop group tacacs+
!
tacacs server <name>
 address ipv4 <tacacs-ip>
 key <shared-secret>
!
```

## Logging and Debugging

### Syslog Configuration
```
logging host <syslog-server>
logging trap informational
logging source-interface <interface>
logging facility local7
!
```

### Terminal Monitoring
```
terminal monitor          <-- Enable console logging
terminal no monitor       <-- Disable console logging
terminal width 0          <-- Disable line wrapping
terminal length 0         <-- Disable pagination
```

### Debug Commands
```
debug bgp                 <-- BGP debugging (use with caution)
debug ospf events         <-- OSPF event debugging
debug isis adj-packets    <-- IS-IS adjacency debugging
debug ip packet           <-- IP packet debugging
undebug all               <-- Disable all debugging
```

## Command Shortcuts and Aliases

### Common Shortcuts
```
conf t          <-- configure terminal
sh run          <-- show running-config
sh int          <-- show interfaces
sh ip int br    <-- show ipv4 interface brief
sh bgp sum      <-- show bgp summary
sh route        <-- show route
```

### Custom Aliases
```
alias exec shbgp show bgp summary
alias exec shroute show route
alias exec shint show interfaces brief
```

## Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| `Ctrl+A` | Move to beginning of line |
| `Ctrl+E` | Move to end of line |
| `Ctrl+U` | Clear line before cursor |
| `Ctrl+K` | Clear line after cursor |
| `Ctrl+W` | Delete word before cursor |
| `Tab` | Command completion |
| `?` | Context-sensitive help |
| `Ctrl+Z` | Exit to exec mode |
| `Ctrl+C` | Abort current command |

## Best Practices

1. **Always use `commit confirmed`** for production changes
2. **Label all commits** with descriptive names
3. **Use `show running-config`** before committing to verify
4. **Test in maintenance window** for routing changes
5. **Document rollback procedures** before making changes
6. **Use `terminal length 0`** when scripting
7. **Never use `debug`** in production without understanding impact
8. **Configure logging** to external syslog server
9. **Use AAA** for authentication, not local passwords
10. **Archive configurations** regularly
