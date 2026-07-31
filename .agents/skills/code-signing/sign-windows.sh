#!/bin/bash
# Hyperspace Technologies - Windows Code Signing Script
# Usage: sign-windows.sh <input-file> [app-name] [--replace]

set -e

# Certificate configuration
CERT_DIR="${HYPERSPACE_CERT_DIR:-$HOME/.config/opencode/certs/hyperspace}"
CERT_FILE="$CERT_DIR/hyperspace.pfx"
CERT_PASS="${HYPERSPACE_CERT_PASS:-hyperspace2024}"
PUBLISHER_URL="https://reactorpro.ng"
TIMESTAMP_SERVER="${TIMESTAMP_SERVER:-http://timestamp.digicert.com}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <input-file> [app-name] [--replace]"
    echo ""
    echo "Arguments:"
    echo "  input-file    Path to .exe, .dll, or .msi file"
    echo "  app-name      Application name (default: filename without extension)"
    echo "  --replace     Replace original file with signed version"
    echo ""
    echo "Environment Variables:"
    echo "  HYPERSPACE_CERT_DIR   Certificate directory (default: ~/.config/opencode/certs/hyperspace)"
    echo "  HYPERSPACE_CERT_PASS  Certificate password (default: hyperspace2024)"
    echo "  TIMESTAMP_SERVER      Timestamp server URL"
    echo ""
    echo "Examples:"
    echo "  $0 myapp.exe"
    echo "  $0 myapp.exe \"My Application\" --replace"
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

INPUT_FILE="$1"
APP_NAME="${2:-$(basename "${INPUT_FILE%.*}")}"
REPLACE=false

# Check for --replace flag
for arg in "$@"; do
    if [ "$arg" = "--replace" ]; then
        REPLACE=true
    fi
done

# Validate input file
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}Error: File not found: $INPUT_FILE${NC}"
    exit 1
fi

# Check file extension
EXT="${INPUT_FILE##*.}"
if [[ ! "$EXT" =~ ^(exe|dll|msi|EXE|DLL|MSI)$ ]]; then
    echo -e "${YELLOW}Warning: Unusual file extension: .$EXT${NC}"
fi

# Check certificate exists
if [ ! -f "$CERT_FILE" ]; then
    echo -e "${RED}Error: Certificate not found: $CERT_FILE${NC}"
    echo "Run the certificate setup first. See: ~/.config/opencode/skills/code-signing/skill.md"
    exit 1
fi

# Check osslsigncode is installed
if ! command -v osslsigncode &> /dev/null; then
    echo -e "${RED}Error: osslsigncode not found. Install with: brew install osslsigncode${NC}"
    exit 1
fi

# Generate output filename
DIRNAME=$(dirname "$INPUT_FILE")
BASENAME=$(basename "$INPUT_FILE")
FILENAME="${BASENAME%.*}"
OUTPUT_FILE="$DIRNAME/${FILENAME}-signed.${EXT}"

echo -e "${GREEN}Signing: $INPUT_FILE${NC}"
echo "  App Name: $APP_NAME"
echo "  Output: $OUTPUT_FILE"

# Sign the file
osslsigncode sign \
    -pkcs12 "$CERT_FILE" \
    -pass "$CERT_PASS" \
    -n "$APP_NAME" \
    -i "$PUBLISHER_URL" \
    -t "$TIMESTAMP_SERVER" \
    -h sha256 \
    -in "$INPUT_FILE" \
    -out "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Signing successful${NC}"
    
    # Replace original if requested
    if [ "$REPLACE" = true ]; then
        mv "$INPUT_FILE" "$DIRNAME/${FILENAME}-unsigned.${EXT}"
        mv "$OUTPUT_FILE" "$INPUT_FILE"
        echo -e "${GREEN}✓ Replaced original (backup: ${FILENAME}-unsigned.${EXT})${NC}"
        OUTPUT_FILE="$INPUT_FILE"
    fi
    
    # Verify
    echo ""
    echo "Verification:"
    osslsigncode verify "$OUTPUT_FILE" 2>&1 | grep -E "(Subject:|Timestamp time:)" | head -2
else
    echo -e "${RED}✗ Signing failed${NC}"
    exit 1
fi
