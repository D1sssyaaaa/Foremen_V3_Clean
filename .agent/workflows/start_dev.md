---
description: Запуск всего стека разработки (Docker + Backend + Frontend + Bot)
---

1. Запускаем инфраструктуру (БД, Redis, MinIO) в Docker
// turbo
```powershell
docker-compose up -d postgres redis minio
```

2. Запускаем Backend (FastAPI) в отдельном терминале
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python main.py"
```

3. Запускаем Telegram Bot в отдельном терминале
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\.venv\Scripts\Activate.ps1; python -m app.bot.main"
```

4. Запускаем Frontend (Vite) в отдельном терминале
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
```

5. Проверяем статус
```powershell
docker-compose ps
```
