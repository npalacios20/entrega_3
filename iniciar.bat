
@echo off
cd /d "%~dp0"

echo Verificando dependencias...
python -m pip install -r requirements.txt

echo.
echo Iniciando CMN InverGest...
python main.py

if errorlevel 1 (
    echo.
    echo No se pudo iniciar CMN InverGest.
    pause
)
.