#!/bin/bash
# Локальный скрипт для сборки macOS приложения

echo "========================================"
echo "Voice Translator Build Script (macOS)"
echo "========================================"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found! Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✓ Activating virtual environment"
    source venv/bin/activate
fi

# Установка PyInstaller
echo ""
echo "Installing PyInstaller..."
pip install pyinstaller

# Проверка ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo ""
    echo "⚠️  WARNING: ffmpeg not found!"
    echo "The built application will require ffmpeg to be installed."
    echo "Install it with: brew install ffmpeg"
    echo ""
    read -p "Press enter to continue..."
fi

# Очистка предыдущих сборок
if [ -d "build" ]; then
    echo "Cleaning previous build..."
    rm -rf build
fi
if [ -d "dist" ]; then
    rm -rf dist
fi

# Сборка
echo ""
echo "========================================"
echo "Building executable..."
echo "This may take 5-10 minutes"
echo "========================================"
echo ""

if [ -f "VoiceTranslator.spec" ]; then
    echo "Using VoiceTranslator.spec"
    pyinstaller VoiceTranslator.spec
else
    echo "Using default configuration"
    pyinstaller --name="VoiceTranslator" \
      --windowed \
      --onefile \
      --add-data "config.py:." \
      --hidden-import="PyQt6" \
      --hidden-import="faster_whisper" \
      --hidden-import="transformers" \
      --hidden-import="TTS" \
      --collect-all="TTS" \
      --collect-all="transformers" \
      --collect-all="faster_whisper" \
      main.py
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Build failed! Check errors above."
    exit 1
fi

# Создание релизной папки
echo ""
echo "Creating release package..."
mkdir -p release
cp dist/VoiceTranslator release/
cp README.md release/
cp QUICKSTART.md release/
cat > release/FIRST_RUN.txt << EOF
Models will be downloaded on first run (approx. 7-8 GB).
Ensure ffmpeg is installed: brew install ffmpeg

To run: ./VoiceTranslator
EOF

chmod +x release/VoiceTranslator

echo ""
echo "========================================"
echo "✓ Build completed successfully!"
echo "========================================"
echo ""
echo "Executable location: release/VoiceTranslator"
echo ""
echo "You can now:"
echo "1. Test the executable: ./release/VoiceTranslator"
echo "2. Distribute the 'release' folder"
echo ""
echo "Note: First run will download models (~7-8 GB)"
echo ""

open release

echo "Done!"
