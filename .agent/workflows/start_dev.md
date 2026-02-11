---
description: Запуск всего стека разработки (Docker + Backend + Frontend + Bot)
---

1. Запускаем Базу Данных (PostgreSQL)
// Убедитесь, что служба PostgreSQL запущена локально

2. Запускаем Redis (если используется)
// Убедитесь, что служба Redis запущена локально (опционально)

3. Запускаем MinIO (если используется)
// Убедитесь, что служба MinIO запущена локально (опционально)

4. Запускаем Backend (FastAPI) в отдельном терминале
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install -r requirements.txt; python main.py"
```

5. Запускаем Telegram Bot в отдельном терминале
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\.venv\Scripts\Activate.ps1; python -m app.bot.main"
```

6. Запускаем Frontend (Vite) в отдельном терминале
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
```

