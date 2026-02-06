import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiClient } from '../api/client';
import { useNavigate } from 'react-router-dom';
import { Modal } from '../components/Modal';
import { TopObjectsChart } from '../components/TopObjectsChart';
import { TopEquipmentChart } from '../components/TopEquipmentChart';
import '../styles/Modal.css';

// Перевод ролей на русский
const roleLabels: Record<string, string> = {
  'ADMIN': 'Администратор',
  'MANAGER': 'Менеджер',
  'FOREMAN': 'Бригадир',
  'ACCOUNTANT': 'Бухгалтер',
  'HR_MANAGER': 'Кадровик',
  'EQUIPMENT_MANAGER': 'Менеджер по технике',
  'MATERIALS_MANAGER': 'Менеджер по материалам',
  'PROCUREMENT_MANAGER': 'Менеджер по закупкам',
};

interface DashboardStats {
  objects: number;
  upd: number;
  materialRequests: number;
  equipmentOrders: number;
  timesheets?: number;
  newMaterialRequests?: number;
  pendingEquipment?: number;
  completedObjects?: number;
}

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    objects: 0,
    upd: 0,
    materialRequests: 0,
    equipmentOrders: 0,
    newMaterialRequests: 0,
    pendingEquipment: 0,
  });
  const [loading, setLoading] = useState(true);
  const [activeModal, setActiveModal] = useState<'objects' | 'upd' | 'materials' | 'equipment' | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      // Загружаем данные из API
      const [objectsRes, updRes, materialsRes, equipmentRes] = await Promise.all([
        apiClient.get<any[]>('/objects/').catch(() => []),
        apiClient.get<any[]>('/material-costs/').catch(() => []),
        apiClient.get<any[]>('/material-requests/').catch(() => []),
        apiClient.get<any[]>('/equipment-orders/').catch(() => []),
      ]);

      setStats({
        objects: Array.isArray(objectsRes) ? objectsRes.length : 0,
        upd: Array.isArray(updRes) ? updRes.length : 0,
        materialRequests: Array.isArray(materialsRes) ? materialsRes.length : 0,
        equipmentOrders: Array.isArray(equipmentRes) ? equipmentRes.length : 0,
        newMaterialRequests: Array.isArray(materialsRes) ? materialsRes.filter((r: any) => r.status === 'NEW').length : 0,
        pendingEquipment: Array.isArray(equipmentRes) ? equipmentRes.filter((o: any) => o.status === 'NEW').length : 0,
      });
    } catch (err) {
      console.error('Ошибка загрузки статистики:', err);
    } finally {
      setLoading(false);
    }
  };

  const cards = [
    {
      title: 'Объекты',
      icon: '🏗️',
      count: stats.objects,
      color: '#3498db',
      path: '/objects',
      type: 'objects' as const,
      subtitle: 'всего в системе'
    },
    {
      title: 'УПД документы',
      icon: '📄',
      count: stats.upd,
      color: '#2ecc71',
      path: '/upd',
      type: 'upd' as const,
      subtitle: 'загружено'
    },
    {
      title: 'Заявки на материалы',
      icon: '📦',
      count: stats.materialRequests,
      color: '#e74c3c',
      path: '/material-requests',
      type: 'materials' as const,
      subtitle: stats.newMaterialRequests ? `${stats.newMaterialRequests} новых` : 'всего'
    },
    {
      title: 'Аренда техники',
      icon: '🚜',
      count: stats.equipmentOrders,
      color: '#f39c12',
      path: '/equipment-orders',
      type: 'equipment' as const,
      subtitle: stats.pendingEquipment ? `${stats.pendingEquipment} ожидают` : 'всего'
    },
  ];

  // Модули быстрого доступа в зависимости от ролей
  const getQuickActions = () => {
    const actions = [];

    if (user?.roles.some(r => ['ADMIN', 'MANAGER', 'ACCOUNTANT'].includes(r))) {
      actions.push({ label: '📄 Загрузить УПД', path: '/upd', color: '#3498db' });
    }

    if (user?.roles.some(r => ['ADMIN', 'MANAGER', 'FOREMAN'].includes(r))) {
      actions.push({ label: '📦 Заявки на материалы', path: '/material-requests', color: '#2ecc71' });
      actions.push({ label: '🚜 Заявки на технику', path: '/equipment-orders', color: '#f39c12' });
    }



    actions.push({ label: '📊 Отчёты и аналитика', path: '/analytics', color: '#1abc9c' });

    if (user?.roles.includes('ADMIN')) {
      actions.push({ label: '⚙️ Администрирование', path: '/admin', color: '#95a5a6' });
    }

    return actions;
  };

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>🏠 Главная</h1>

      {/* Информация о профиле */}
      <div style={{
        backgroundColor: 'white',
        padding: '25px',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '30px',
        display: 'flex',
        alignItems: 'center',
        gap: '25px'
      }}>
        {user?.profile_photo_url ? (
          <img
            src={`http://192.168.0.235:8000${user.profile_photo_url}`}
            alt="Фото профиля"
            style={{
              width: '90px',
              height: '90px',
              borderRadius: '50%',
              objectFit: 'cover',
              border: '4px solid #3498db'
            }}
          />
        ) : (
          <div style={{
            width: '90px',
            height: '90px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #3498db, #2980b9)',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '36px',
            fontWeight: 'bold',
            boxShadow: '0 4px 12px rgba(52, 152, 219, 0.4)'
          }}>
            {(user?.full_name || user?.username || '?')[0].toUpperCase()}
          </div>
        )}
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: '0 0 8px 0', fontSize: '24px' }}>
            👋 Добро пожаловать, {user?.full_name || user?.username}!
          </h2>
          <div style={{ color: '#7f8c8d', fontSize: '14px', marginBottom: '8px' }}>
            @{user?.username}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {user?.roles.map(role => (
              <span
                key={role}
                style={{
                  padding: '4px 12px',
                  backgroundColor: '#3498db20',
                  color: '#3498db',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '500'
                }}
              >
                {roleLabels[role] || role}
              </span>
            ))}
          </div>
          {user?.birth_date && (
            <div style={{ color: '#7f8c8d', fontSize: '13px', marginTop: '8px' }}>
              🎂 Дата рождения: {new Date(user.birth_date).toLocaleDateString('ru')}
            </div>
          )}
        </div>
      </div>

      {/* Статистика */}
      <h3 style={{ marginBottom: '15px', color: '#2c3e50' }}>📊 Статистика системы</h3>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '20px',
        marginBottom: '40px'
      }}>
        {cards.map(card => (
          <div
            key={card.title}
            onClick={() => setActiveModal(card.type)}
            style={{
              backgroundColor: 'white',
              padding: '25px',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              borderLeft: `5px solid ${card.color}`,
              cursor: 'pointer',
              transition: 'transform 0.2s, box-shadow 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 8px 20px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <span style={{ fontSize: '24px' }}>{card.icon}</span>
              <span style={{ fontSize: '14px', color: '#7f8c8d' }}>{card.title}</span>
            </div>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: card.color }}>
              {loading ? '...' : card.count}
            </div>
            <div style={{ fontSize: '12px', color: '#95a5a6', marginTop: '5px' }}>
              {card.subtitle}
            </div>
          </div>
        ))}
      </div>

      {/* Графики продуктивности */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
        gap: '20px',
        marginBottom: '40px'
      }}>
        <div style={{
          backgroundColor: 'white',
          padding: '25px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>
            📊 Топ объектов по доставкам материалов
          </h3>
          <TopObjectsChart />
        </div>

        <div style={{
          backgroundColor: 'white',
          padding: '25px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>
            🚜 Топ объектов по расходам на технику
          </h3>
          <TopEquipmentChart />
        </div>
      </div>

      {/* Быстрый доступ */}
      <div style={{
        backgroundColor: 'white',
        padding: '25px',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '20px' }}>⚡ Быстрый доступ</h3>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {getQuickActions().map(action => (
            <button
              key={action.path}
              onClick={() => navigate(action.path)}
              style={{
                padding: '12px 20px',
                backgroundColor: action.color,
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'opacity 0.2s, transform 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.9';
                e.currentTarget.style.transform = 'scale(1.02)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '1';
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>

      {/* Подсказки для новых пользователей */}
      {stats.objects === 0 && !loading && (
        <div style={{
          marginTop: '30px',
          backgroundColor: '#fef9e7',
          border: '1px solid #f9e79f',
          padding: '20px',
          borderRadius: '12px'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#d68910' }}>💡 Начало работы</h4>
          <p style={{ margin: 0, color: '#7f8c8d' }}>
            Для начала работы создайте объекты учёта, загрузите УПД документы или используйте Telegram бот для создания заявок.
          </p>
        </div>
      )}

      {/* Модальные окна статистики */}
      <Modal
        isOpen={activeModal === 'objects'}
        onClose={() => setActiveModal(null)}
        title="Объекты учета"
        size="large"
      >
        <div style={{ padding: '20px' }}>
          <p style={{ marginBottom: '15px', color: '#7f8c8d' }}>
            Всего объектов в системе: <strong>{stats.objects}</strong>
          </p>
          <button
            onClick={() => { setActiveModal(null); navigate('/objects'); }}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Перейти к объектам →
          </button>
        </div>
      </Modal>

      <Modal
        isOpen={activeModal === 'upd'}
        onClose={() => setActiveModal(null)}
        title="УПД документы"
        size="large"
      >
        <div style={{ padding: '20px' }}>
          <p style={{ marginBottom: '15px', color: '#7f8c8d' }}>
            Загружено УПД документов: <strong>{stats.upd}</strong>
          </p>
          <button
            onClick={() => { setActiveModal(null); navigate('/upd'); }}
            style={{
              padding: '10px 20px',
              backgroundColor: '#2ecc71',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Перейти к УПД →
          </button>
        </div>
      </Modal>

      <Modal
        isOpen={activeModal === 'materials'}
        onClose={() => setActiveModal(null)}
        title="Заявки на материалы"
        size="large"
      >
        <div style={{ padding: '20px' }}>
          <p style={{ marginBottom: '10px', color: '#7f8c8d' }}>
            Всего заявок: <strong>{stats.materialRequests}</strong>
          </p>
          {stats.newMaterialRequests! > 0 && (
            <p style={{ marginBottom: '15px', color: '#e74c3c', fontWeight: 'bold' }}>
              Новых заявок: {stats.newMaterialRequests}
            </p>
          )}
          <button
            onClick={() => { setActiveModal(null); navigate('/material-requests'); }}
            style={{
              padding: '10px 20px',
              backgroundColor: '#e74c3c',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Перейти к заявкам →
          </button>
        </div>
      </Modal>

      <Modal
        isOpen={activeModal === 'equipment'}
        onClose={() => setActiveModal(null)}
        title="Аренда техники"
        size="large"
      >
        <div style={{ padding: '20px' }}>
          <p style={{ marginBottom: '10px', color: '#7f8c8d' }}>
            Всего заявок на технику: <strong>{stats.equipmentOrders}</strong>
          </p>
          {stats.pendingEquipment! > 0 && (
            <p style={{ marginBottom: '15px', color: '#f39c12', fontWeight: 'bold' }}>
              Ожидают утверждения: {stats.pendingEquipment}
            </p>
          )}
          <button
            onClick={() => { setActiveModal(null); navigate('/equipment-orders'); }}
            style={{
              padding: '10px 20px',
              backgroundColor: '#f39c12',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Перейти к технике →
          </button>
        </div>
      </Modal>
    </div>
  );
}
