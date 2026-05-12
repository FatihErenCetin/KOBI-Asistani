#!/usr/bin/env bash
# Usage: bash scripts/set_telegram_webhook.sh https://xxx.ngrok-free.app
set -euo pipefail
PUBLIC_URL="${1:-}"
if [ -z "$PUBLIC_URL" ]; then
  echo "Usage: $0 <https-public-url>"
  exit 1
fi
# .env'i yukle
set -a
source .env
set +a

WEBHOOK_URL="$PUBLIC_URL/api/v1/webhooks/telegram"
echo "Setting webhook to: $WEBHOOK_URL"
curl -sS -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
     -H "Content-Type: application/json" \
     -d "{\"url\":\"$WEBHOOK_URL\",\"secret_token\":\"$TELEGRAM_WEBHOOK_SECRET\"}"
echo
