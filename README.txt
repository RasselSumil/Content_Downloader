🧰 e621 + kemono.su Downloader
Author: Copilot

📁 Requirements:
- Python 3.10 or higher
- Optional: install dependencies → pip install requests tqdm

📦 Included Files:
- downloader.py              — main launcher
- downloader_e621.py         — module for downloading from e621.net
- downloader_kemono.py       — module for downloading from kemono.su (patreon, fanbox, etc.)
- lang_en.json / lang_ru.json — multilingual interface files

🌍 Multilanguage Support:
- On first launch, you choose your language (English / Russian)
- All prompts, menus, and messages are translated using JSON

✅ Features:
- Search by author or tag
- Cross-platform lookup (e621 + kemono)
- Fetches posts and downloads attachments
- Damaged file detection: skips and retries files under 10KB
- Logs all failures to skipped.log
- Clean summary after run (new, skipped, broken, etc.)
- Loop-back menu for continuous workflow

🧰 Загрузчик e621 + kemono.su
Автор: Copilot

📁 Установка:
- Python 3.10+
- Установить зависимости (опционально): pip install requests tqdm

📦 Файлы:
- downloader.py            — основной лаунчер
- downloader_e621.py       — модуль загрузки с e621.net
- downloader_kemono.py     — модуль загрузки с kemono.su (patreon, fanbox и т.д.)
- lang_ru.json / lang_en.json — мультиязычные строки

🌐 Поддержка языков:
- При запуске `downloader.py` спрашивает язык (русский / английский)
- Все подписи и меню подгружаются динамически

✅ Возможности:
- Поиск по автору или тегу
- Проверка платформ
- Скачивание постов и вложений
- Обработка повреждённых файлов (10 КБ+), повторная загрузка
- Лог ошибок (`skipped.log`)
- Возврат в главное меню после завершения