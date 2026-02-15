@echo off
REM Локальный скрипт для сборки Windows приложения

echo ========================================
echo Voice Translator Build Script (Windows)
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

echo ✓ Python found

REM Проверка виртуального окружения
if not exist "venv\" (
    echo ⚠️  Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    echo ✓ Activating virtual environment
    call venv\Scripts\activate.bat
)

REM Установка PyInstaller
echo.
echo Installing PyInstaller...
pip install pyinstaller

REM Проверка ffmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  WARNING: ffmpeg not found!
    echo The built application will require ffmpeg to be installed.
    echo Install it with: choco install ffmpeg
    echo.
    pause
)

REM Очистка предыдущих сборок
if exist "build\" (
    echo Cleaning previous build...
    rmdir /s /q build
)
if exist "dist\" (
    rmdir /s /q dist
)

REM Сборка
echo.
echo ========================================
echo Building executable...
echo This may take 5-10 minutes
echo ========================================
echo.

if exist "VoiceTranslator.spec" (
    echo Using VoiceTranslator.spec
    pyinstaller VoiceTranslator.spec
) else (
    echo Using default configuration
    pyinstaller --name="VoiceTranslator" ^
      --windowed ^
      --onedir ^
      --add-data "config.py;." ^
      --hidden-import="PyQt6" ^
      --hidden-import="faster_whisper" ^
      --hidden-import="transformers" ^
      --hidden-import="TTS" ^
      --collect-all="TTS" ^
      --collect-all="transformers" ^
      --collect-all="faster_whisper" ^
      --collect-all="torch" ^
      main.py
)

if errorlevel 1 (
    echo.
    echo ❌ Build failed! Check errors above.
    pause
    exit /b 1
)

REM Создание релизной папки
echo.
echo Creating release package...
mkdir release 2>nul
xcopy /E /I dist\VoiceTranslator release\VoiceTranslator
copy README.md release\
copy QUICKSTART.md release\
echo Models will be downloaded on first run (approx. 7-8 GB). > release\FIRST_RUN.txt
echo Ensure ffmpeg is installed: choco install ffmpeg >> release\FIRST_RUN.txt
echo. >> release\FIRST_RUN.txt
echo To run: Open VoiceTranslator folder and run VoiceTranslator.exe >> release\FIRST_RUN.txt

echo.
echo ========================================
echo ✓ Build completed successfully!
echo ========================================
echo.
echo Application location: release\VoiceTranslator\
echo Main executable: release\VoiceTranslator\VoiceTranslator.exe
echo.
echo You can now:
echo 1. Test the executable: release\VoiceTranslator\VoiceTranslator.exe
echo 2. Distribute the entire 'release' folder
echo.
echo Note: First run will download models (~7-8 GB)
echo.

explorer release

pause
