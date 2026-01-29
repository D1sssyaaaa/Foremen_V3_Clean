# 🔧 Быстрая интеграция компонентов в App.tsx

## Шаг 1: Импортирование компонентов

```typescript
// В начале App.tsx добавьте импорты:

import ObjectAccessRequest from './components/ObjectAccessRequest';
import AdminAccessRequests from './components/AdminAccessRequests';
```

## Шаг 2: Добавление маршрутов

```typescript
// В компоненте Router (внутри <Routes>):

{/* Маршруты для запроса доступа */}
<Route path="/access-request" element={<ObjectAccessRequest />} />
<Route path="/admin/access-requests" element={<AdminAccessRequests />} />
```

## Шаг 3: Добавление навигации

### Вариант 1: Добавить в главное меню

```typescript
// В компоненте главного меню или ProfilePage:

import { useAuth } from './contexts/AuthContext';

export function MainMenu() {
  const { userRoles } = useAuth();
  
  return (
    <nav>
      {/* Существующие пункты меню */}
      
      {/* НОВОЕ: Запрос доступа (для бригадиров) */}
      {userRoles?.includes('FOREMAN') && (
        <Link to="/access-request" className="menu-item">
          🏗️ Запрос доступа к объектам
        </Link>
      )}
      
      {/* НОВОЕ: Управление запросами (для менеджеров) */}
      {(userRoles?.includes('MANAGER') || userRoles?.includes('ADMIN')) && (
        <Link to="/admin/access-requests" className="menu-item">
          🔐 Управление запросами доступа
        </Link>
      )}
    </nav>
  );
}
```

### Вариант 2: Добавить в ProfilePage

```typescript
// В компоненте ProfilePage добавьте новый раздел:

export function ProfilePage() {
  const { user, userRoles } = useAuth();
  
  return (
    <div className="profile-container">
      {/* Существующие разделы */}
      
      {/* НОВОЕ: Раздел запроса доступа */}
      <section className="profile-section">
        <h3>📋 Мои запросы доступа</h3>
        
        {userRoles?.includes('FOREMAN') && (
          <>
            <p>Запросить доступ к объектам для работы:</p>
            <Link to="/access-request" className="btn btn-primary">
              🏗️ Запросить доступ
            </Link>
          </>
        )}
        
        {(userRoles?.includes('MANAGER') || userRoles?.includes('ADMIN')) && (
          <>
            <p>Управление запросами доступа от бригадиров:</p>
            <Link to="/admin/access-requests" className="btn btn-primary">
              🔐 Управлять запросами
            </Link>
          </>
        )}
      </section>
    </div>
  );
}
```

## Шаг 4: Проверка переменных окружения

Убедитесь, что в файле `.env` (или `.env.local`) установлена переменная:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

Или для production:

```env
VITE_API_URL=https://your-domain.com/api/v1
```

## Шаг 5: Проверка AuthContext

Убедитесь, что ваш `AuthContext` экспортирует следующие значения:

```typescript
interface AuthContextType {
  token: string | null;
  user: User | null;
  userRoles: string[]; // ['FOREMAN', 'MANAGER', 'ADMIN', ...]
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  // ... остальные методы
}

// Использование в компонентах:
const { token, user, userRoles } = useAuth();
```

## Шаг 6: Тестирование

### Для бригадира (FOREMAN)
```typescript
// Эта ссылка должна быть видна:
<Link to="/access-request">🏗️ Запросить доступ</Link>

// Кликнуть и проверить функциональность:
1. Выбрать объект
2. Ввести причину (опционально)
3. Отправить запрос
4. Проверить в истории
```

### Для менеджера (MANAGER/ADMIN)
```typescript
// Эта ссылка должна быть видна:
<Link to="/admin/access-requests">🔐 Управлять запросами</Link>

// Кликнуть и проверить функциональность:
1. Выбрать объект
2. Увидеть запросы со статусом PENDING
3. Одобрить или отклонить
4. Проверить обновление статистики
```

## Полный пример App.tsx

```typescript
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';

// Импортируем новые компоненты
import ObjectAccessRequest from './components/ObjectAccessRequest';
import AdminAccessRequests from './components/AdminAccessRequests';

// Существующие компоненты
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import DashboardPage from './pages/DashboardPage';

function App() {
  const { token, user, userRoles } = useAuth();

  return (
    <Router>
      <div className="app">
        <header>
          <nav>
            <Link to="/">Home</Link>
            {token && <Link to="/profile">Profile</Link>}
            {token && <Link to="/dashboard">Dashboard</Link>}
            
            {/* НОВОЕ: Запрос доступа для бригадиров */}
            {userRoles?.includes('FOREMAN') && (
              <Link to="/access-request" className="nav-item foreman">
                🏗️ Запрос доступа
              </Link>
            )}
            
            {/* НОВОЕ: Управление запросами для менеджеров */}
            {(userRoles?.includes('MANAGER') || userRoles?.includes('ADMIN')) && (
              <Link to="/admin/access-requests" className="nav-item admin">
                🔐 Управлять запросами
              </Link>
            )}
          </nav>
        </header>

        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            
            {/* НОВОЕ: Маршруты для запроса доступа */}
            <Route path="/access-request" element={<ObjectAccessRequest />} />
            <Route 
              path="/admin/access-requests" 
              element={
                // Проверка прав доступа
                userRoles?.includes('MANAGER') || userRoles?.includes('ADMIN') ? (
                  <AdminAccessRequests />
                ) : (
                  <div>❌ Access Denied</div>
                )
              } 
            />
          </Routes>
        </main>

        <footer>
          <p>&copy; 2025 Construction Costs Management System</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
```

## Чек-лист интеграции

- [ ] Импортированы компоненты ObjectAccessRequest и AdminAccessRequests
- [ ] Добавлены маршруты в <Routes>
- [ ] Добавлены ссылки в навигацию с проверкой ролей
- [ ] Проверена переменная окружения VITE_API_URL
- [ ] Протестирована функциональность для FOREMAN
- [ ] Протестирована функциональность для MANAGER/ADMIN
- [ ] Проверено на мобильных устройствах
- [ ] Все стили загружаются корректно
- [ ] Нет ошибок в консоли браузера

## Трубблшутинг

### Компонент не загружается
```typescript
// Проверьте импорт:
import ObjectAccessRequest from './components/ObjectAccessRequest';
// Должен быть полный путь к файлу

// Проверьте что файл существует:
// src/components/ObjectAccessRequest.tsx
// src/styles/ObjectAccessRequest.css
```

### API не отвечает
```typescript
// Проверьте VITE_API_URL в .env
console.log(import.meta.env.VITE_API_URL);

// Убедитесь что backend запущен:
// python -m app.main (в папке backend)

// Проверьте CORS настройки на backend
```

### Стили не применяются
```typescript
// Убедитесь что CSS файл импортирован в компонент:
import '../styles/ObjectAccessRequest.css';

// Или используйте CSS Modules:
import styles from '../styles/ObjectAccessRequest.module.css';
```

### Проблемы с авторизацией
```typescript
// Проверьте что токен передается:
const { token } = useAuth();
console.log('Token:', token);

// Проверьте что Authorization header правильный:
// Authorization: Bearer {token}
```

---

## Дополнительно

### Добавление иконок (опционально)
```typescript
// Если используете библиотеку иконок (react-icons):
import { FiRequestLine, FiCheckSquare } from 'react-icons/fi';

<Link to="/access-request">
  <FiRequestLine /> Запрос доступа
</Link>
```

### Добавление уведомлений (опционально)
```typescript
// После успешного запроса можно показать уведомление:
import { toast } from 'react-hot-toast';

// В ObjectAccessRequest.tsx:
if (response.ok) {
  toast.success('✅ Запрос отправлен успешно!');
  setSubmitted(true);
}
```

### Интеграция с глобальным состоянием (Redux/Zustand)
```typescript
// Если используете Redux:
import { useDispatch, useSelector } from 'react-redux';

const dispatch = useDispatch();
const requests = useSelector(state => state.accessRequests);

// После успешного запроса обновите store:
dispatch(addAccessRequest(newRequest));
```

---

## Ресурсы

- 📖 [Полная документация](./COMPLETE_IMPLEMENTATION.md)
- 🧪 [Примеры тестирования](./test_telegram_access.md)
- 🏗️ [Архитектура системы](./ARCHITECTURE_DIAGRAM.md)
- 📋 [API документация](./TELEGRAM_REQUEST_ACCESS_UPDATE.md)

---

**Все готово! Начните с Шага 1 и следуйте инструкциям. 🚀**

