## Бот домашних заданий (Telethon)

Требования: Python 3.10+

### Установка

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell
pip install -r requirements.txt
copy env.example .env
# заполните .env значениями API_ID, API_HASH, BOT_TOKEN
```

### Запуск

```bash
python -m src.main
```

### Переменные окружения
- API_ID, API_HASH, BOT_TOKEN: токены Telegram (бот через @BotFather)
- ADMIN_WHITELIST: список Telegram user_id через запятую, кто видит /admin_menu
- SUBJECTS_FILE: путь к subjects.json
- TIMEZONE: таймзона для расчёта «завтра», по умолчанию Asia/Yekaterinburg
- HW_RETENTION_DAYS: сколько дней хранить ДЗ после даты (0 — удалить на следующий день)

### Функционал
- /start — подписывает пользователя на уведомления и открывает меню
- Пользователь: все ДЗ, на завтра, по дате, по предмету
- Админ (/admin_menu): добавить ДЗ (пошагово) и рассылка всем
- Авто-очистка: ДЗ удаляются после истечения срока (например, ДЗ до 10.10 удалится 11.10)

### Структура
```
src/
  main.py
  config.py
  db.py
  keyboards.py
  utils/
    dates.py
  repositories/
    users.py
    homeworks.py
    whitelist.py
subjects.json
```
