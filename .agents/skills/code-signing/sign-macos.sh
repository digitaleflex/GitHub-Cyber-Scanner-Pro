#!/bin/bash
# Hyperspace Technologies - macOS Code Signing Script
# Usage: sign-macos.sh <app-path> [bundle-id] [app-name]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <app-path> [bundle-id] [app-name]"
    echo ""
    echo "Arguments:"
    echo "  app-path      Path to .app bundle"
    echo "  bundle-id     Bundle identifier (default: ng.hyperspace.<app-name>)"
    echo "  app-name      Application name for Info.plist (default: from bundle)"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/MyApp.app"
    echo "  $0 /path/to/MyApp.app ng.hyperspace.myapp \"My Application\""
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

APP_PATH="$1"

# Validate app path
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}Error: App bundle not found: $APP_PATH${NC}"
    exit 1
fi

if [[ ! "$APP_PATH" =~ \.app$ ]]; then
    echo -e "${RED}Error: Path must be a .app bundle${NC}"
    exit 1
fi

# Get app name from bundle
PLIST_PATH="$APP_PATH/Contents/Info.plist"
if [ -f "$PLIST_PATH" ]; then
    DEFAULT_NAME=$(/usr/libexec/PlistBuddy -c "Print :CFBundleName" "$PLIST_PATH" 2>/dev/null || basename "${APP_PATH%.app}")
    DEFAULT_ID=$(/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$PLIST_PATH" 2>/dev/null || echo "")
else
    DEFAULT_NAME=$(basename "${APP_PATH%.app}")
    DEFAULT_ID=""
fi

# Set bundle ID and app name
if [ -n "$2" ] && [ "$2" != "--" ]; then
    BUNDLE_ID="$2"
else
    BUNDLE_ID="${DEFAULT_ID:-ng.hyperspace.$(echo "$DEFAULT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')}"
fi

APP_NAME="${3:-$DEFAULT_NAME}"

echo -e "${GREEN}Signing macOS App: $APP_PATH${NC}"
echo "  Bundle ID: $BUNDLE_ID"
echo "  App Name: $APP_NAME"

# Remove extended attributes (quarantine, resource forks)
echo ""
echo "Removing extended attributes..."
xattr -cr "$APP_PATH" 2>/dev/null || true

# Update Info.plist
if [ -f "$PLIST_PATH" ]; then
    echo "Updating Info.plist..."
    
    # Update copyright
    /usr/libexec/PlistBuddy -c "Delete :NSHumanReadableCopyright" "$PLIST_PATH" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Add :NSHumanReadableCopyright string 'Copyright © 2024-2026 Hyperspace Technologies. All rights reserved.'" "$PLIST_PATH"
    
    # Update info string
    /usr/libexec/PlistBuddy -c "Delete :CFBundleGetInfoString" "$PLIST_PATH" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Add :CFBundleGetInfoString string '$APP_NAME - by Hyperspace Technologies'" "$PLIST_PATH"
    
    echo -e "${GREEN}✓ Info.plist updated${NC}"
fi

# Remove existing signature
echo ""
echo "Removing existing signature..."
codesign --remove-signature "$APP_PATH" 2>/dev/null || true

# Sign with ad-hoc signature
echo "Signing with ad-hoc signature..."
codesign --force --deep --sign - \
    --identifier "$BUNDLE_ID" \
    --timestamp=none \
    "$APP_PATH"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Signing successful${NC}"
else
    echo -e "${RED}✗ Signing failed${NC}"
    exit 1
fi

# Verify signature
echo ""
echo "Verification:"
if codesign --verify --deep --strict "$APP_PATH" 2>/dev/null; then
    echo -e "${GREEN}✓ Signature valid${NC}"
else
    echo -e "${RED}✗ Signature invalid${NC}"
    exit 1
fi

# Show signature details
echo ""
echo "Signature Details:"
codesign -dvvv "$APP_PATH" 2>&1 | grep -E "Identifier=|Signature=|Format=|TeamIdentifier=" | head -5
