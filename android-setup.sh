#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v pkg >/dev/null 2>&1; then
  echo "ဒီ Setup ကို Termux app ထဲမှာပဲ run လုပ်ပါ။"
  exit 1
fi

echo "[1/5] Termux packages တင်နေသည်..."
pkg update -y
pkg install -y python python-pillow python-cryptography unzip

echo "[2/5] Python virtual environment ပြင်ဆင်နေသည်..."
if [ ! -d .venv ]; then
  python -m venv --system-site-packages .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip

echo "[3/5] Python dependencies တင်နေသည်..."
python -m pip install -r requirements-android.txt
# SQLAlchemy's synchronous SQLite usage does not require greenlet.
python -m pip install --no-deps 'SQLAlchemy>=2,<3'

echo "[4/5] Native Android libraries စစ်ဆေးနေသည်..."
python - <<'PY'
import PIL, cryptography, fastapi, pydantic, sqlalchemy, uvicorn
print('Pillow:', PIL.__version__)
print('cryptography:', cryptography.__version__)
print('FastAPI:', fastapi.__version__)
print('Pydantic:', pydantic.__version__)
print('SQLAlchemy:', sqlalchemy.__version__)
print('Uvicorn:', uvicorn.__version__)
PY

if [ ! -f .env ]; then
  cp .env.android .env
fi
python -m app.cli generate-secrets
mkdir -p data/evidence
chmod 700 data data/evidence 2>/dev/null || true

echo "[5/5] Setup ပြီးပါပြီ။"
echo "Admin account ဖန်တီးရန်:"
echo "  source .venv/bin/activate"
echo "  python -m app.cli create-admin --username admin --email admin@example.com"
echo "ပြီးလျှင် စတင်ရန်: bash android-start.sh"
