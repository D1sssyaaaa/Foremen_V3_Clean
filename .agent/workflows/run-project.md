---
description: Запуск проекта СНАБ (backend, frontend, bot)
---

// turbo-all

## Запуск всего проекта

1. Остановить старые процессы Python:
```powershell
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
```

2. Запустить Backend (FastAPI на порту 8000):
```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

3. Запустить Frontend (React на порту 3000):
```powershell
cd frontend
npm run dev
```

4. Запустить Telegram Bot:
```powershell
cd backend
python -m app.bot.main
```

## Адреса сервисов
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
