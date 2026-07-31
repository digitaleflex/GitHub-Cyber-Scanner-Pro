#!/usr/bin/env bash
# vcenter.sh — vCenter + ESXi discovery collector (HTTPS API / govc / SSH).
# Emits normalized JSON for the vCenter asset AND its VMs (with runs-on links).
# Requires: govc (preferred) OR PowerCLI on the collector host, and SSH to ESXi.
# Env: VCENTER_HOST, VCENTER_USER, VCENTER_PASS (vaulted), ESXI_HOST (optional).
set -u

VC_HOST="${VCENTER_HOST:-}"
VC_USER="${VCENTER_USER:-}"
VC_PASS="${VCENTER_PASS:-}"
ESXI="${ESXI_HOST:-}"

jstr() { printf '"%s"' "$(printf '%s' "$1" | tr -d '\r' | sed 's/"/\\"/g')"; }

if ! command -v govc >/dev/null 2>&1; then
  cat <<EOF
{"key":"vcenter:$VC_HOST","type":"vcenter","name":$(jstr "$VC_HOST"),"fqdn":$(jstr "$VC_HOST"),"mgmtIp":$(jstr "$VC_HOST"),"source":"vcenter",
"attrs":{"os":"VMware vCenter","error":"govc not installed on collector host — install govc or use PowerCLI"}}
EOF
  exit 0
fi

export GOVC_URL="https://${VC_USER}:${VC_PASS}@${VC_HOST}/sdk"
export GOVC_INSECURE="${GOVC_INSECURE:-true}"

ABOUT=$(govc about 2>/dev/null | tr '\n' ' ')
VMS_JSON="[]"
LINKS_JSON="[]"

if [ -n "$ESXI" ]; then
  VMS_JSON=$(govc ls "/${ESXI}/vm" 2>/dev/null | while read -r vmpath; do
    vmname=$(basename "$vmpath")
    info=$(govc vm.info -json=true "$vmpath" 2>/dev/null)
    state=$(printf '%s' "$info" | grep -oE '"PowerState":[^,}]*' | head -1 | cut -d: -f2 | tr -d '" ')
    printf '%s{"key":"vm:%s","type":"vm","name":%s,"attrs":{"powerState":%s}}' \
      "$( [ -n "$seen" ] && echo ,)" "$vmname" "$(jstr "$vmname")" "$(jstr "$state")"
    seen=1
  done | tr -d '\n')
  LINKS_JSON=$(govc ls "/${ESXI}/vm" 2>/dev/null | while read -r vmpath; do
    vmname=$(basename "$vmpath")
    printf '%s{"from":"vm:%s","to":"esx:%s","rel":"runs-on"}' "$( [ -n "$lseen" ] && echo ,)" "$vmname" "$ESXI"
    lseen=1
  done | tr -d '\n')
fi

cat <<EOF
{"key":"vcenter:$VC_HOST","type":"vcenter","name":$(jstr "$VC_HOST"),"fqdn":$(jstr "$VC_HOST"),"mgmtIp":$(jstr "$VC_HOST"),"source":"vcenter",
"attrs":{"os":"VMware vCenter","about":$(jstr "$ABOUT"),"esxHost":$(jstr "$ESXI")},
"vms":[${VMS_JSON}],"links":[${LINKS_JSON}]}
EOF
