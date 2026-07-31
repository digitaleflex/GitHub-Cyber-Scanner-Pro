#!/usr/bin/env bash
#
# secure-scan.sh — End-to-end security scan orchestrator
#
# Runs Semgrep, Gitleaks, Trivy, CodeQL, and Horusec in sequence,
# aggregates results, and produces a summary report.
#
# Usage:
#   bash scripts/secure-scan.sh /path/to/project [options]
#
# Options:
#   --layers LAYERS        Comma-separated list of layers to run
#                         Available: secrets,patterns,deps,misconfigs,containers,deep,sweep,quick,all
#                         Default: all
#   --ci                   Fail on any HIGH/CRITICAL finding (exit code 1)
#   --severity SEV         Comma-separated severity filter (default: all)
#                         Values: critical,high,medium,low,info
#   --format FORMAT        Output format: text (default), json
#   --output FILE          Write results to file (default: stdout)
#   --timeout SECS         Timeout per tool in seconds (default: 600)
#   --skip-dirs DIRS       Comma-separated dirs to exclude
#   --help                 Show this help message
#
set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────────

PROJECT_DIR=""
LAYERS="all"
CI_MODE=false
SEVERITY=""
FORMAT="text"
OUTPUT=""
TIMEOUT=600
SKIP_DIRS="node_modules,vendor,.git,dist,build,__pycache__,.venv,venv,egg-info,.next"
RESULTS_DIR="/tmp/security-scan-results"

# ─── Colors ─────────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ─── Parse Arguments ───────────────────────────────────────────────────────────

show_help() {
    sed -n '3,21p' "$0" | sed 's/^# //' | sed 's/^#//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --layers)     LAYERS="$2"; shift 2 ;;
        --ci)         CI_MODE=true; shift ;;
        --severity)   SEVERITY="$2"; shift 2 ;;
        --format)     FORMAT="$2"; shift 2 ;;
        --output)     OUTPUT="$2"; shift 2 ;;
        --timeout)    TIMEOUT="$2"; shift 2 ;;
        --skip-dirs)  SKIP_DIRS="$2"; shift 2 ;;
        --help|-h)    show_help ;;
        -*)           echo "Unknown option: $1"; exit 1 ;;
        *)            PROJECT_DIR="$1"; shift ;;
    esac
done

if [[ -z "$PROJECT_DIR" ]]; then
    echo -e "${RED}Error: Project directory required${NC}"
    echo "Usage: bash scripts/secure-scan.sh /path/to/project [options]"
    exit 1
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo -e "${RED}Error: Directory does not exist: $PROJECT_DIR${NC}"
    exit 1
fi

# Resolve absolute path
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

# ─── Determine Layers ──────────────────────────────────────────────────────────

declare -A RUN_LAYER
case "$LAYERS" in
    all)       RUN_LAYER[secrets]=1; RUN_LAYER[patterns]=1; RUN_LAYER[deps]=1; RUN_LAYER[misconfigs]=1; RUN_LAYER[containers]=1; RUN_LAYER[deep]=1; RUN_LAYER[sweep]=1 ;;
    quick)     RUN_LAYER[secrets]=1; RUN_LAYER[patterns]=1; RUN_LAYER[deps]=1 ;;
    secrets)   RUN_LAYER[secrets]=1 ;;
    patterns)  RUN_LAYER[patterns]=1 ;;
    deps)      RUN_LAYER[deps]=1 ;;
    misconfigs) RUN_LAYER[misconfigs]=1 ;;
    containers) RUN_LAYER[containers]=1 ;;
    deep)      RUN_LAYER[deep]=1 ;;
    sweep)     RUN_LAYER[sweep]=1 ;;
    *)
        IFS=',' read -ra LAYER_ARRAY <<< "$LAYERS"
        for layer in "${LAYER_ARRAY[@]}"; do
            RUN_LAYER["$(echo "$layer" | xargs)"]=1
        done
        ;;
esac

# ─── Setup ─────────────────────────────────────────────────────────────────────

mkdir -p "$RESULTS_DIR"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${CYAN}  Secure Code Analysis & Review${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Project: ${BOLD}$PROJECT_DIR${NC}"
echo -e "  Layers:  ${BOLD}$LAYERS${NC}"
echo -e "  CI mode: ${BOLD}$CI_MODE${NC}"
echo ""

# ─── Tool Availability Check ───────────────────────────────────────────────────

check_tool() {
    if command -v "$1" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $1 ($(command -v "$1"))"
        return 0
    else
        echo -e "  ${RED}✗${NC} $1 (not found)"
        return 1
    fi
}

echo -e "${BOLD}Tool Availability:${NC}"
TOOLS_AVAILABLE=0
if [[ -n "${RUN_LAYER[secrets]:-}" ]]; then
    check_tool gitleaks || TOOLS_AVAILABLE=1
fi
if [[ -n "${RUN_LAYER[patterns]:-}" ]]; then
    check_tool semgrep || TOOLS_AVAILABLE=1
fi
if [[ -n "${RUN_LAYER[deps]:-}" || -n "${RUN_LAYER[misconfigs]:-}" || -n "${RUN_LAYER[containers]:-}" ]]; then
    check_tool trivy || TOOLS_AVAILABLE=1
fi
if [[ -n "${RUN_LAYER[deep]:-}" ]]; then
    check_tool codeql || TOOLS_AVAILABLE=1
fi
if [[ -n "${RUN_LAYER[sweep]:-}" ]]; then
    check_tool horusec || TOOLS_AVAILABLE=1
fi

if [[ $TOOLS_AVAILABLE -ne 0 ]]; then
    echo ""
    echo -e "${YELLOW}Some tools are missing. Install them or use --layers to skip.${NC}"
    if [[ "$CI_MODE" == true ]]; then
        exit 1
    fi
fi
echo ""

# ─── Phase 1: Secret Detection (Gitleaks) ──────────────────────────────────────

if [[ -n "${RUN_LAYER[secrets]:-}" ]] && command -v gitleaks &>/dev/null; then
    echo -e "${BOLD}${BLUE}━━━ Layer 1: Secret Detection (Gitleaks) ━━━${NC}"
    GITLEAKS_ARGS="detect --source $PROJECT_DIR --report-format json --report-path $RESULTS_DIR/gitleaks.json -v"
    # If not a git repo, use --no-git
    if [[ ! -d "$PROJECT_DIR/.git" ]]; then
        GITLEAKS_ARGS="$GITLEAKS_ARGS --no-git"
    fi
    gitleaks $GITLEAKS_ARGS 2>&1 || true
    echo ""
fi

# ─── Phase 2: Pattern Scan (Semgrep) ──────────────────────────────────────────

if [[ -n "${RUN_LAYER[patterns]:-}" ]] && command -v semgrep &>/dev/null; then
    echo -e "${BOLD}${BLUE}━━━ Layer 2: Pattern Scan (Semgrep) ━━━${NC}"
    SEMGREP_ARGS="--config auto --json --output $RESULTS_DIR/semgrep.json --exclude $SKIP_DIRS $PROJECT_DIR"
    if [[ -n "$SEVERITY" ]]; then
        SEMGREP_ARGS="--config auto --json --output $RESULTS_DIR/semgrep.json --exclude $SKIP_DIRS"
        for sev in $(echo "$SEVERITY" | tr ',' ' '); do
            SEMGREP_ARGS="$SEMGREP_ARGS --severity $(echo $sev | tr '[:lower:]' '[:upper:]')"
        done
        SEMGREP_ARGS="$SEMGREP_ARGS $PROJECT_DIR"
    fi
    semgrep $SEMGREP_ARGS 2>&1 || true
    echo ""
fi

# ─── Phase 3: Dependency Scan (Trivy SCA) ────────────────────────────────────

if [[ -n "${RUN_LAYER[deps]:-}" ]] && command -v trivy &>/dev/null; then
    echo -e "${BOLD}${BLUE}━━━ Layer 3: Dependency Scan (Trivy) ━━━${NC}"
    TRIVY_SEVERITY=""
    if [[ -n "$SEVERITY" ]]; then
        TRIVY_SEVERITY="--severity $(echo $SEVERITY | tr '[:lower:]' '[:upper:]')"
    fi
    trivy fs --scanners vuln,secret $TRIVY_SEVERITY --skip-dirs "$SKIP_DIRS" --format json --output "$RESULTS_DIR/trivy-deps.json" "$PROJECT_DIR" 2>&1 || true
    echo ""
fi

# ─── Phase 4: Misconfig Scan (Trivy IaC) ──────────────────────────────────────

if [[ -n "${RUN_LAYER[misconfigs]:-}" ]] && command -v trivy &>/dev/null; then
    echo -e "${BOLD}${BLUE}━━━ Layer 4: Misconfig Scan (Trivy IaC) ━━━${NC}"
    TRIVY_SEVERITY=""
    if [[ -n "$SEVERITY" ]]; then
        TRIVY_SEVERITY="--severity $(echo $SEVERITY | tr '[:lower:]' '[:upper:]')"
    fi
    trivy fs --scanners misconfig $TRIVY_SEVERITY --skip-dirs "$SKIP_DIRS" --format json --output "$RESULTS_DIR/trivy-iac.json" "$PROJECT_DIR" 2>&1 || true
    echo ""
fi

# ─── Phase 5: Container Scan (Trivy Image) ───────────────────────────────────

if [[ -n "${RUN_LAYER[containers]:-}" ]] && command -v trivy &>/dev/null; then
    echo -e "${BOLD}${BLUE}━━━ Layer 5: Container Scan (Trivy Image) ━━━${NC}"
    # Scan Dockerfile base images
    while IFS= read -r dockerfile; do
        if [[ -f "$dockerfile" ]]; then
            BASE_IMAGE=$(grep -m1 "^FROM" "$dockerfile" 2>/dev/null | awk '{print $2}' || true)
            if [[ -n "$BASE_IMAGE" ]]; then
                echo -e "  Scanning base image: ${BOLD}$BASE_IMAGE${NC} (from $dockerfile)"
                trivy image --severity HIGH,CRITICAL --format json --output "$RESULTS_DIR/trivy-image-$(echo "$BASE_IMAGE" | tr '/:' '_').json" "$BASE_IMAGE" 2>&1 || true
            fi
        fi
    done < <(find "$PROJECT_DIR" -name "Dockerfile" -o -name "*.dockerfile" | head -5)
    echo ""
fi

# ─── Phase 6: Deep Analysis (CodeQL) ─────────────────────────────────────────

if [[ -n "${RUN_LAYER[deep]:-}" ]] && command -v codeql &>/dev/null; then
    echo -e "${BOLD}${BLUE}━━━ Layer 6: Deep Analysis (CodeQL) ━━━${NC}"
    # Detect primary language
    LANG=$(python3 -c "
import os
counts = {}
for root, dirs, files in os.walk('$PROJECT_DIR'):
    dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'vendor', 'dist', 'build', '__pycache__', '.venv', 'venv']]
    for f in files:
        ext = os.path.splitext(f)[1]
        lang_map = {'.py':'python', '.js':'javascript', '.ts':'javascript', '.tsx':'javascript', '.jsx':'javascript',
                    '.go':'go', '.java':'java', '.rb':'ruby', '.c':'cpp', '.cpp':'cpp', '.h':'cpp',
                    '.rs':'rust', '.swift':'swift', '.kt':'java', '.scala':'java', '.cs':'csharp'}
        lang = lang_map.get(ext)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
if counts:
    print(max(counts, key=counts.get))
else:
    print('unknown')
" 2>/dev/null || echo "unknown")

    if [[ "$LANG" != "unknown" ]]; then
        echo -e "  Detected language: ${BOLD}$LANG${NC}"
        CODEQL_DB="/tmp/codeql-db-$$"
        echo -e "  Creating CodeQL database..."
        if codeql database create "$CODEQL_DB" --language="$LANG" --source-root="$PROJECT_DIR" --overwrite 2>&1; then
            echo -e "  Analyzing with security queries..."
            # Use the Security query pack for the detected language
            # Fall back to individual queries if the full pack fails
            CODEQL_QUERIES="codeql/${LANG}-queries:Security"
            echo -e "  Running CodeQL analysis with: ${BOLD}$CODEQL_QUERIES${NC}"
            if ! codeql database analyze "$CODEQL_DB" \
                --format=sarif-latest \
                --output "$RESULTS_DIR/codeql.sarif" \
                $CODEQL_QUERIES 2>&1; then
                echo -e "  ${YELLOW}Full Security pack failed, trying individual query suites...${NC}"
                # Resolve and run individual security queries
                CODEQL_QUERIES=$(codeql resolve queries "codeql/${LANG}-queries:Security" 2>/dev/null | tr '\n' ' ' || true)
                if [[ -n "$CODEQL_QUERIES" ]]; then
                    codeql database analyze "$CODEQL_DB" \
                        --format=sarif-latest \
                        --output "$RESULTS_DIR/codeql.sarif" \
                        $CODEQL_QUERIES 2>&1 || true
                else
                    echo -e "  ${YELLOW}Could not resolve any security queries. Skipping CodeQL analysis.${NC}"
                fi
            fi
            codeql database cleanup "$CODEQL_DB" 2>/dev/null || true
        else
            echo -e "  ${YELLOW}CodeQL database creation failed. Skipping analysis.${NC}"
        fi
    else
        echo -e "  ${YELLOW}No supported language detected. Skipping CodeQL.${NC}"
    fi
    echo ""
fi

# ─── Phase 7: Full Sweep (Horusec) ────────────────────────────────────────────

if [[ -n "${RUN_LAYER[sweep]:-}" ]] && command -v horusec &>/dev/null; then
    echo -e "${BOLD}${BLUE}━━━ Layer 7: Full Sweep (Horusec) ━━━${NC}"
    HORUSEC_CMD=(horusec start -p "$PROJECT_DIR" -t "$TIMEOUT" --output-format json --json-output-file "$RESULTS_DIR/horusec.json")
    if [[ -n "$SKIP_DIRS" ]]; then
        HORUSEC_CMD+=(-i "$SKIP_DIRS")
    fi
    # Load false-positive hashes from project config if available
    HORUSEC_FP_FILE="$PROJECT_DIR/.horusec-false-positives"
    if [[ -f "$HORUSEC_FP_FILE" ]]; then
        FP_HASHES=$(grep -v '^#' "$HORUSEC_FP_FILE" | grep -v '^$' | tr '\n' ',' | sed 's/,$//')
        if [[ -n "$FP_HASHES" ]]; then
            HORUSEC_CMD+=(-F "$FP_HASHES")
            echo -e "  Loaded ${BOLD}$(echo "$FP_HASHES" | tr ',' '\n' | wc -l | xargs)${NC} false-positive suppressions from .horusec-false-positives"
        fi
    fi
    "${HORUSEC_CMD[@]}" 2>&1 || true
    echo ""
fi

# ─── Results Summary ──────────────────────────────────────────────────────────

echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${CYAN}  Security Scan Complete${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Count findings per tool
LEAK_COUNT=0
if [[ -f "$RESULTS_DIR/gitleaks.json" ]]; then
    LEAK_COUNT=$(python3 -c "
import json
try:
    data = json.load(open('$RESULTS_DIR/gitleaks.json'))
    print(len(data) if isinstance(data, list) else 0)
except: print(0)
" 2>/dev/null || echo 0)
fi

SEMGREP_COUNT=0
if [[ -f "$RESULTS_DIR/semgrep.json" ]]; then
    SEMGREP_COUNT=$(python3 -c "
import json
try:
    data = json.load(open('$RESULTS_DIR/semgrep.json'))
    print(len(data.get('results', [])))
except: print(0)
" 2>/dev/null || echo 0)
fi

TRIVY_COUNT=0
for f in "$RESULTS_DIR"/trivy-*.json; do
    if [[ -f "$f" ]]; then
        COUNT=$(python3 -c "
import json
try:
    data = json.load(open('$f'))
    total = 0
    for r in data.get('results', []):
        total += len(r.get('vulnerabilities') or [])
        total += len(r.get('misconfigurations') or [])
        total += len(r.get('secrets') or [])
    print(total)
except: print(0)
" 2>/dev/null || echo 0)
        TRIVY_COUNT=$((TRIVY_COUNT + COUNT))
    fi
done

CODEQL_COUNT=0
if [[ -f "$RESULTS_DIR/codeql.sarif" ]]; then
    CODEQL_COUNT=$(python3 -c "
import json
try:
    data = json.load(open('$RESULTS_DIR/codeql.sarif'))
    total = 0
    for run in data.get('runs', []):
        total += len(run.get('results', []))
    print(total)
except: print(0)
" 2>/dev/null || echo 0)
fi

HORUSEC_COUNT=0
if [[ -f "$RESULTS_DIR/horusec.json" ]]; then
    HORUSEC_COUNT=$(python3 -c "
import json
try:
    data = json.load(open('$RESULTS_DIR/horusec.json'))
    vulns = data.get('analysisVulnerabilities', [])
    # Count only actual vulnerabilities (not false positives or risk accepted)
    count = 0
    for v in vulns:
        info = v.get('vulnerabilities', {})
        if info.get('type', '') == 'Vulnerability':
            count += 1
    print(count)
except: print(0)
" 2>/dev/null || echo 0)
fi

echo -e "  Gitleaks (secrets):     ${BOLD}$LEAK_COUNT${NC} findings"
echo -e "  Semgrep (patterns):    ${BOLD}$SEMGREP_COUNT${NC} findings"
echo -e "  Trivy (deps/IaC/imgs): ${BOLD}$TRIVY_COUNT${NC} findings"
echo -e "  CodeQL (deep):          ${BOLD}$CODEQL_COUNT${NC} findings"
echo -e "  Horusec (sweep):        ${BOLD}$HORUSEC_COUNT${NC} findings"
echo ""

TOTAL=$((LEAK_COUNT + SEMGREP_COUNT + TRIVY_COUNT + CODEQL_COUNT + HORUSEC_COUNT))
echo -e "  ${BOLD}TOTAL FINDINGS: ${TOTAL}${NC}"
echo ""

# Critical actions
if [[ $LEAK_COUNT -gt 0 ]]; then
    echo -e "  ${RED}${BOLD}⚠️  CRITICAL: $LEAK_COUNT leaked secrets detected!${NC}"
    echo -e "  ${RED}   → Rotate ALL leaked credentials immediately${NC}"
    echo -e "  ${RED}   → Remove secrets from code, use environment variables${NC}"
    echo ""
fi

# Risk level
RISK_SCORE=$((LEAK_COUNT * 10 + SEMGREP_COUNT * 2 + TRIVY_COUNT * 2 + CODEQL_COUNT * 3 + HORUSEC_COUNT * 3))
if [[ $RISK_SCORE -gt 50 ]]; then
    RISK_LEVEL="🔴 CRITICAL"
elif [[ $RISK_SCORE -gt 20 ]]; then
    RISK_LEVEL="🟠 HIGH"
elif [[ $RISK_SCORE -gt 5 ]]; then
    RISK_LEVEL="🟡 MEDIUM"
else
    RISK_LEVEL="🟢 LOW"
fi

echo -e "  Risk Score: ${BOLD}$RISK_SCORE${NC} — $RISK_LEVEL"
echo ""
echo -e "  Results directory: ${BOLD}$RESULTS_DIR${NC}"
echo -e "  ${CYAN}═══════════════════════════════════════════════════════════${NC}"

# ─── CI Mode Exit ──────────────────────────────────────────────────────────────

if [[ "$CI_MODE" == true ]]; then
    if [[ $LEAK_COUNT -gt 0 || $TOTAL -gt 0 ]]; then
        echo -e "${RED}${BOLD}CI FAILED: Security findings detected${NC}"
        exit 1
    fi
    echo -e "${GREEN}${BOLD}CI PASSED: No security findings${NC}"
fi

exit 0
