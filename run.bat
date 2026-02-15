@echo off
REM Скрипт для быстрого запуска приложения (Windows)

echo 🚀 Starting Voice-to-Voice Translator...

REM Активация виртуального окружения
if exist "venv\Scripts\activate.bat" (
    echo ✓ Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ❌ Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate.bat
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Проверка установки зависимостей
python -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo ⚠️  Dependencies not installed. Installing...
    pip install -r requirements.txt
)

REM Запуск приложения
echo ✓ Launching application...
python main.py

echo 👋 Application closed.
pause
