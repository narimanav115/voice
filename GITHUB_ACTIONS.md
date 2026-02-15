# GitHub Actions - Автоматическая сборка

## Как работает

GitHub Actions автоматически соберет приложение при:

1. **Push в ветку main/master** - создаст артефакты для скачивания
2. **Pull Request** - проверит, что сборка проходит
3. **Создание тега** (например, `v1.0.0`) - создаст GitHub Release
4. **Ручной запуск** через вкладку Actions на GitHub

## Что происходит при сборке

### Windows сборка:
1. ✅ Запускается Windows Server (GitHub-hosted runner)
2. ✅ Устанавливается Python 3.10
3. ✅ Устанавливается FFmpeg через Chocolatey
4. ✅ Кэшируются pip пакеты (ускоряет повторные сборки)
5. ✅ Устанавливаются все зависимости из requirements.txt
6. ✅ PyInstaller собирает `VoiceTranslator.exe` (~500-800 MB)
7. ✅ Создается ZIP архив с EXE, README и инструкциями
8. ✅ Артефакт загружается на GitHub (доступен 90 дней)

### macOS сборка:
Аналогично, но:
- Использует macOS runner
- FFmpeg устанавливается через Homebrew
- Создается macOS исполняемый файл

## Файлы конфигурации

### `.github/workflows/build-windows.yml`
- Сборка только для Windows
- Используется для тестирования Windows-специфичных изменений

### `.github/workflows/build-all.yml`
- Сборка для Windows И macOS одновременно
- При создании тега создает GitHub Release с обеими версиями

## Как использовать

### Способ 1: Автоматически при push

```bash
git add .
git commit -m "Update application"
git push origin main
```

Через ~10-20 минут артефакты появятся в разделе Actions

### Способ 2: Создать релиз

```bash
# Создать tag
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions автоматически:
- Соберет приложения для Windows и macOS
- Создаст GitHub Release
- Приложит ZIP файлы к релизу

### Способ 3: Ручной запуск

1. Перейдите на GitHub в раздел **Actions**
2. Выберите workflow `Build Windows Application` или `Build Multi-Platform`
3. Нажмите **Run workflow**
4. Выберите ветку и нажмите **Run workflow**

## Скачивание результатов

### После обычной сборки:
1. Перейдите в **Actions**
2. Выберите нужный workflow run
3. Scroll вниз до секции **Artifacts**
4. Скачайте `VoiceTranslator-Windows-x64.zip` или `VoiceTranslator-macOS.zip`

### После создания тега:
1. Перейдите в **Releases**
2. Найдите свой release (например, `v1.0.0`)
3. Скачайте нужный ZIP из Assets

## Важные замечания

### ⚠️ Размер исполняемого файла
- Windows EXE: ~500-800 MB (включает Python + все библиотеки)
- macOS: ~600-900 MB
- Это нормально для приложений с ML-моделями

### ⚠️ Модели НЕ включены
- Исполняемый файл НЕ содержит ML модели (~7-8 GB)
- Модели скачиваются при первом запуске приложения
- Пользователю нужен интернет только для первого запуска

### ⚠️ Время сборки
- Windows: ~10-15 минут
- macOS: ~12-18 минут
- Оба вместе: ~20-25 минут

### ⚠️ GitHub Actions лимиты (Free tier)
- 2000 минут в месяц для приватных репозиториев
- Неограниченно для публичных репозиториев
- Windows: 1 минута = 2 минуты лимита
- macOS: 1 минута = 10 минут лимита

## Локальная сборка

Если не хотите использовать GitHub Actions:

### Windows:
```cmd
build.bat
```

### macOS/Linux:
```bash
chmod +x build.sh
./build.sh
```

## Настройка

### Изменить версию Python:
В `.github/workflows/build-windows.yml`:
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.10'  # Измените здесь
```

### Добавить иконку:
1. Создайте `icon.ico` в корне проекта
2. Раскомментируйте в `VoiceTranslator.spec`:
```python
icon='icon.ico'  # вместо icon=None
```

### Изменить имя приложения:
В workflow файлах замените `VoiceTranslator` на нужное имя

## Проверка статуса

Добавьте badge в README.md:

```markdown
![Build Status](https://github.com/ваш-username/voicechanger/workflows/Build%20Windows%20Application/badge.svg)
```

## Troubleshooting

### Сборка падает с ошибкой памяти
Увеличьте swap в build скрипте или используйте `--onedir` вместо `--onefile`

### Не хватает зависимостей
Добавьте в `--hidden-import` или `--collect-all` в PyInstaller команде

### Приложение не запускается
Проверьте логи в `logs/app.log` после запуска

## Рекомендации

1. **Тестируйте локально** перед push
2. **Используйте tags** для релизов (v1.0.0, v1.0.1, etc.)
3. **Кэш работает** - повторные сборки быстрее
4. **Проверяйте size** - если EXE > 1GB, что-то не так

## Что дальше?

После успешной сборки:
1. Скачайте артефакт
2. Распакуйте ZIP
3. Протестируйте `VoiceTranslator.exe`
4. Распространяйте пользователям
5. Пользователи запускают, модели скачиваются автоматически

---

**Примечание**: Первая сборка займет больше времени. Последующие будут быстрее благодаря кэшированию.
