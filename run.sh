#!/bin/bash

# Скрипт для быстрого запуска приложения (macOS/Linux)

echo "🚀 Starting Voice-to-Voice Translator..."

# Активация виртуального окружения
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Проверка установки зависимостей
if ! python -c "import PyQt6" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing..."
    pip install -r requirements.txt
fi

# Запуск приложения
echo "✓ Launching application..."
python main.py

echo "👋 Application closed."
