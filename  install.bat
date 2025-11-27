@echo off
echo [*] Creando entorno virtual...
python -m venv venv

echo [*] Activando entorno virtual...
call venv\Scripts\activate

echo [*] Actualizando pip...
python -m pip install --upgrade pip

echo [*] Instalando dependencias desde requirements.txt...
pip install -r requirements.txt

echo [*] Instalacion completada.
echo Para ejecutar la app:
echo   venv\Scripts\activate
echo   python main.py
pause
