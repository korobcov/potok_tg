# Telegram Video Poster Bot

Production-ready асинхронный Telegram-бот на Python 3.11+, предназначенный для администраторов каналов. Бот принимает ссылки на видео (YouTube, VK, TikTok, Instagram, RuTube), извлекает метаданные (заголовок, превью) с помощью `yt-dlp` и позволяет опубликовать красивый пост в заданный Telegram-канал.

## 🚀 Технологический стек
- **Python 3.11+**
- **aiogram 3.x**
- **yt-dlp**
- **pydantic-settings**
- **pytest & pytest-asyncio**
- **Docker & Docker Compose**
- **flake8**

## 📦 Быстрый запуск

### 1. Локальный запуск
1. Склонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/potok_tg.git
   cd potok_tg
   ```
2. Создайте и заполните `.env` файл на основе `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Укажите ваш `BOT_TOKEN`, `ADMIN_ID` (можно через запятую) и `CHANNEL_ID`.

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Запустите бота:
   ```bash
   python -m app.main
   ```

### 2. Запуск в Docker Compose
```bash
docker compose up -d --build
```

## 🧪 Тестирование и линтинг
Для запуска тестов:
```bash
pytest
```
Для проверки стиля кода:
```bash
flake8 .
```

## 📜 Лицензия
Этот проект распространяется под лицензией [MIT](LICENSE).
