#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Setup မလုပ်ရသေးပါ။ အရင် bash android-setup.sh ကို run လုပ်ပါ။"
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate
termux-wake-lock >/dev/null 2>&1 || true
trap 'termux-wake-unlock >/dev/null 2>&1 || true' EXIT INT TERM
echo "PROOF V3 Local Server စတင်နေသည်။"
echo "Chrome မှ http://127.0.0.1:8000 ကိုဖွင့်ပါ။"
echo "ရပ်ရန် Termux ထဲတွင် Ctrl+C နှိပ်ပါ။"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
