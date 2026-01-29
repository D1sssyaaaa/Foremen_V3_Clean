# Быстрый старт - Система управления доступом к объектам

## Что это?

Система позволяет бригадирам запрашивать доступ к строительным объектам, а менеджерам одобрять или отклонять эти запросы.

## Для бригадира (FOREMAN)

### Запросить доступ к объекту

```bash
# 1. Получить токен
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "foreman",
    "password": "foreman123"
  }'

# Ответ содержит access_token

# 2. Запросить доступ к объекту
curl -X POST http://localhost:8000/api/v1/objects/1/request-access \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Назначен ответственным за электромонтажные работы"
  }'
```

### Увидеть свои запросы

```bash
curl http://localhost:8000/api/v1/objects/access-requests/my \
  -H "Authorization: Bearer ACCESS_TOKEN"

# Ответ: список запросов со статусами
[
  {
    "id": 1,
    "object_id": 1,
    "object_name": "Жилой комплекс 'Солнечный'",
    "status": "PENDING",  # PENDING, APPROVED, или REJECTED
    "reason": "Назначен ответственным за электромонтажные работы"
  }
]
```

## Для менеджера (MANAGER)

### Создать новый объект

```bash
curl -X POST http://localhost:8000/api/v1/objects \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Жилой комплекс 'Солнечный'",
    "contract_number": "К-2025-001",
    "material_amount": 2000000,
    "labor_amount": 1000000
  }'

# Ответ:
# {
#   "id": 1,
#   "name": "Жилой комплекс 'Солнечный'",
#   "code": "OBJ-2026-001",  # генерируется автоматически
#   "contract_amount": 3000000.0
# }
```

### Увидеть запросы на доступ к объекту

```bash
curl http://localhost:8000/api/v1/objects/1/access-requests \
  -H "Authorization: Bearer ACCESS_TOKEN"

# Ответ: список всех запросов к объекту
[
  {
    "id": 1,
    "foreman_id": 4,
    "foreman_name": "Бригадир Иванов И.И.",
    "status": "PENDING",
    "reason": "Назначен ответственным за электромонтажные работы",
    "created_at": "2026-01-26T20:47:16.123456"
  }
]
```

### Одобрить запрос

```bash
curl -X POST http://localhost:8000/api/v1/objects/1/access-requests/1/approve \
  -H "Authorization: Bearer ACCESS_TOKEN"

# Ответ:
# {
#   "id": 1,
#   "status": "APPROVED",
#   "message": "Запрос одобрен. Бригадир получил доступ к объекту"
# }
```

### Отклонить запрос

```bash
curl -X POST http://localhost:8000/api/v1/objects/1/access-requests/1/reject \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rejection_reason": "На объекте уже работает назначенная бригада"
  }'

# Ответ:
# {
#   "id": 1,
#   "status": "REJECTED",
#   "rejection_reason": "На объекте уже работает назначенная бригада",
#   "message": "Запрос отклонён"
# }
```

## Статусы запроса доступа

- **PENDING** - ожидает рассмотрения менеджером
- **APPROVED** - одобрено, бригадир получил доступ
- **REJECTED** - отклонено, указана причина

## Тестовые пользователи

```
Бригадир:
  Логин: foreman
  Пароль: foreman123

Менеджер:
  Логин: manager
  Пароль: manager123

Администратор:
  Логин: admin
  Пароль: admin123
```

## Примеры кодов объектов

- `OBJ-2026-001` - объект 1 за 2026 год
- `OBJ-2026-002` - объект 2 за 2026 год
- Генерируются автоматически

## Частые вопросы

**Q: Что если я отправлю несколько запросов на доступ к одному объекту?**
A: Система блокирует дублирующиеся запросы с сообщением "Вы уже отправили запрос на доступ к этому объекту"

**Q: Что произойдет, если менеджер одобрит запрос?**
A: Бригадир автоматически добавится в список ответственных за объект и сможет создавать заявки по этому объекту

**Q: Как отклонить запрос?**
A: Используйте эндпоинт `/reject` и обязательно укажите причину для бригадира

**Q: Где увидеть историю?**
A: Все действия логируются в `audit_log` - запросы, одобрения, отклонения

## Возможные ошибки и их решения

| Ошибка | Причина | Решение |
|--------|---------|--------|
| 404 "Объект не найден" | ID объекта неверный | Проверьте ID объекта |
| 400 "Вы уже отправили запрос" | Активный запрос существует | Подождите решения менеджера |
| 400 "У вас уже есть доступ" | Доступ уже одобрен | Запрос больше не нужен |
| 400 "Запрос уже обработан" | Статус не PENDING | Нельзя обработать дважды |
| 403 "Недостаточно прав" | Роль не позволяет операцию | Проверьте роль пользователя |

## Интеграция с фронтенд

API готов к интеграции с React компонентами:

```typescript
// Запрос доступа
const requestObjectAccess = async (objectId: number, reason?: string) => {
  const response = await fetch(`/api/v1/objects/${objectId}/request-access`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ reason })
  });
  return response.json();
};

// Получить свои запросы
const getMyAccessRequests = async () => {
  const response = await fetch('/api/v1/objects/access-requests/my', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};
```

## Контакты и поддержка

Все эндпоинты задокументированы в Swagger:
`http://localhost:8000/docs`

Полная документация в файле: `OBJECT_ACCESS_SYSTEM.md`
