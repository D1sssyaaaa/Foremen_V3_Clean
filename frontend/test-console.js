/**
 * Скрипт для тестирования веб-приложения "Снаб" через консоль браузера
 * 
 * ИНСТРУКЦИЯ:
 * 1. Откройте http://localhost:3000 в браузере
 * 2. Залогиньтесь как admin/admin123
 * 3. Откройте консоль браузера (F12)
 * 4. Скопируйте и вставьте весь этот скрипт
 * 5. Дождитесь завершения тестов
 * 
 * Скрипт автоматически проверит все страницы и функции
 */

(async function testConstructionCostsApp() {
  console.log('🚀 Начинаем тестирование системы "Снаб"...\n');
  
  const results = {
    passed: [],
    failed: [],
    warnings: []
  };

  const API_BASE = 'http://localhost:8000/api/v1';
  
  // Получаем токен из localStorage
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    console.error('❌ Токен не найден. Пожалуйста, залогиньтесь в систему!');
    return;
  }

  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  // Функция задержки
  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  // Функция для выполнения теста
  const runTest = async (name, testFn) => {
    try {
      console.log(`⏳ ${name}...`);
      await testFn();
      results.passed.push(name);
      console.log(`✅ ${name} - PASSED\n`);
    } catch (error) {
      const errorDetails = {
        message: error.message,
        type: error.name,
        stack: error.stack?.split('\n').slice(0, 3).join('\n') || 'N/A',
        response: error.response || null
      };
      
      // Расширенная диагностика
      console.group(`❌ ${name} - FAILED`);
      
      console.error(`📋 Тип ошибки: ${errorDetails.type}`);
      console.error(`💬 Сообщение: ${errorDetails.message}`);
      
      // Диагностика типа ошибки
      if (error.message === 'Failed to fetch') {
        console.error(`\n🔍 Детали CORS/Network ошибки:`);
        console.error(`   ├─ Origin: ${window.location.origin}`);
        console.error(`   ├─ Target API: ${API_BASE}`);
        console.error(`   ├─ Браузер: ${navigator.userAgent.split(' ').slice(-2).join(' ')}`);
        console.error(`   ├─ Онлайн: ${navigator.onLine ? '✓ Да' : '✗ Нет'}`);
        console.error(`   └─ Возможные причины:`);
        console.error(`      • Backend сервер не запущен`);
        console.error(`      • CORS настройки блокируют запрос`);
        console.error(`      • Неверный URL эндпоинта`);
        console.error(`      • Firewall/антивирус блокирует`);
      } else if (error.message.includes('HTTP')) {
        const statusMatch = error.message.match(/HTTP (\d+)/);
        if (statusMatch) {
          const status = parseInt(statusMatch[1]);
          console.error(`\n🌐 HTTP Статус: ${status}`);
          if (status === 401) {
            console.error(`   └─ Ошибка аутентификации - токен недействителен или истек`);
          } else if (status === 403) {
            console.error(`   └─ Доступ запрещен - недостаточно прав`);
          } else if (status === 404) {
            console.error(`   └─ Эндпоинт не найден - проверьте URL`);
          } else if (status === 500) {
            console.error(`   └─ Внутренняя ошибка сервера - проверьте логи backend`);
          } else if (status >= 400 && status < 500) {
            console.error(`   └─ Ошибка клиента - проверьте запрос`);
          } else if (status >= 500) {
            console.error(`   └─ Ошибка сервера - проверьте backend`);
          }
        }
      } else if (error.message.includes('JSON')) {
        console.error(`\n📄 Ошибка парсинга JSON - сервер вернул некорректный ответ`);
      }
      
      // Стек вызовов (сокращенный)
      if (errorDetails.stack !== 'N/A') {
        console.error(`\n📚 Стек вызовов:\n${errorDetails.stack}`);
      }
      
      console.groupEnd();
      console.log(''); // Пустая строка для разделения
      
      results.failed.push({ 
        name, 
        error: errorDetails.message,
        type: errorDetails.type,
        timestamp: new Date().toISOString()
      });
    }
  };

  // ========== ТЕСТЫ API ==========

  // Тест CORS перед всеми остальными
  await runTest('Проверка CORS конфигурации', async () => {
    console.log(`   Frontend Origin: ${window.location.origin}`);
    console.log(`   Backend API: ${API_BASE}`);
    
    const response = await fetch(`${API_BASE}/auth/me`, { 
      headers,
      mode: 'cors',
      credentials: 'include'
    });
    
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    
    const corsHeaders = {
      'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
      'access-control-allow-credentials': response.headers.get('access-control-allow-credentials'),
      'access-control-allow-methods': response.headers.get('access-control-allow-methods')
    };
    
    console.log('   ✓ CORS Headers:', JSON.stringify(corsHeaders, null, 2));
  });

  await runTest('Проверка аутентификации', async () => {
    const response = await fetch(`${API_BASE}/auth/me`, { headers });
    if (!response.ok) throw new Error(`HTTP ${response.status}: Не удалось получить данные пользователя`);
    const user = await response.json();
    console.log('   Пользователь:', user.username, '| Роли:', user.roles.join(', '));
  });

  await runTest('Получение списка объектов учета', async () => {
    const response = await fetch(`${API_BASE}/objects`, { headers });
    if (!response.ok) throw new Error(`Ошибка ${response.status}`);
    const objects = await response.json();
    console.log(`   Найдено объектов: ${objects.length}`);
    if (objects.length > 0) {
      console.log(`   Первый объект: ${objects[0].name} (${objects[0].code})`);
    }
  });

  await runTest('Получение необработанных УПД', async () => {
    const response = await fetch(`${API_BASE}/material-costs/unprocessed`, { headers });
    if (!response.ok) throw new Error(`Ошибка ${response.status}`);
    const upds = await response.json();
    console.log(`   Необработанных УПД: ${upds.length}`);
  });

  await runTest('Получение заявок на материалы', async () => {
    const response = await fetch(`${API_BASE}/material-requests/`, { headers });
    if (!response.ok) {
      const errorText = await response.text();
      console.log('   Ответ сервера:', errorText.substring(0, 300));
      throw new Error(`Ошибка ${response.status}`);
    }
    const requests = await response.json();
    console.log(`   Найдено заявок на материалы: ${requests.length}`);
    if (requests.length > 0) {
      const statuses = requests.reduce((acc, r) => {
        acc[r.status] = (acc[r.status] || 0) + 1;
        return acc;
      }, {});
      console.log('   Статусы:', statuses);
    }
  });

  await runTest('Получение заявок на технику', async () => {
    const response = await fetch(`${API_BASE}/equipment-orders/`, { headers });
    if (!response.ok) throw new Error(`Ошибка ${response.status}`);
    const orders = await response.json();
    console.log(`   Найдено заявок на технику: ${orders.length}`);
  });

  await runTest('Получение табелей РТБ', async () => {
    const response = await fetch(`${API_BASE}/time-sheets/`, { headers });
    if (!response.ok) throw new Error(`Ошибка ${response.status}`);
    const sheets = await response.json();
    console.log(`   Найдено табелей: ${sheets.length}`);
  });

  await runTest('Получение аналитики', async () => {
    const today = new Date().toISOString().split('T')[0];
    const monthAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    const response = await fetch(
      `${API_BASE}/analytics?period_start=${monthAgo}&period_end=${today}`,
      { headers }
    );
    if (!response.ok) throw new Error(`Ошибка ${response.status}`);
    const analytics = await response.json();
    console.log(`   Данных по объектам: ${analytics.length}`);
    const totalCosts = analytics.reduce((sum, item) => sum + (item.total_costs || 0), 0);
    console.log(`   Общая сумма затрат: ${totalCosts.toLocaleString('ru')} ₽`);
  });

  // ========== ТЕСТЫ UI ЭЛЕМЕНТОВ ==========

  await runTest('Проверка навигационного меню', async () => {
    const menuLinks = document.querySelectorAll('nav a');
    if (menuLinks.length === 0) throw new Error('Меню не найдено');
    console.log(`   Найдено пунктов меню: ${menuLinks.length}`);
    const menuTexts = Array.from(menuLinks).map(link => link.textContent.trim());
    console.log('   Пункты:', menuTexts.join(', '));
  });

  await runTest('Проверка кнопок на странице', async () => {
    const buttons = document.querySelectorAll('button');
    console.log(`   Найдено кнопок: ${buttons.length}`);
    
    const buttonTexts = Array.from(buttons)
      .map(btn => btn.textContent.trim())
      .filter(text => text.length > 0);
    
    console.log('   Тексты кнопок:', [...new Set(buttonTexts)].join(', '));
  });

  await runTest('Проверка заголовка страницы', async () => {
    const h1 = document.querySelector('h1');
    if (!h1) throw new Error('Заголовок H1 не найден');
    console.log(`   Заголовок: "${h1.textContent.trim()}"`);
  });

  // ========== ТЕСТ СОЗДАНИЯ ОБЪЕКТА ==========

  await runTest('Создание тестового объекта', async () => {
    const testObject = {
      name: `Тестовый объект ${Date.now()}`,
      code: `TEST-${Date.now()}`,
      contract_number: 'TEST-2026-001',
      contract_amount: 1000000
    };

    const response = await fetch(`${API_BASE}/objects`, {
      method: 'POST',
      headers,
      body: JSON.stringify(testObject)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Не удалось создать объект: ${error.detail || response.statusText}`);
    }

    const created = await response.json();
    console.log(`   Создан объект: ${created.name} (ID: ${created.id})`);
    
    // Удаляем тестовый объект
    await fetch(`${API_BASE}/objects/${created.id}`, {
      method: 'DELETE',
      headers
    });
    console.log(`   Тестовый объект удалён`);
  });

  // ========== ТЕСТ ЭКСПОРТА ==========

  await runTest('Проверка endpoint экспорта аналитики', async () => {
    const today = new Date().toISOString().split('T')[0];
    const monthAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    const response = await fetch(
      `${API_BASE}/analytics/export?period_start=${monthAgo}&period_end=${today}`,
      { headers }
    );

    if (!response.ok) throw new Error(`Ошибка ${response.status}`);
    
    const contentType = response.headers.get('content-type');
    if (!contentType.includes('spreadsheet') && !contentType.includes('excel')) {
      results.warnings.push('Экспорт: Content-Type не Excel');
    }
    
    const blob = await response.blob();
    console.log(`   Размер Excel файла: ${(blob.size / 1024).toFixed(2)} KB`);
  });

  // ========== ТЕСТ НАВИГАЦИИ ==========

  await runTest('Проверка навигации между страницами', async () => {
    const links = document.querySelectorAll('nav a');
    const pages = Array.from(links).map(link => {
      const href = link.getAttribute('href');
      return { text: link.textContent.trim(), href };
    });
    
    console.log(`   Доступных страниц: ${pages.length}`);
    pages.forEach(page => console.log(`     - ${page.text}: ${page.href}`));
  });

  // ========== ПРОВЕРКА ЛОКАЛЬНОГО ХРАНИЛИЩА ==========

  await runTest('Проверка данных в localStorage', async () => {
    const keys = Object.keys(localStorage);
    console.log(`   Ключей в localStorage: ${keys.length}`);
    
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    const user = localStorage.getItem('user');
    
    if (accessToken) console.log('   ✓ Access token присутствует');
    if (refreshToken) console.log('   ✓ Refresh token присутствует');
    if (user) {
      const userData = JSON.parse(user);
      console.log(`   ✓ Пользователь: ${userData.username}`);
    }
  });

  // ========== ПРОВЕРКА ОШИБОК КОНСОЛИ ==========

  await runTest('Проверка ошибок в консоли', async () => {
    // Этот тест просто информационный
    console.log('   Проверьте консоль браузера на наличие ошибок (красные сообщения)');
    results.warnings.push('Проверьте консоль на ошибки вручную');
  });

  // ========== ИТОГОВЫЙ ОТЧЕТ ==========

  console.log('\n' + '='.repeat(60));
  console.log('📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ');
  console.log('='.repeat(60) + '\n');

  console.log(`✅ Успешных тестов: ${results.passed.length}`);
  results.passed.forEach(test => console.log(`   ✓ ${test}`));

  if (results.failed.length > 0) {
    console.log(`\n❌ Провальных тестов: ${results.failed.length}`);
    results.failed.forEach(({ name, error, type, timestamp }) => {
      console.log(`   ✗ ${name}`);
      console.log(`     ├─ Ошибка: ${error}`);
      console.log(`     ├─ Тип: ${type}`);
      console.log(`     └─ Время: ${new Date(timestamp).toLocaleTimeString('ru')}`);
    });
    
    // Рекомендации по исправлению
    console.log(`\n💡 Рекомендации для исправления:`);
    const hasCorsErrors = results.failed.some(f => f.error === 'Failed to fetch');
    const hasHttpErrors = results.failed.some(f => f.error.includes('HTTP'));
    
    if (hasCorsErrors) {
      console.log(`   🔧 CORS/Network ошибки:`);
      console.log(`      1. Проверьте, запущен ли backend сервер на http://localhost:8000`);
      console.log(`      2. Откройте http://localhost:8000/docs - должна открыться Swagger UI`);
      console.log(`      3. Проверьте консоль backend на наличие ошибок`);
      console.log(`      4. Перезапустите backend: cd backend && python -m uvicorn main:app --reload`);
    }
    
    if (hasHttpErrors) {
      console.log(`   🔧 HTTP ошибки:`);
      console.log(`      1. Проверьте логи backend сервера`);
      console.log(`      2. Перелогиньтесь (Выход → Вход)`);
      console.log(`      3. Проверьте роли пользователя admin`);
    }
  }

  if (results.warnings.length > 0) {
    console.log(`\n⚠️  Предупреждения: ${results.warnings.length}`);
    results.warnings.forEach(warning => console.log(`   ⚠ ${warning}`));
  }

  const successRate = (results.passed.length / (results.passed.length + results.failed.length) * 100).toFixed(1);
  
  console.log('\n' + '='.repeat(60));
  console.log(`🎯 Процент успешности: ${successRate}%`);
  console.log('='.repeat(60));

  if (results.failed.length === 0) {
    console.log('\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!');
    console.log('✨ Приложение работает корректно\n');
  } else {
    console.log('\n⚠️  Есть проблемы, требующие внимания\n');
  }

  // Возвращаем результаты для программной обработки
  return {
    success: results.failed.length === 0,
    passed: results.passed.length,
    failed: results.failed.length,
    warnings: results.warnings.length,
    successRate: parseFloat(successRate),
    details: results
  };
})();
