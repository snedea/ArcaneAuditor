#!/usr/bin/env bash
set -euo pipefail

# 🧙 Arcane Auditor Notarization Helper (apps, DMGs, and standalone binaries)
# Works with Apple ID + App-Specific Password authentication.

APP_PATH="$1"
LOG_DIR="./notary-logs"
mkdir -p "$LOG_DIR"

timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/notarization_${timestamp}.log"

echo "🪶 Starting notarization for: $APP_PATH"
echo "📋 Logging to: $LOG_FILE"

if [[ -z "${APPLE_ID:-}" || -z "${APPLE_APP_SPECIFIC_PASSWORD:-}" || -z "${APPLE_TEAM_ID:-}" ]]; then
  echo "❌ Missing notarization environment variables."
  echo "   Expected: APPLE_ID, APPLE_APP_SPECIFIC_PASSWORD, APPLE_TEAM_ID"
  exit 1
fi

if [[ ! -e "$APP_PATH" ]]; then
  echo "❌ File not found: $APP_PATH"
  exit 1
fi

# --- Handle non-app/dmg binaries (CLI etc.) ---
ZIP_PATH=""
if [[ "$APP_PATH" != *.app && "$APP_PATH" != *.dmg && "$APP_PATH" != *.zip ]]; then
  echo "📦 Detected standalone binary. Zipping for notarization..."
  ZIP_PATH="${APP_PATH}.zip"
  /usr/bin/ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"
elif [[ "$APP_PATH" == *.zip ]]; then
  ZIP_PATH="$APP_PATH"
else
  ZIP_PATH="${APP_PATH}.zip"
  echo "📦 Compressing $APP_PATH for notarization..."
  /usr/bin/ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"
fi

echo "🚀 Submitting to Apple notarization service..."
xcrun notarytool submit "$ZIP_PATH" \
  --apple-id "$APPLE_ID" \
  --password "$APPLE_APP_SPECIFIC_PASSWORD" \
  --team-id "$APPLE_TEAM_ID" \
  --output-format json > "$LOG_FILE" 2>&1

SUBMISSION_ID=$(grep -Eo '"id"[[:space:]]*:[[:space:]]*"[^"]+"' "$LOG_FILE" | cut -d '"' -f 4 || true)
echo "🪪 Submission ID: $SUBMISSION_ID"

if [[ -z "$SUBMISSION_ID" ]]; then
  echo "❌ Failed to obtain submission ID. See $LOG_FILE for details."
  exit 1
fi

# Poll for up to 60 minutes
for i in {1..60}; do
  STATUS=$(xcrun notarytool info "$SUBMISSION_ID" \
    --apple-id "$APPLE_ID" \
    --password "$APPLE_APP_SPECIFIC_PASSWORD" \
    --team-id "$APPLE_TEAM_ID" \
    --output-format json 2>>"$LOG_FILE" | jq -r '.status' || echo "error")
  echo "⏳ [$i/60] Status: $STATUS"
  if [[ "$STATUS" == "Accepted" ]]; then
    echo "✅ Notarization accepted!"
    break
  elif [[ "$STATUS" == "Invalid" ]]; then
    echo "❌ Notarization failed. Fetching detailed log..."
    xcrun notarytool log "$SUBMISSION_ID" \
      --apple-id "$APPLE_ID" \
      --password "$APPLE_APP_SPECIFIC_PASSWORD" \
      --team-id "$APPLE_TEAM_ID" \
      --output-format json > "$LOG_DIR/log_${timestamp}.json" 2>>"$LOG_FILE"
    echo "📄 Saved Apple failure log to: $LOG_DIR/log_${timestamp}.json"
    exit 1
  fi
  sleep 60
done

# --- Staple ticket ---
if [[ "$APP_PATH" == *.app || "$APP_PATH" == *.dmg ]]; then
  echo "🔏 Stapling ticket to bundle..."
  xcrun stapler staple -v "$APP_PATH" 2>&1 | tee -a "$LOG_FILE"
elif [[ "$APP_PATH" == *.zip ]]; then
  echo "📦 Skipping staple for ZIP container (cannot be stapled)."
else
  echo "📦 Skipping staple for standalone binaries (not applicable)."
fi

echo "🎉 Notarization complete!"

# --- Log environment for traceability ---
{
  echo "🧾 Runner environment snapshot:"
  echo "GITHUB_RUN_ID=${GITHUB_RUN_ID:-N/A}"
  echo "RUNNER_OS=${RUNNER_OS:-N/A}"
  echo "RUNNER_TEMP=${RUNNER_TEMP:-N/A}"
  echo "ENDPOINT: appstoreconnect.apple.com"
} >> "$LOG_FILE"

# --- GitHub Actions artifact notice ---
if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
  echo "📤 Uploading notarization logs as artifact..."
  echo "::notice title=Notarization Logs::Logs saved to $LOG_FILE"
fi
