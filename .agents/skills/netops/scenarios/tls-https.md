# Scenario — TLS / HTTPS / QUIC

TLS failures are common and confusing because the symptom ("can't reach https://X") looks like a network problem but the cause is often cert/SNI/cipher/ALPN. Use `SSLKEYLOGFILE` decryption **only for traffic you control** (your own clients) — never third-party or malware.

---

## Triage

```bash
# 1. Does the TLS handshake complete?
openssl s_client -connect example.com:443 -servername example.com -showcerts </dev/null 2>&1 | tee tls.log
#   - Read the cert chain, verify return code
#   - "verify return code: 0 (ok)" = cert valid
#   - "alert handshake failure" = cipher/SNI/version mismatch
#   - "alert certificate expired" = expired cert
#   - "alert hostname mismatch" = SNI/cert name mismatch

# 2. Force a specific TLS version
openssl s_client -connect example.com:443 -servername example.com -tls1_2 </dev/null
openssl s_client -connect example.com:443 -servername example.com -tls1_3 </dev/null

# 3. curl with verbose
curl -v --max-time 10 https://example.com/   # the `*` lines show TLS negotiation
curl -v --tlsv1.2 --tls-max 1.2 https://example.com/

# 4. Which ciphers does the server offer?
nmap --script ssl-enum-ciphers -p 443 example.com   # or:
openssl s_client -connect example.com:443 -servername example.com </dev/null | grep "Cipher"

# 5. HTTP/2 vs HTTP/1.1
curl -v --http2 https://example.com/         # does HTTP/2 negotiate?
curl -v --http1.1 https://example.com/        # does falling back fix it?
```

---

## Symptom → cause map

| Symptom | Likely cause | Confirm with |
|---|---|---|
| `handshake failure` (alert 40) | Cipher/SNI/TLS version mismatch | `openssl s_client -tls1_2/1_3`; check server cipher list |
| `certificate expired` (alert 45) | Expired cert | `openssl s_client` → verify dates |
| `hostname mismatch` / SNI issue | SNI not sent, or cert has wrong SAN | `openssl s_client -servername` (with and without) |
| `protocol version` (alert 70) | Server doesn't support client's TLS version | Force `-tls1_2` / `-tls1_3` |
| Works in browser, fails in curl/openssl | Missing SNI, or browser has older cipher suite | Send SNI: `-servername` |
| HTTP/2 fails, HTTP/1.1 works | ALPN negotiation or HTTP/2 implementation | `curl --http1.1`; check ALPN |
| QUIC (UDP 443) fails, TCP 443 works | UDP blocked on path, QUIC broken | test UDP 443 reachability; mtu-path.md |
| TLS 1.3 works, 1.2 fails (or vice versa) | Version/cipher policy | Force versions |
| Only one client fails | Client cipher/SNI/version config | Compare client configs |
| All clients fail | Server cert/config | Check server |
| Intermittent TLS hangs | Network dropping large ClientHello/ServerHello (MTU) | mtu-path.md |

---

## Playbook: "TLS handshake fails — cipher/SNI"

### Step 1 — Reproduce and see the alert
```bash
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>&1 | grep -iE 'alert|verify|cipher|protocol'
```

### Step 2 — Capture the handshake (host-based on the client)
```bash
sudo tshark -i any -Y "tls.handshake.type == 1 || tls.handshake.type == 2 || tls.alert_message" -w tls.pcap
# ClientHello = type 1, ServerHello = type 2, alert = failure
# See the alert code:
tshark -r tls.pcap -Y "tls.alert_message" -V | grep -i alert
```

### Step 3 — Decrypt with SSLKEYLOGFILE (if you control the client)
```bash
# Set the keylog env var on the CLIENT process, then capture
SSLKEYLOGFILE=/tmp/sslkeylog.txt curl https://example.com/ &
sudo tshark -i any -o "tls.keylog_file:/tmp/sslkeylog.txt" -Y "http" -w decrypted.pcap
# Now you see the decrypted HTTP inside the TLS
# With netwatch on the same host:
SSLKEYLOGFILE=/tmp/sslkeylog.txt sudo netwatch
# Packets tab → filter decrypted:true → see plaintext HTTP
```

### Step 4 — Common fixes
| Finding | Fix |
|---|---|
| Server offers no shared cipher | Update server cipher suite OR update client |
| SNI required but client not sending | Client must send SNI (`-servername`, `--resolve`, `Host:` header) |
| TLS 1.0/1.1 disabled on server, client only does 1.0 | Upgrade client to 1.2+ |
| Self-signed cert | Add to client trust store (or use `-k` / `--insecure` for testing) |
| Cert SAN missing the hostname | Reissue cert with correct SAN |

---

## Playbook: "HTTPS to some sites hangs"

Often PMTUD (large ServerHello/Certificate messages) — see mtu-path.md.

```bash
# Confirm: small sites work, large-certificate sites hang
openssl s_client -connect small-site:443 -servername small-site </dev/null   # works
openssl s_client -connect big-corp-site:443 -servername big-corp-site </dev/null  # hangs?
# Capture: do we send ClientHello and get no ServerHello?
sudo tshark -i any -Y "tls.handshake.type == 1 || tls.handshake.type == 2"
# If ClientHello out but no ServerHello back → packet drop on path (often MTU)
tracepath big-corp-site    # check PMTU
```

---

## Playbook: "HTTP/2 vs HTTP/1.1"

```bash
curl -v --http2 https://example.com/ 2>&1 | grep -i 'ALPN\|HTTP/2'
curl -v --http1.1 https://example.com/   # does the fallback work?
# ALPN negotiation in the capture:
sudo tshark -i any -Y "tls.handshake.extensions_alpn_str" -V | grep -i alpn
```
If HTTP/2 fails but HTTP/1.1 works → server ALPN misconfigured, or a middlebox stripping ALPN, or client HTTP/2 implementation bug.

---

## Playbook: "QUIC / HTTP/3 (UDP 443)"

QUIC runs over UDP/443. Many networks block or mishandle UDP 443.

```bash
# Does UDP 443 even reach the server?
nc -uvz -w 3 example.com 443          # UDP test (unreliable but quick)
# curl supports HTTP/3:
curl --http3 -v https://example.com/   # if curl built with HTTP/3
# Capture QUIC:
sudo tshark -i any -Y "quic" -w quic.pcap
# QUIC handshake: Initial → Handshake → 1-RTT
tshark -r quic.pcap -Y "quic.packet.long.packet_type == 0"     # Initial
```

### Common QUIC issues
| Symptom | Cause | Fix |
|---|---|---|
| Hangs on QUIC, works on TCP 443 | UDP 443 blocked on path | Allow UDP 443, or force TCP (`curl --http1.1`/disable HTTP/3 in client) |
| QUIC packet loss | UDP often gets dropped preferentially under congestion | QoS to protect UDP 443, or fall back to TCP |
| MTU issues with QUIC | QUIC has its own PMTUD; large initial packets can drop | mtu-path.md |

---

## Playbook: "expired / untrusted cert"

```bash
openssl s_client -connect example.com:443 -servername example.com </dev/null | openssl x509 -noout -dates
# notBefore / notAfter
# Full chain validation:
openssl s_client -connect example.com:443 -servername example.com -verify_return_error </dev/null 2>&1 | grep -i verify
```
Fixes:
- Expired → renew the cert
- Untrusted → install the CA in the client trust store, or fix the chain (server not sending intermediate)
- Name mismatch → reissue with correct SAN

---

## Decrypting TLS you control — the SSLKEYLOGFILE pattern

This is the single most useful TLS troubleshooting technique. Works in netwatch, tshark, Wireshark.

### Setup (Linux client)
```bash
# Export on the client process you want to observe
SSLKEYLOGFILE=/tmp/sslkeylog.txt firefox &            # browser
SSLKEYLOGFILE=/tmp/sslkeylog.txt curl https://example.com/   # curl
SSLKEYLOGFILE=/tmp/sslkeylog.txt python3 app.py       # Python (requests/urllib3)
# Node.js: set NODE_OPTIONS=--tls-keylog=/tmp/sslkeylog.txt
# Go: set SSLKEYLOGFILE in the environment
```

### Capture + decrypt on the same host (netwatch)
```bash
SSLKEYLOGFILE=/tmp/sslkeylog.txt sudo netwatch
# Packets tab → filter decrypted:true → see plaintext HTTP
```

### Capture + decrypt on a sensor (tshark)
```bash
sudo tshark -i eth0 -o "tls.keylog_file:/tmp/sslkeylog.txt" -w cap.pcap    # capture with decryption
tshark -r cap.pcap -o "tls.keylog_file:/tmp/sslkeylog.txt" -Y "http"       # post-hoc decrypt
```

### Caveats
- **Only decrypts traffic where you set the env var on the client** — i.e., traffic you control
- **Cannot** decrypt third-party clients, other users' traffic, or malware TLS
- For malware TLS, use **JA4 fingerprinting** (netwatch) — identify by handshake, not by decrypting

---

## Evidence checklist

- [ ] `openssl s_client` output (the alert code / verify result)
- [ ] TLS capture showing ClientHello + ServerHello + any alert
- [ ] Decrypted HTTP (if you controlled the client) via SSLKEYLOGFILE
- [ ] Cipher list + version both ends support
- [ ] Cert dates + SAN + chain
