#!/bin/bash
# Verify a vault-stored key by checking its length (bypasses terminal redaction)
# Usage: verify-key.sh KEY_NAME
# Example: verify-key.sh DEEPSEEK_API_KEY

set -e
source ~/.hermes/.env.local 2>/dev/null
export PATH="$HOME/.local/bin:$PATH"

KEY_NAME="${1:?Usage: verify-key.sh KEY_NAME}"

# Get from vault
VAL=$(hermes-vault get "$KEY_NAME" 2>/dev/null)

if [ ${#VAL} -le 3 ]; then
    echo "❌ $KEY_NAME: length=${#VAL} — looks like a placeholder ('$VAL')"
    exit 1
elif [ "$VAL" = "***" ]; then
    echo "❌ $KEY_NAME: value is '***' — placeholder, not real key"
    exit 1
else
    echo "✅ $KEY_NAME: length=${#VAL}, starts_with=${VAL:0:8}..."
    exit 0
fi
