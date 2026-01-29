import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../hooks/useAuth';

interface EquipmentOrder {
  id: number;
  cost_object_id: number;
  cost_object_name?: string;
  foreman_id: number;
  foreman_name?: string;
  foreman_phone?: string;
  equipment_type: string;
  quantity: number;
  start_date: string;
  end_date: string;
  status: string;
  rejection_reason?: string;
  total_cost?: number;
  hour_rate?: number;
  hours_worked?: number;
  description?: string;
  comment?: string;
  created_at: string;
  updated_at?: string;
}

// Все статусы с метками (используем русские значения как в backend)
const ALL_STATUSES = [
  { value: 'all', label: 'Все' },
  { value: 'НОВАЯ', label: 'Новая' },
  { value: 'УТВЕРЖДЕНА', label: 'Утверждена' },
  { value: 'В РАБОТЕ', label: 'В работе' },
  { value: 'ЗАВЕРШЕНА', label: 'Завершена' },
  { value: 'ОТМЕНА ЗАПРОШЕНА', label: 'Запрос отмены' },
  { value: 'ОТМЕНЕНА', label: 'Отменена' },
];

// Перевод типов техники на русский
const equipmentTypeLabels: Record<string, string> = {
  'excavator': 'Экскаватор',
  'crane': 'Кран',
  'loader': 'Погрузчик',
  'bulldozer': 'Бульдозер',
  'truck': 'Грузовик',
  'concrete_mixer': 'Бетоносмеситель',
  'dump_truck': 'Самосвал',
  'forklift': 'Вилочный погрузчик',
  'roller': 'Каток',
  'grader': 'Грейдер',
  'scaffolding': 'Строительные леса',
  'generator': 'Генератор',
  'compressor': 'Компрессор',
  'welding_machine': 'Сварочный аппарат',
  'jackhammer': 'Отбойный молоток',
  'drill': 'Дрель',
  'concrete_pump': 'Бетононасос',
  'tower_crane': 'Башенный кран',
  'mobile_crane': 'Автокран',
  'mini_excavator': 'Мини-экскаватор',
  'backhoe': 'Экскаватор-погрузчик',
  'other': 'Другое',
};

export function EquipmentOrdersPage() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<EquipmentOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [selectedOrder, setSelectedOrder] = useState<EquipmentOrder | null>(null);
  const [showCostModal, setShowCostModal] = useState(false);
  const [costOrder, setCostOrder] = useState<EquipmentOrder | null>(null);
  const [hourRate, setHourRate] = useState('');

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const data = await apiClient.get<EquipmentOrder[]>('/equipment-orders/');
      setOrders(data);
    } catch (err) {
      console.error('Ошибка загрузки заявок:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'НОВАЯ': '#3498db',
      'УТВЕРЖДЕНА': '#2ecc71',
      'В РАБОТЕ': '#f39c12',
      'ЗАВЕРШЕНА': '#27ae60',
      'ОТМЕНЕНА': '#95a5a6',
      'ОТМЕНА ЗАПРОШЕНА': '#e67e22',
      'ОТКЛОНЕНА': '#e74c3c',
    };
    return colors[status] || '#7f8c8d';
  };

  const getStatusText = (status: string) => {
    // Backend уже возвращает русские статусы
    return status;
  };

  // Перевод типа техники
  const getEquipmentTypeText = (type: string) => {
    return equipmentTypeLabels[type.toLowerCase()] || equipmentTypeLabels[type] || type;
  };

  const handleApprove = async (id: number) => {
    try {
      await apiClient.post(`/equipment-orders/${id}/approve`, {});
      await loadOrders();
      alert('Заявка утверждена');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка утверждения');
    }
  };

  const handleSetCost = async () => {
    if (!costOrder || !hourRate) return;
    
    try {
      await apiClient.put(`/equipment-orders/${costOrder.id}/cost`, {
        hour_rate: parseFloat(hourRate)
      });
      await loadOrders();
      setShowCostModal(false);
      setCostOrder(null);
      setHourRate('');
      alert('Стоимость установлена');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка установки стоимости');
    }
  };

  const openCostModal = (order: EquipmentOrder) => {
    setCostOrder(order);
    setHourRate(order.hour_rate?.toString() || '');
    setShowCostModal(true);
  };

  const calculateDays = (start: string, end: string) => {
    const diff = new Date(end).getTime() - new Date(start).getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24)) + 1;
  };

  // Проверка прав на управление заявками
  const canManageOrders = () => {
    if (!user) return false;
    return user.roles.some(role => 
      ['ADMIN', 'MANAGER', 'EQUIPMENT_MANAGER'].includes(role)
    );
  };

  const filteredOrders = orders.filter(order => {
    if (filter === 'all') return true;
    return order.status === filter;
  });

  // Подсчёт заявок по статусам
  const statusCounts = ALL_STATUSES.reduce((acc, status) => {
    if (status.value === 'all') {
      acc[status.value] = orders.length;
    } else {
      acc[status.value] = orders.filter(o => o.status === status.value).length;
    }
    return acc;
  }, {} as Record<string, number>);

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Загрузка...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>🚜 Аренда техники и инструмента</h1>
        <button 
          onClick={() => alert('Используйте Telegram Bot для создания заявок на технику!')}
          style={{
            padding: '12px 24px',
            backgroundColor: '#f39c12',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          + Создать заявку
        </button>
      </div>

      {/* Вкладки статусов */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {ALL_STATUSES.map(status => (
          <button
            key={status.value}
            onClick={() => setFilter(status.value)}
            style={{
              padding: '10px 16px',
              backgroundColor: filter === status.value ? '#f39c12' : '#ecf0f1',
              color: filter === status.value ? 'white' : '#2c3e50',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            {status.label}
            <span style={{
              backgroundColor: filter === status.value ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.1)',
              padding: '2px 8px',
              borderRadius: '10px',
              fontSize: '12px'
            }}>
              {statusCounts[status.value] || 0}
            </span>
          </button>
        ))}
      </div>

      {filteredOrders.length === 0 ? (
        <div style={{ 
          backgroundColor: 'white', 
          padding: '40px', 
          borderRadius: '8px',
          textAlign: 'center',
          color: '#7f8c8d'
        }}>
          Заявки не найдены
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '15px' }}>
          {filteredOrders.map(order => (
            <div
              key={order.id}
              style={{
                backgroundColor: 'white',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                borderLeft: `4px solid ${getStatusColor(order.status)}`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '15px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', flexWrap: 'wrap' }}>
                    <h3 style={{ margin: 0, color: '#2c3e50' }}>Заявка #{order.id}</h3>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '500',
                      backgroundColor: getStatusColor(order.status) + '20',
                      color: getStatusColor(order.status)
                    }}>
                      {getStatusText(order.status)}
                    </span>
                  </div>
                  <div style={{ color: '#7f8c8d', fontSize: '14px' }}>
                    📍 <strong>{order.cost_object_name || `Объект ${order.cost_object_id}`}</strong>
                    {' • '}
                    👷 <strong>{order.foreman_name || `Бригадир ${order.foreman_id}`}</strong>
                    {' • '}
                    📅 {new Date(order.created_at).toLocaleDateString('ru')}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {canManageOrders() && order.status === 'НОВАЯ' && (
                    <button
                      onClick={() => handleApprove(order.id)}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#2ecc71',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '14px'
                      }}
                    >
                      ✓ Утвердить
                    </button>
                  )}
                  {canManageOrders() && order.status === 'УТВЕРЖДЕНА' && (
                    <button
                      onClick={() => openCostModal(order)}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#9b59b6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '14px'
                      }}
                    >
                      💰 Стоимость
                    </button>
                  )}
                  <button
                    onClick={() => setSelectedOrder(order)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#3498db',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    👁 Подробнее
                  </button>
                </div>
              </div>

              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                gap: '15px',
                padding: '15px',
                backgroundColor: '#f8f9fa',
                borderRadius: '6px'
              }}>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Тип техники</div>
                  <div style={{ fontWeight: '600', fontSize: '15px' }}>🚜 {getEquipmentTypeText(order.equipment_type)}</div>
                </div>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Количество</div>
                  <div style={{ fontWeight: '600', fontSize: '15px' }}>{order.quantity} ед.</div>
                </div>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Период аренды</div>
                  <div style={{ fontWeight: '600', fontSize: '15px' }}>
                    {new Date(order.start_date).toLocaleDateString('ru')} - {new Date(order.end_date).toLocaleDateString('ru')}
                    <span style={{ color: '#7f8c8d', fontWeight: '400', marginLeft: '8px' }}>
                      ({calculateDays(order.start_date, order.end_date)} дн.)
                    </span>
                  </div>
                </div>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Стоимость</div>
                  <div style={{ fontWeight: '600', fontSize: '15px', color: order.total_cost ? '#27ae60' : '#95a5a6' }}>
                    {order.total_cost ? `${order.total_cost.toLocaleString('ru')} ₽` : 'Не указана'}
                  </div>
                </div>
              </div>

              {order.description && (
                <div style={{ 
                  marginTop: '10px',
                  padding: '10px', 
                  backgroundColor: '#fef9e7', 
                  borderRadius: '4px',
                  fontSize: '14px'
                }}>
                  💬 <strong>Описание работ:</strong> {order.description}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Модальное окно "Подробнее" */}
      {selectedOrder && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}
        onClick={() => setSelectedOrder(null)}
        >
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '12px',
            maxWidth: '600px',
            width: '95%',
            maxHeight: '85vh',
            overflow: 'auto',
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
          }}
          onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
              <div>
                <h2 style={{ margin: 0, marginBottom: '10px' }}>🚜 Заявка #{selectedOrder.id}</h2>
                <span style={{
                  padding: '6px 14px',
                  borderRadius: '12px',
                  fontSize: '13px',
                  fontWeight: '600',
                  backgroundColor: getStatusColor(selectedOrder.status) + '20',
                  color: getStatusColor(selectedOrder.status)
                }}>
                  {getStatusText(selectedOrder.status)}
                </span>
              </div>
              <button
                onClick={() => setSelectedOrder(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#7f8c8d'
                }}
              >
                ✕
              </button>
            </div>

            {/* Информация о заявителе */}
            <div style={{ 
              backgroundColor: '#f8f9fa', 
              padding: '15px', 
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>👷 Информация о заявителе</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Бригадир</div>
                  <div style={{ fontWeight: '600' }}>{selectedOrder.foreman_name || `ID ${selectedOrder.foreman_id}`}</div>
                </div>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Дата создания</div>
                  <div style={{ fontWeight: '600' }}>{new Date(selectedOrder.created_at).toLocaleString('ru')}</div>
                </div>
              </div>
            </div>

            {/* Детали заявки */}
            <div style={{ 
              backgroundColor: '#fff', 
              border: '1px solid #ecf0f1',
              padding: '15px', 
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <h4 style={{ margin: '0 0 15px 0', color: '#2c3e50' }}>📋 Детали заявки</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Объект</div>
                  <div style={{ fontWeight: '600' }}>{selectedOrder.cost_object_name || `ID ${selectedOrder.cost_object_id}`}</div>
                </div>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Тип техники</div>
                  <div style={{ fontWeight: '600' }}>{getEquipmentTypeText(selectedOrder.equipment_type)}</div>
                </div>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Количество</div>
                  <div style={{ fontWeight: '600' }}>{selectedOrder.quantity} ед.</div>
                </div>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Период аренды</div>
                  <div style={{ fontWeight: '600' }}>
                    {new Date(selectedOrder.start_date).toLocaleDateString('ru')} - {new Date(selectedOrder.end_date).toLocaleDateString('ru')}
                  </div>
                </div>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Дней аренды</div>
                  <div style={{ fontWeight: '600' }}>{calculateDays(selectedOrder.start_date, selectedOrder.end_date)}</div>
                </div>
                {selectedOrder.hour_rate && (
                  <div>
                    <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Ставка в час</div>
                    <div style={{ fontWeight: '600' }}>{selectedOrder.hour_rate.toLocaleString('ru')} ₽/ч</div>
                  </div>
                )}
                {selectedOrder.hours_worked && (
                  <div>
                    <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Отработано часов</div>
                    <div style={{ fontWeight: '600' }}>{selectedOrder.hours_worked} ч</div>
                  </div>
                )}
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Итоговая стоимость</div>
                  <div style={{ fontWeight: '600', color: selectedOrder.total_cost ? '#27ae60' : '#95a5a6' }}>
                    {selectedOrder.total_cost ? `${selectedOrder.total_cost.toLocaleString('ru')} ₽` : 'Не указана'}
                  </div>
                </div>
              </div>
            </div>

            {selectedOrder.description && (
              <div style={{ 
                backgroundColor: '#fef9e7', 
                border: '1px solid #f9e79f',
                padding: '15px', 
                borderRadius: '8px',
                marginBottom: '20px'
              }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>💬 Описание работ</h4>
                <div>{selectedOrder.description}</div>
              </div>
            )}

            {selectedOrder.rejection_reason && (
              <div style={{ 
                backgroundColor: '#fdedec', 
                border: '1px solid #f5b7b1',
                padding: '15px', 
                borderRadius: '8px',
                marginBottom: '20px'
              }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#c0392b' }}>❌ Причина отклонения</h4>
                <div>{selectedOrder.rejection_reason}</div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSelectedOrder(null)}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#95a5a6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно установки стоимости */}
      {showCostModal && costOrder && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1001
        }}
        onClick={() => setShowCostModal(false)}
        >
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '12px',
            maxWidth: '400px',
            width: '95%',
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
          }}
          onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ margin: '0 0 20px 0' }}>💰 Установить стоимость</h3>
            <p style={{ color: '#7f8c8d', marginBottom: '15px' }}>
              Заявка #{costOrder.id}<br/>
              Техника: <strong>{getEquipmentTypeText(costOrder.equipment_type)}</strong>
            </p>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>Ставка за час (₽):</label>
              <input
                type="number"
                value={hourRate}
                onChange={(e) => setHourRate(e.target.value)}
                placeholder="Введите ставку"
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #ddd',
                  fontSize: '14px',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowCostModal(false)}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#95a5a6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Отмена
              </button>
              <button
                onClick={handleSetCost}
                disabled={!hourRate}
                style={{
                  padding: '10px 20px',
                  backgroundColor: hourRate ? '#27ae60' : '#bdc3c7',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: hourRate ? 'pointer' : 'not-allowed'
                }}
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
