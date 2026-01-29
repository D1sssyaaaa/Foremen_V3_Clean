# Отчёт: WebSocket уведомления в реальном времени

**Дата:** 26 января 2026 г.  
**Модуль:** WebSocket — реальное время для веб-клиента

---

## ✅ Что сделано

### 1. ConnectionManager

**Файл:** `backend/app/websocket/manager.py`

**Основная функциональность:**
- Управление WebSocket подключениями
- Отправка персональных сообщений
- Broadcast по ролям
- Мульти-подключение (один пользователь = несколько вкладок)
- Автоматическое переподключение

**Ключевые методы:**

#### connect()
Подключение нового WebSocket клиента
- Принимает соединение
- Сохраняет метаданные (user_id, roles, timestamp)
- Отправляет приветственное сообщение

#### disconnect()
Отключение клиента
- Удаляет из активных подключений
- Очищает метаданные
- Логирует отключение

#### send_personal_message()
Отправка сообщения конкретному пользователю
- Поддержка множественных подключений
- Автоматическая очистка мёртвых соединений

#### broadcast_to_roles()
Broadcast по ролям
- Фильтрация пользователей по ролям
- Отправка всем подходящим

#### get_stats()
Статистика подключений
- Количество пользователей онлайн
- Количество подключений на пользователя

---

### 2. WebSocket Router

**Файл:** `backend/app/websocket/router.py`

#### WebSocket endpoint: /api/v1/ws

**URL:** `ws://localhost:8000/api/v1/ws?token=YOUR_JWT_TOKEN`

**Аутентификация:**
- JWT токен в query параметре
- Проверка активности пользователя
- Автоматическое закрытие при ошибке

**Типы сообщений от сервера:**
- `connection_established` — соединение установлено
- `notification` — новое уведомление
- `budget_alert_80` — бюджет на 80%
- `budget_alert_100` — бюджет превышен
- `comment_added` — новый комментарий
- `ping`/`pong` — heartbeat
- `error` — ошибка

**Типы сообщений от клиента:**
- `ping` — heartbeat (ответ: `pong`)
- `subscribe` — подписка на события

---

#### GET /api/v1/ws/stats

**Назначение:** статистика WebSocket подключений

**Доступ:** ADMIN, MANAGER

**Ответ:**
```json
{
  "status": "ok",
  "stats": {
    "total_users": 5,
    "total_connections": 7,
    "active_users": [1, 3, 5, 7, 10],
    "connections_per_user": {
      "1": 2,
      "3": 1,
      "5": 2,
      "7": 1,
      "10": 1
    }
  }
}
```

---

### 3. NotificationService расширен

**Файл:** `backend/app/notifications/service.py`

**Новые методы:**

#### send_websocket_notification()
Отправка уведомления одному пользователю через WebSocket

**Структура сообщения:**
```json
{
  "type": "notification",
  "notification_type": "budget_alert_80",
  "title": "⚠️ Бюджет объекта на 80%",
  "message": "Объект 'Строительство дома' израсходовал 82.5% бюджета",
  "data": {
    "object_id": 3,
    "object_name": "Строительство дома",
    "percentage": 82.5,
    "spent": 825000.0,
    "budget": 1000000.0
  },
  "timestamp": "2026-01-26T22:00:00"
}
```

---

#### broadcast_websocket_to_roles()
Broadcast уведомления пользователям с определёнными ролями

**Пример:**
```python
await notif_service.broadcast_websocket_to_roles(
    roles=["MANAGER", "ACCOUNTANT"],
    notification_type="budget_alert_100",
    title="🚨 Бюджет превышен!",
    message="Объект 'Дом №5' превысил бюджет на 15%",
    data={...}
)
```

---

#### notify_user() — универсальный метод
Единая точка отправки уведомлений:
- ✅ Сохранение в БД
- ✅ WebSocket (если пользователь онлайн)
- ✅ Telegram (если настроен)

**Параметры:**
- `send_websocket` — отправить через WebSocket (по умолчанию True)
- `send_telegram` — отправить в Telegram (по умолчанию True)

---

### 4. Интеграция с модулями

#### Бюджеты объектов (ObjectService)

**Файл:** `backend/app/services/object_service.py`

**Метод:** `check_budget_alerts()`

**Логика:**
1. Расчёт процента использования бюджета
2. При ≥80% → broadcast MANAGER + ACCOUNTANT
3. При ≥100% → broadcast MANAGER + ACCOUNTANT (критично)
4. Флаги предотвращают повторную отправку

**Уведомления:**
```json
// 80%
{
  "type": "notification",
  "notification_type": "budget_alert_80",
  "title": "⚠️ Бюджет объекта на 80%",
  "message": "Объект 'Строительство дома' израсходовал 82.5% бюджета (825,000 из 1,000,000 ₽)",
  "data": {
    "object_id": 3,
    "percentage": 82.5,
    ...
  }
}

// 100%
{
  "type": "notification",
  "notification_type": "budget_alert_100",
  "title": "🚨 Бюджет объекта превышен!",
  "message": "Объект 'Строительство дома' превысил бюджет: 105.3% (1,053,000 из 1,000,000 ₽)",
  "data": {
    "object_id": 3,
    "percentage": 105.3,
    ...
  }
}
```

---

#### Комментарии к табелям (TimeSheetService)

**Файл:** `backend/app/time_sheets/service.py`

**Метод:** `add_comment()`

**Логика:**
1. HR-менеджер добавляет комментарий к табелю
2. Отправка WebSocket уведомления бригадиру
3. Дублирование в Telegram (если настроен)

**Уведомление:**
```json
{
  "type": "notification",
  "notification_type": "timesheet_comment",
  "title": "💬 Новый комментарий к табелю",
  "message": "HR-менеджер оставил комментарий к табелю #42",
  "data": {
    "timesheet_id": 42,
    "comment_id": 15,
    "comment_type": "HR_CORRECTION",
    "text": "Исправьте часы за 15 января"
  }
}
```

---

## 🔄 Жизненный цикл WebSocket соединения

```
1. Клиент подключается
   ↓
   ws://localhost:8000/api/v1/ws?token=JWT_TOKEN
   
2. Сервер аутентифицирует
   ↓
   - Проверка JWT
   - Загрузка пользователя из БД
   - Проверка is_active
   
3. Соединение установлено
   ↓
   ConnectionManager.connect()
   → Отправка приветственного сообщения
   
4. Клиент слушает события
   ↓
   ws.onmessage = (event) => {
     const data = JSON.parse(event.data);
     // Обработка уведомления
   }
   
5. Сервер отправляет уведомления
   ↓
   - При бюджетных алертах
   - При новых комментариях
   - При смене статусов
   - При новых УПД
   
6. Heartbeat (опционально)
   ↓
   Клиент: {"type": "ping", "timestamp": ...}
   Сервер: {"type": "pong", "timestamp": ...}
   
7. Отключение
   ↓
   ConnectionManager.disconnect()
```

---

## 💻 Примеры использования

### JavaScript клиент

```javascript
// Подключение к WebSocket
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws?token=${token}`);

// Обработка подключения
ws.onopen = () => {
  console.log('✅ WebSocket connected');
};

// Обработка сообщений
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'connection_established':
      console.log('Connected as user', data.user_id);
      break;
    
    case 'notification':
      showNotification(data.title, data.message);
      playSound();
      break;
    
    case 'budget_alert_80':
      showWarning(data.title, data.message);
      updateBudgetIndicator(data.data.object_id, data.data.percentage);
      break;
    
    case 'budget_alert_100':
      showCriticalAlert(data.title, data.message);
      break;
    
    case 'comment_added':
      refreshComments(data.data.timesheet_id);
      break;
    
    case 'pong':
      console.log('Heartbeat OK');
      break;
  }
};

// Обработка ошибок
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Обработка закрытия
ws.onclose = (event) => {
  console.log('WebSocket closed. Reconnecting in 5s...');
  setTimeout(() => connectWebSocket(), 5000);
};

// Heartbeat каждые 30 секунд
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'ping',
      timestamp: new Date().toISOString()
    }));
  }
}, 30000);
```

---

### React Hook (useWebSocket)

```typescript
import { useEffect, useState, useRef } from 'react';

interface WebSocketMessage {
  type: string;
  notification_type?: string;
  title?: string;
  message?: string;
  data?: any;
  timestamp?: string;
}

export function useWebSocket(token: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    if (!token) return;
    
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws?token=${token}`);
    wsRef.current = ws;
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('✅ WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLastMessage(data);
      
      // Обработка уведомлений
      if (data.type === 'notification') {
        // Показать уведомление
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification(data.title, {
            body: data.message,
            icon: '/logo.png'
          });
        }
      }
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket closed. Reconnecting...');
      // Переподключение через 5 секунд
      setTimeout(() => {
        // Реконнект
      }, 5000);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      ws.close();
    };
  }, [token]);
  
  return { isConnected, lastMessage, ws: wsRef.current };
}
```

---

### Python клиент (для тестирования)

```python
import asyncio
import websockets
import json

async def connect_websocket(token: str):
    uri = f"ws://localhost:8000/api/v1/ws?token={token}"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket")
        
        # Получение сообщений
        async for message in websocket:
            data = json.loads(message)
            print(f"📩 Received: {data['type']}")
            
            if data['type'] == 'notification':
                print(f"  Title: {data['title']}")
                print(f"  Message: {data['message']}")
            
            elif data['type'] == 'connection_established':
                print(f"  User ID: {data['user_id']}")
                
                # Отправка ping
                await websocket.send(json.dumps({
                    "type": "ping",
                    "timestamp": "2026-01-26T22:00:00"
                }))

# Запуск
token = "YOUR_JWT_TOKEN"
asyncio.run(connect_websocket(token))
```

---

## 🎯 Сценарии использования

### Сценарий 1: Превышение бюджета

```
1. Бухгалтер добавляет новую материальную затрату
   ↓
   POST /api/v1/material-costs/distribute
   
2. Сервер вызывает check_budget_alerts()
   ↓
   spent = 850,000 ₽
   budget = 1,000,000 ₽
   percentage = 85%
   
3. percentage >= 80% → отправка уведомления
   ↓
   broadcast_websocket_to_roles([MANAGER, ACCOUNTANT])
   
4. Все MANAGER и ACCOUNTANT онлайн получают уведомление
   ↓
   {
     "type": "notification",
     "notification_type": "budget_alert_80",
     "title": "⚠️ Бюджет объекта на 80%",
     ...
   }
   
5. Frontend показывает всплывающее уведомление
   ↓
   - Toast notification
   - Звуковой сигнал
   - Обновление индикатора бюджета
```

---

### Сценарий 2: Комментарий HR к табелю

```
1. HR-менеджер оставляет комментарий
   ↓
   POST /api/v1/time-sheets/42/comments
   
2. Сервер вызывает add_comment()
   ↓
   - Сохранение в time_sheet_comments
   - send_websocket_notification()
   
3. Бригадир онлайн получает уведомление
   ↓
   {
     "type": "notification",
     "notification_type": "timesheet_comment",
     "title": "💬 Новый комментарий к табелю",
     ...
   }
   
4. Frontend показывает уведомление
   ↓
   - Badge на иконке табелей
   - Всплывающее уведомление
   - Переход к табелю (опционально)
```

---

## 🔒 Безопасность

### Аутентификация
- ✅ JWT токен обязателен
- ✅ Проверка активности пользователя
- ✅ Автоматическое закрытие при неверном токене

### Изоляция
- ✅ Пользователь получает только свои сообщения
- ✅ Broadcast фильтруется по ролям
- ✅ Нет доступа к чужим данным

### Защита от переполнения
- ✅ Автоматическая очистка мёртвых соединений
- ✅ Heartbeat для проверки активности

---

## 📊 Мониторинг

### Статистика в реальном времени

```bash
# Получение статистики
curl http://localhost:8000/api/v1/ws/stats \
  -H "Authorization: Bearer <token>"

# Ответ:
{
  "status": "ok",
  "stats": {
    "total_users": 8,
    "total_connections": 12,
    "active_users": [1, 3, 5, 7, 10, 12, 15, 20],
    "connections_per_user": {
      "1": 2,  # 2 вкладки
      "3": 1,
      "5": 3,  # 3 вкладки
      ...
    }
  }
}
```

### Логирование

Все события логируются:
```
INFO - WebSocket connected: user_id=5, total=1
INFO - Message sent to user 5: budget_alert_80
INFO - Broadcast to roles ['MANAGER', 'ACCOUNTANT']: 3 users
INFO - WebSocket disconnected: user_id=5
```

---

## ✨ Итоги

**Добавлено:**
- ✅ ConnectionManager (200 строк)
- ✅ WebSocket router с JWT аутентификацией
- ✅ 3 новых метода в NotificationService
- ✅ Интеграция с бюджетами объектов
- ✅ Интеграция с комментариями табелей
- ✅ Endpoint /ws/stats для мониторинга
- ✅ Поддержка множественных подключений
- ✅ Автоматическое переподключение

**Файлы:**
- `app/websocket/manager.py` — новый
- `app/websocket/router.py` — новый
- `app/websocket/__init__.py` — новый
- `app/notifications/service.py` — обновлён
- `app/services/object_service.py` — обновлён
- `app/time_sheets/service.py` — обновлён
- `app/auth/dependencies.py` — обновлён
- `main.py` — подключён WebSocket router

**Строк кода:** ~500 новых строк

---

## 🚀 Что дальше?

**Готово к реализации:**

1. **Расширение уведомлений** 📢
   - Смена статуса объекта
   - Новые УПД
   - Утверждение/отклонение табелей
   - Новые заявки на технику/материалы

2. **Telegram бот интеграция** 🤖
   - Двунаправленная связь
   - Управление через бот
   - Дублирование WebSocket уведомлений

3. **Frontend Dashboard** 📊
   - Real-time индикаторы
   - Бюджет progress bar
   - Live feed уведомлений

**Сервер:** ✅ http://127.0.0.1:8000  
**WebSocket:** ✅ ws://127.0.0.1:8000/api/v1/ws  
**Swagger UI:** http://127.0.0.1:8000/docs
