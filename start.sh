#!/usr/bin/env bash
# ==============================================================================
# DataViz - Buyuk Veri, AI Guven Skoru ve Istatistik Platformu
# TUBITAK 2209-A Destekli Yerel Veri Analiz Studyosu (Linux & macOS Baslatici)
# ==============================================================================

set -e

# Proje ana dizinine gec
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

echo ""
echo "========================================================================"
echo "  📊 DataViz - Buyuk Veri Analitigi ve Kalite Platformu"
echo "  TUBITAK 2209-A Destekli Yerel Veri Analiz Studyosu"
echo "========================================================================"
echo ""

# 1. Python Tespiti (3.10+)
PY_CMD=""
if command -v python3 &>/dev/null && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null && python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' &>/dev/null; then
    PY_CMD="python"
else
    echo "❌ HATA: Sisteminizde Python 3.10 veya daha yeni bir surum bulunamadi."
    echo "Lutfen Python 3.10+ yukleyip tekrar deneyin."
    exit 1
fi

echo "✅ [1/3] Python bulundu: $($PY_CMD --version)"

# 2. Sanal Ortam (.venv)
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "⚙️  [2/3] Sanal ortam olusturuluyor (.venv)..."
    $PY_CMD -m venv "$VENV_DIR"
fi

# Sanal ortami aktif et
source "$VENV_DIR/bin/activate"

# 3. Bagimliliklar
echo "📦 [3/3] Bagimliliklar kontrol ediliyor..."
if ! python -c "import flask, pandas, numpy, polars, pyarrow, scipy, sklearn, reportlab, pyreadstat" &>/dev/null; then
    echo "Gerekli paketler yukleniyor (requirements.txt)..."
    pip install --disable-pip-version-check --prefer-binary -r requirements.txt
    echo "✅ Paketler basariyla kuruldu."
else
    echo "✅ Tum paketler hazir."
fi

mkdir -p uploads

# 4. Port Kontrolu
PORT=5000
if [ -f ".env" ]; then
    ENV_PORT=$(grep -E '^PORT=' .env | cut -d '=' -f2 | tr -d ' "')
    if [ -n "$ENV_PORT" ]; then
        PORT="$ENV_PORT"
    fi
fi

# 5. Sunucuyu Baslat
echo ""
echo "========================================================================"
echo "  🚀 DataViz Platformu Baslatiliyor..."
echo "  Adres     : http://127.0.0.1:$PORT"
echo "  Durdurmak : Ctrl + C tuslarina basin"
echo "========================================================================"
echo ""

# Tarayicida otomatik ac (macOS open veya Linux xdg-open)
(sleep 2 && {
    if command -v xdg-open &>/dev/null; then
        xdg-open "http://127.0.0.1:$PORT" &>/dev/null &
    elif command -v open &>/dev/null; then
        open "http://127.0.0.1:$PORT" &>/dev/null &
    fi
}) &

python app.py
