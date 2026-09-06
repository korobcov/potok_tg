# Telegram Video Poster Bot

Production-ready асинхронный Telegram-бот на Python 3.11+, предназначенный для администраторов каналов. Бот принимает ссылки на видео (YouTube, VK, TikTok, Instagram, RuTube), извлекает метаданные (заголовок, превью) с помощью `yt-dlp` и позволяет опубликовать красивый пост в заданный Telegram-канал.

## 🚀 Технологический стек
- **Python 3.11+**
- **aiogram 3.x**
- **yt-dlp**
- **aiohttp**
- **pydantic-settings**
- **pytest & pytest-asyncio**
- **Docker & Docker Compose**
- **flake8**

## 📋 Перед началом

Понадобится Telegram-бот и его данные:

1. Создайте бота через [@BotFather](https://t.me/BotFather) и получите `BOT_TOKEN`.
2. Узнайте свой `ADMIN_ID` (числовой Telegram ID) через [@userinfobot](https://t.me/userinfobot) — можно указать несколько ID через запятую.
3. Добавьте бота **администратором** в свой канал и узнайте `CHANNEL_ID` (для приватных каналов он выглядит как `-100xxxxxxxxxx`).

Есть два способа запустить бота: **в Docker** (рекомендуется, ничего кроме Docker ставить не нужно) или **напрямую в WSL/Linux** (для разработки и отладки).

---

## 🐳 Вариант 1: Запуск в Docker (рекомендуется)

Подходит и для Windows (через Docker Desktop с WSL2-бэкендом), и для Linux/macOS — команды одинаковые.

### 1. Установите Docker

- **Windows**: установите [Docker Desktop](https://www.docker.com/products/docker-desktop/) и включите интеграцию с WSL2 (Settings → Resources → WSL Integration). Все команды ниже выполняются в терминале WSL (Ubuntu) или в PowerShell — одинаково.
- **Linux**: установите Docker Engine и плагин Compose по [официальной инструкции](https://docs.docker.com/engine/install/) для вашего дистрибутива.
- Проверьте, что всё установлено:
  ```bash
  docker --version
  docker compose version
  ```

### 2. Склонируйте репозиторий

```bash
git clone https://github.com/your-username/potok_tg.git
cd potok_tg
```

### 3. Настройте `.env`

```bash
cp .env.example .env
```

Откройте `.env` и укажите свои значения:

```dotenv
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyZ
ADMIN_ID=123456789,987654321
CHANNEL_ID=-1001234567890
```

### 4. Соберите и запустите контейнер

```bash
docker compose up -d --build
```

Бот скачает все зависимости (включая `ffmpeg`, который нужен `yt-dlp`) внутри образа — на хосте ничего дополнительно ставить не надо.

### 5. Полезные команды

```bash
# посмотреть логи в реальном времени
docker compose logs -f

# перезапустить бота (например, после правки .env)
docker compose restart

# остановить бота
docker compose down

# пересобрать образ после изменения кода/зависимостей
docker compose up -d --build
```

---

## 🐧 Вариант 2: Запуск напрямую в WSL (Ubuntu) или Linux

Подходит для разработки, отладки и запуска тестов без Docker.

### 1. Установите WSL (только для Windows)

Если WSL ещё не установлен, откройте PowerShell **от имени администратора** и выполните:

```powershell
wsl --install -d Ubuntu
```

Перезагрузите компьютер, дождитесь установки Ubuntu и создайте пользователя. Все дальнейшие команды выполняются **внутри WSL** (в терминале Ubuntu), а не в PowerShell.

Если WSL уже установлен, откройте Ubuntu из меню «Пуск» или командой:

```powershell
wsl
```

### 2. Установите системные зависимости

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git ffmpeg
```

> `ffmpeg` обязателен — без него `yt-dlp` не сможет корректно обрабатывать часть видео. Если в вашем дистрибутиве нет пакета `python3.11`, воспользуйтесь [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) или установите Python 3.11+ любым другим способом.

Проверьте версию Python:

```bash
python3.11 --version
```

### 3. Склонируйте репозиторий

```bash
git clone https://github.com/your-username/potok_tg.git
cd potok_tg
```

> Работайте с проектом из файловой системы Linux (`~/potok_tg`), а не из `/mnt/c/...` — так операции с файлами будут значительно быстрее.

### 4. Создайте виртуальное окружение и установите зависимости

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> Виртуальное окружение нужно активировать (`source .venv/bin/activate`) в каждой новой сессии терминала перед запуском бота, тестов или flake8.

### 5. Настройте `.env`

```bash
cp .env.example .env
nano .env   # или любой другой редактор
```

Укажите `BOT_TOKEN`, `ADMIN_ID` и `CHANNEL_ID`, как описано в разделе «Перед началом».

### 6. Запустите бота

```bash
python -m app.main
```

Бот начнёт опрашивать Telegram (long polling). Чтобы оставить его работать в фоне, используйте `tmux`/`screen` либо запускайте через Docker (Вариант 1).

---

## 🧪 Тестирование и линтинг

Выполняется одинаково что в WSL/Linux (с активированным `.venv`), что внутри контейнера:

```bash
pytest
```

Проверка стиля кода:

```bash
flake8 .
```

Запуск тестов внутри уже работающего Docker-контейнера:

```bash
docker compose exec bot pytest
```

## 🛠 Возможные проблемы

- **`ModuleNotFoundError` при запуске** — не активировано виртуальное окружение: выполните `source .venv/bin/activate`.
- **Бот не отвечает / `Unauthorized` от Telegram** — проверьте, что `BOT_TOKEN` в `.env` скопирован полностью и без пробелов.
- **Бот игнорирует сообщения** — убедитесь, что ваш `ADMIN_ID` указан верно (узнать свой ID можно через [@userinfobot](https://t.me/userinfobot)).
- **Не публикуется пост в канал** — бот должен быть добавлен в канал **администратором**, а `CHANNEL_ID` — соответствовать этому каналу (для приватных каналов начинается с `-100`).
- **Ошибки `yt-dlp` про отсутствующий ffmpeg** — при запуске вне Docker установите `ffmpeg` (`sudo apt install ffmpeg`); в Docker он уже включён в образ.
- **Docker Desktop не видит команды `docker` в WSL** — включите интеграцию: Docker Desktop → Settings → Resources → WSL Integration → включите нужный дистрибутив.

## 📜 Лицензия
Этот проект распространяется под лицензией [MIT](LICENSE).
