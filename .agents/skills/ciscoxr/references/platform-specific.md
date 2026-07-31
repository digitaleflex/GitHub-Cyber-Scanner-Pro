# IOS XR Platform-Specific Configuration Reference

## Cisco 8000 Series

### Platform Overview
- Powered by Cisco Silicon One™ Q200/Q200L ASICs
- Fixed-form factor routers (8201, 8202, 8101, 8102, 8201-32FH, 8201-64H, 8202-64H)
- 400GE and 800GE interfaces
- Cloud-scale routing platform

### Platform-Specific Commands
```
show platform                          -- 8000 platform status
show controllers fabric plane          -- Fabric plane status
show controllers npu                   -- NPU status
show controllers npu <npu-id> port <port> counters  -- NPU port counters
show controllers optics                  -- Optical transceiver status
```

### 8000 Interface Naming
```
FourHundredGigE0/0/0/0    -- 400GE interface
EightHundredGigE0/0/0/0   -- 800GE interface (8202-64H)
HundredGigE0/0/0/0        -- 100GE interface
```

### 8000 Best Practices
```
# Enable NPU counters
controllers npu 0
 counter poll interval 30
!

# Configure optimal MTU for 400GE
interface FourHundredGigE0/0/0/0
 mtu 9216
 no shutdown
!
```

## ASR 9000 Series

### Platform Overview
- Aggregation Services Router
- Modular and fixed-form factor options
- BNG, MPLS, and mobile backhaul capabilities
- RP (Route Processor) and LC (Line Card) architecture

### Platform-Specific Commands
```
show platform                          -- ASR9K platform status
show controllers fabric plane          -- Fabric plane status
show redundancy                        -- RP redundancy status
show platform                          -- LC status
show controllers npu                   -- NPU status
```

### ASR 9000 BNG Configuration
```
bng
 profile BNG-PROFILE
  subscriber-interface Bundle-Ether10.100
   dhcp ipv4
    profile DHCP-PROFILE proxy
   !
  !
 !
!
```

### ASR 9000 Redundancy
```
redundancy
!
```

### ASR 9000 Best Practices
```
# Configure RP redundancy
redundancy
!

# Enable fabric plane monitoring
show controllers fabric plane
```

## NCS 5500/5700/540 Series

### Platform Overview
- Network Convergence System
- High-density 100GE/400GE routing
- Service provider edge and core deployments
- Fixed-form factor (NCS 540, 5500) and modular (NCS 5700)

### Platform-Specific Commands
```
show platform                          -- NCS platform status
show controllers fabric plane          -- Fabric plane status
show controllers npu                   -- NPU status
```

### NCS 5500 Best Practices
```
# Configure optimal MTU
interface HundredGigE0/0/0/0
 mtu 9216
 no shutdown
!

# Enable NPU counters for monitoring
controllers npu 0
 counter poll interval 30
!
```

## Platform Comparison

| Feature | Cisco 8000 | ASR 9000 | NCS 5500 |
|---------|-----------|----------|----------|
| **Use Case** | Cloud core, DCI | Aggregation, BNG | SP edge, aggregation |
| **Max Interface Speed** | 800GE | 400GE | 400GE |
| **Form Factor** | Fixed | Modular/Fixed | Fixed |
| **ASIC** | Silicon One Q200 | Custom | Silicon One |
| **Routing Scale** | 1M+ routes | 500K+ routes | 500K+ routes |
| **BNG Support** | No | Yes | Limited |
| **Redundancy** | N/A (fixed) | RP redundancy | N/A (fixed) |

## Common Platform Commands

### Hardware Status
```
show platform                          -- Platform status
show inventory                         -- Hardware inventory
show controllers fabric plane          -- Fabric plane status
show controllers npu                   -- NPU status
show controllers optics                  -- Optical transceiver status
show environment                       -- Environmental status
show power                             -- Power supply status
show fans                              -- Fan status
```

### Software Management
```
show version                           -- IOS XR version
show install active summary            -- Active packages
show install committed                  -- Committed packages
install add source <path> activate      -- Add and activate package
install commit                         -- Commit package changes
install remove inactive                 -- Remove inactive packages
```

### Platform-Specific Troubleshooting

#### Cisco 8000
```
show controllers npu 0 port 0 counters  -- NPU port counters
show controllers fabric plane all       -- Fabric plane status
show controllers optics                  -- Optical transceiver status
```

#### ASR 9000
```
show redundancy                        -- RP redundancy status
show platform lc                        -- Line card status
show platform rp                        -- Route processor status
show controllers fabric plane all       -- Fabric plane status
```

#### NCS 5500
```
show controllers npu 0 port 0 counters  -- NPU port counters
show controllers fabric plane all       -- Fabric plane status
show controllers optics                  -- Optical transceiver status
```

## Platform Upgrade Procedure

### Step 1: Check Current Version
```
show version
show install active summary
```

### Step 2: Add New Package
```
install add source <tftp://server>/image.tar.gz activate
```

### Step 3: Verify Upgrade
```
show install active summary
show version
```

### Step 4: Commit Changes
```
install commit
```

### Step 5: Rollback (if needed)
```
install rollback to <previous-version>
```

## Platform Best Practices

1. **Always verify hardware compatibility** before deploying new interfaces
2. **Use `show controllers optics`** to monitor optical levels
3. **Monitor fabric plane status** for hardware health
4. **Configure NPU counters** for performance monitoring
5. **Use `install commit`** after software upgrades
6. **Document platform-specific limitations** (e.g., BNG only on ASR 9000)
7. **Verify transceiver compatibility** before deployment
8. **Monitor environmental sensors** for temperature and power
9. **Use `show platform`** regularly for hardware health checks
10. **Follow Cisco's upgrade procedures** for software updates
