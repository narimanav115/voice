# Команды для локального запуска

## Быстрый запуск (после установки зависимостей):

### Способ 1: Через скрипт (рекомендуется)
```bash
./run.sh
```

### Способ 2: Напрямую через Python
```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запустить приложение
python main.py
```

### Способ 3: Без активации окружения
```bash
venv/bin/python main.py
```

## Первый запуск

При первом запуске приложение автоматически скачает модели (~7-8 GB):
- Это займет 10-30 минут в зависимости от скорости интернета
- После этого приложение будет работать офлайн
- Модели сохраняются в папке `models/`

## Проверка установки

```bash
# Проверить, что PyQt6 установлен
source venv/bin/activate
python -c "import PyQt6; print('PyQt6 OK')"

# Проверить все основные зависимости
python -c "
import PyQt6
import torch
import transformers
import TTS
print('✓ All dependencies OK')
"
```

## Если что-то не работает

### Переустановить зависимости
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Проверить Python версию
```bash
python --version  # Должна быть 3.9+
```

### Проверить ffmpeg
```bash
ffmpeg -version  # Если не установлен: brew install ffmpeg
```

## После установки

Просто запустите:
```bash
./run.sh
```

Или:
```bash
python main.py
```

Откроется окно приложения с GUI интерфейсом.
