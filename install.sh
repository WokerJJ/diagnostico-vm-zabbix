#!/usr/bin/env bash
set -e

echo "[*] Creando entorno virtual..."
python3 -m venv venv

echo "[*] Activando entorno virtual..."
source venv/bin/activate

echo "[*] Actualizando pip..."
pip install --upgrade pip

echo "[*] Instalando dependencias desde requirements.txt..."
pip install -r requirements.txt

echo "[*] Instalación completada."
echo "Para ejecutar la app:"
echo "  source venv/bin/activate"
echo "  python main.py"
