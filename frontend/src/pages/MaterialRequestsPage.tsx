import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../hooks/useAuth';

interface MaterialRequest {
  id: number;
  cost_object_id: number;
  cost_object_name?: string;
  foreman_id: number;
  foreman_name?: string;
  foreman_phone?: string;
  status: string;
  urgency: string;
  comment?: string;
  expected_delivery_date?: string;
  supplier?: string;
  order_number?: string;
  rejection_reason?: string;
  material_type?: string;
  delivery_time?: string;
  created_at: string;
  updated_at?: string;
  items: MaterialRequestItem[];
}

interface MaterialRequestItem {
  id: number;
  material_name: string;
  quantity: number;
  unit: string;
  comment?: string;
  distributed_quantity?: number;
}

// Все возможные статусы в правильном порядке workflow
// Backend использует русские значения статусов
const ALL_STATUSES = [
  { value: 'all', label: 'Все' },
  { value: 'НОВАЯ', label: 'Новая' },
  { value: 'НА СОГЛАСОВАНИИ', label: 'На согласовании' },
  { value: 'В ОБРАБОТКЕ', label: 'В обработке' },
  { value: 'ЗАКАЗАНО', label: 'Заказано' },
  { value: 'ЧАСТИЧНО ПОСТАВЛЕНО', label: 'Частично поставлено' },
  { value: 'ОТГРУЖЕНО', label: 'Отгружено' },
  { value: 'ВЫПОЛНЕНА', label: 'Выполнена' },
];

export function MaterialRequestsPage() {
  const { user } = useAuth();
  const [requests, setRequests] = useState<MaterialRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [selectedRequest, setSelectedRequest] = useState<MaterialRequest | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [statusUpdateRequest, setStatusUpdateRequest] = useState<MaterialRequest | null>(null);
  const [newStatus, setNewStatus] = useState('');

  useEffect(() => {
    loadRequests();
  }, [filter]);

  const loadRequests = async () => {
    try {
      const data = await apiClient.get<MaterialRequest[]>('/material-requests/');
      setRequests(data);
    } catch (err) {
      console.error('Ошибка загрузки заявок:', err);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка детальной информации о заявке (включая items)
  const loadRequestDetails = async (requestId: number) => {
    setLoadingDetails(true);
    try {
      const data = await apiClient.get<MaterialRequest>(`/material-requests/${requestId}`);
      setSelectedRequest(data);
    } catch (err) {
      console.error('Ошибка загрузки деталей заявки:', err);
      alert('Не удалось загрузить детали заявки');
    } finally {
      setLoadingDetails(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'НОВАЯ': '#3498db',
      'НА СОГЛАСОВАНИИ': '#f39c12',
      'В ОБРАБОТКЕ': '#9b59b6',
      'ЗАКАЗАНО': '#1abc9c',
      'ЧАСТИЧНО ПОСТАВЛЕНО': '#e67e22',
      'ОТГРУЖЕНО': '#27ae60',
      'ВЫПОЛНЕНА': '#2ecc71',
      'ОТКЛОНЕНА': '#e74c3c',
      'ОТМЕНЕНА': '#95a5a6',
    };
    return colors[status] || '#95a5a6';
  };

  const getStatusText = (status: string) => {
    // Backend возвращает русские статусы, просто показываем как есть
    return status;
  };

  const getUrgencyColor = (urgency: string) => {
    const colors: Record<string, string> = {
      'critical': '#c0392b',
      'CRITICAL': '#c0392b',
      'urgent': '#e74c3c',
      'URGENT': '#e74c3c',
      'high': '#f39c12',
      'HIGH': '#f39c12',
      'normal': '#3498db',
      'NORMAL': '#3498db',
      'low': '#95a5a6',
      'LOW': '#95a5a6',
    };
    return colors[urgency] || '#95a5a6';
  };

  const getUrgencyText = (urgency: string) => {
    const texts: Record<string, string> = {
      'critical': 'Критичная',
      'CRITICAL': 'Критичная',
      'urgent': 'Срочная',
      'URGENT': 'Срочная',
      'high': 'Высокая',
      'HIGH': 'Высокая',
      'normal': 'Обычная',
      'NORMAL': 'Обычная',
      'low': 'Низкая',
      'LOW': 'Низкая',
    };
    return texts[urgency] || urgency;
  };

  const getMaterialTypeText = (type?: string) => {
    if (!type) return 'Не указан';
    const types: Record<string, string> = {
      'regular': 'Обычные материалы',
      'inert': 'Инертные материалы',
    };
    return types[type] || type;
  };

  // Проверка прав на изменение статуса
  const canChangeStatus = () => {
    if (!user) return false;
    return user.roles.some(role => 
      ['ADMIN', 'MANAGER', 'MATERIALS_MANAGER', 'PROCUREMENT_MANAGER'].includes(role)
    );
  };

  // Получить доступные статусы для перехода
  const getAvailableStatuses = (currentStatus: string) => {
    const transitions: Record<string, string[]> = {
      'НОВАЯ': ['НА СОГЛАСОВАНИИ', 'ОТКЛОНЕНА'],
      'НА СОГЛАСОВАНИИ': ['В ОБРАБОТКЕ', 'ОТКЛОНЕНА'],
      'В ОБРАБОТКЕ': ['ЗАКАЗАНО', 'ОТКЛОНЕНА'],
      'ЗАКАЗАНО': ['ЧАСТИЧНО ПОСТАВЛЕНО', 'ОТГРУЖЕНО'],
      'ЧАСТИЧНО ПОСТАВЛЕНО': ['ОТГРУЖЕНО'],
      'ОТГРУЖЕНО': ['ВЫПОЛНЕНА'],
    };
    return transitions[currentStatus] || [];
  };

  const handleApprove = async (id: number) => {
    try {
      await apiClient.post(`/material-requests/${id}/approve`, {});
      await loadRequests();
      alert('Заявка согласована');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка согласования');
    }
  };

  const handleProcess = async (id: number) => {
    try {
      await apiClient.post(`/material-requests/${id}/process`, {});
      await loadRequests();
      alert('Заявка взята в обработку');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка обработки');
    }
  };

  const handleStatusChange = async () => {
    if (!statusUpdateRequest || !newStatus) return;
    
    try {
      // Вызов соответствующего endpoint в зависимости от статуса (используем русские значения)
      if (newStatus === 'НА СОГЛАСОВАНИИ') {
        await apiClient.post(`/material-requests/${statusUpdateRequest.id}/approve`, {});
      } else if (newStatus === 'В ОБРАБОТКЕ') {
        await apiClient.post(`/material-requests/${statusUpdateRequest.id}/process`, {});
      } else if (newStatus === 'ЗАКАЗАНО') {
        await apiClient.post(`/material-requests/${statusUpdateRequest.id}/order`, {
          supplier: 'Указать поставщика',
          order_number: 'Указать номер'
        });
      } else if (newStatus === 'ОТГРУЖЕНО' || newStatus === 'ЧАСТИЧНО ПОСТАВЛЕНО') {
        await apiClient.post(`/material-requests/${statusUpdateRequest.id}/deliver`);
      } else if (newStatus === 'ВЫПОЛНЕНА') {
        await apiClient.post(`/material-requests/${statusUpdateRequest.id}/complete`);
      } else if (newStatus === 'ОТКЛОНЕНА') {
        await apiClient.post(`/material-requests/${statusUpdateRequest.id}/reject`, {
          reason: 'Причина отклонения'
        });
      }
      
      await loadRequests();
      setShowStatusModal(false);
      setStatusUpdateRequest(null);
      setNewStatus('');
      alert('Статус обновлён');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка обновления статуса');
    }
  };

  const openStatusModal = (request: MaterialRequest) => {
    setStatusUpdateRequest(request);
    setNewStatus('');
    setShowStatusModal(true);
  };

  const filteredRequests = requests.filter(req => {
    if (filter === 'all') return true;
    return req.status === filter;
  });

  // Подсчёт заявок по статусам
  const statusCounts = ALL_STATUSES.reduce((acc, status) => {
    if (status.value === 'all') {
      acc[status.value] = requests.length;
    } else {
      acc[status.value] = requests.filter(r => r.status === status.value).length;
    }
    return acc;
  }, {} as Record<string, number>);

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Загрузка...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>📦 Заявки на материалы</h1>
        <button 
          onClick={() => alert('Используйте Telegram Bot для создания заявок на материалы!')}
          style={{
            padding: '12px 24px',
            backgroundColor: '#3498db',
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
              backgroundColor: filter === status.value ? '#3498db' : '#ecf0f1',
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

      {filteredRequests.length === 0 ? (
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
          {filteredRequests.map(request => (
            <div
              key={request.id}
              style={{
                backgroundColor: 'white',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                borderLeft: `4px solid ${getStatusColor(request.status)}`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '15px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', flexWrap: 'wrap' }}>
                    <h3 style={{ margin: 0, color: '#2c3e50' }}>Заявка #{request.id}</h3>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '500',
                      backgroundColor: getStatusColor(request.status) + '20',
                      color: getStatusColor(request.status)
                    }}>
                      {getStatusText(request.status)}
                    </span>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '500',
                      backgroundColor: getUrgencyColor(request.urgency) + '20',
                      color: getUrgencyColor(request.urgency)
                    }}>
                      {getUrgencyText(request.urgency)}
                    </span>
                    {request.material_type && (
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '500',
                        backgroundColor: request.material_type === 'inert' ? '#f39c1220' : '#3498db20',
                        color: request.material_type === 'inert' ? '#f39c12' : '#3498db'
                      }}>
                        {request.material_type === 'inert' ? '🪨 Инертные' : '🏗️ Обычные'}
                      </span>
                    )}
                  </div>
                  <div style={{ color: '#7f8c8d', fontSize: '14px' }}>
                    📍 <strong>{request.cost_object_name || `Объект ${request.cost_object_id}`}</strong>
                    {' • '}
                    👷 <strong>{request.foreman_name || `Бригадир ${request.foreman_id}`}</strong>
                    {' • '}
                    📅 {new Date(request.created_at).toLocaleDateString('ru')}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {user?.roles.some(r => ['PROCUREMENT_MANAGER', 'MANAGER', 'ADMIN'].includes(r)) && request.status === 'НОВАЯ' && (
                    <button
                      onClick={() => handleApprove(request.id)}
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
                      ✓ Согласовать
                    </button>
                  )}
                  {user?.roles.some(r => ['MATERIALS_MANAGER', 'MANAGER', 'ADMIN'].includes(r)) && request.status === 'НА СОГЛАСОВАНИИ' && (
                    <button
                      onClick={() => handleProcess(request.id)}
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
                      📋 В работу
                    </button>
                  )}
                  {canChangeStatus() && getAvailableStatuses(request.status).length > 0 && (
                    <button
                      onClick={() => openStatusModal(request)}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#f39c12',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '14px'
                      }}
                    >
                      ⚡ Статус
                    </button>
                  )}
                  <button
                    onClick={() => loadRequestDetails(request.id)}
                    disabled={loadingDetails}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#3498db',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: loadingDetails ? 'wait' : 'pointer',
                      fontSize: '14px',
                      opacity: loadingDetails ? 0.7 : 1
                    }}
                  >
                    {loadingDetails ? '⏳ Загрузка...' : '👁 Подробнее'}
                  </button>
                </div>
              </div>

              {request.comment && (
                <div style={{ 
                  padding: '10px', 
                  backgroundColor: '#f8f9fa', 
                  borderRadius: '4px',
                  fontSize: '14px',
                  marginBottom: '10px'
                }}>
                  💬 <strong>Комментарий:</strong> {request.comment}
                </div>
              )}

              <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', fontSize: '14px', marginBottom: '10px' }}>
                {request.expected_delivery_date && (
                  <div style={{ color: '#7f8c8d' }}>
                    📅 Ожидаемая дата: <strong>{new Date(request.expected_delivery_date).toLocaleDateString('ru')}</strong>
                  </div>
                )}
                {request.delivery_time && (
                  <div style={{ color: '#7f8c8d' }}>
                    🕐 Время доставки: <strong>{request.delivery_time}</strong>
                  </div>
                )}
                {request.supplier && (
                  <div style={{ color: '#7f8c8d' }}>
                    🏭 Поставщик: <strong>{request.supplier}</strong>
                  </div>
                )}
              </div>

              <div style={{ borderTop: '1px solid #ecf0f1', paddingTop: '10px' }}>
                <strong style={{ fontSize: '14px', color: '#7f8c8d' }}>📦 Материалы ({request.items?.length || 0}):</strong>
                <div style={{ marginTop: '8px', display: 'grid', gap: '5px' }}>
                  {request.items?.slice(0, 3).map((item, idx) => (
                    <div key={idx} style={{ fontSize: '14px', color: '#2c3e50' }}>
                      • {item.material_name} — {item.quantity} {item.unit}
                    </div>
                  ))}
                  {request.items?.length > 3 && (
                    <div style={{ fontSize: '14px', color: '#7f8c8d', fontStyle: 'italic' }}>
                      ... и ещё {request.items.length - 3} позиций
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Модальное окно "Подробнее" */}
      {selectedRequest && (
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
        onClick={() => setSelectedRequest(null)}
        >
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '12px',
            maxWidth: '700px',
            width: '95%',
            maxHeight: '85vh',
            overflow: 'auto',
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
          }}
          onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
              <div>
                <h2 style={{ margin: 0, marginBottom: '10px' }}>📦 Заявка #{selectedRequest.id}</h2>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <span style={{
                    padding: '6px 14px',
                    borderRadius: '12px',
                    fontSize: '13px',
                    fontWeight: '600',
                    backgroundColor: getStatusColor(selectedRequest.status) + '20',
                    color: getStatusColor(selectedRequest.status)
                  }}>
                    {getStatusText(selectedRequest.status)}
                  </span>
                  <span style={{
                    padding: '6px 14px',
                    borderRadius: '12px',
                    fontSize: '13px',
                    fontWeight: '600',
                    backgroundColor: getUrgencyColor(selectedRequest.urgency) + '20',
                    color: getUrgencyColor(selectedRequest.urgency)
                  }}>
                    {getUrgencyText(selectedRequest.urgency)}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedRequest(null)}
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
                  <div style={{ fontWeight: '600' }}>{selectedRequest.foreman_name || `ID ${selectedRequest.foreman_id}`}</div>
                </div>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Дата создания</div>
                  <div style={{ fontWeight: '600' }}>{new Date(selectedRequest.created_at).toLocaleString('ru')}</div>
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
                  <div style={{ fontWeight: '600' }}>{selectedRequest.cost_object_name || `ID ${selectedRequest.cost_object_id}`}</div>
                </div>
                <div>
                  <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Тип материалов</div>
                  <div style={{ fontWeight: '600' }}>{getMaterialTypeText(selectedRequest.material_type)}</div>
                </div>
                {selectedRequest.expected_delivery_date && (
                  <div>
                    <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Ожидаемая дата поставки</div>
                    <div style={{ fontWeight: '600' }}>{new Date(selectedRequest.expected_delivery_date).toLocaleDateString('ru')}</div>
                  </div>
                )}
                {selectedRequest.supplier && (
                  <div>
                    <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Поставщик</div>
                    <div style={{ fontWeight: '600' }}>{selectedRequest.supplier}</div>
                  </div>
                )}
              </div>
            </div>

            {selectedRequest.comment && (
              <div style={{ 
                backgroundColor: '#fef9e7', 
                border: '1px solid #f9e79f',
                padding: '15px', 
                borderRadius: '8px',
                marginBottom: '20px'
              }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>💬 Комментарий</h4>
                <div>{selectedRequest.comment}</div>
              </div>
            )}
            
            <h4 style={{ margin: '0 0 15px 0', color: '#2c3e50' }}>📦 Материалы ({selectedRequest.items?.length || 0})</h4>
            {selectedRequest.items && selectedRequest.items.length > 0 ? (
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6', fontWeight: '600' }}>Наименование</th>
                    <th style={{ padding: '12px', textAlign: 'right', borderBottom: '2px solid #dee2e6', fontWeight: '600' }}>Количество</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6', fontWeight: '600' }}>Ед. изм.</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedRequest.items.map((item, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <td style={{ padding: '12px' }}>{item.material_name}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: '500' }}>{item.quantity}</td>
                      <td style={{ padding: '12px' }}>{item.unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ 
                padding: '20px', 
                backgroundColor: '#f8f9fa', 
                borderRadius: '8px', 
                textAlign: 'center',
                color: '#7f8c8d',
                marginBottom: '20px'
              }}>
                ⏳ Загрузка материалов...
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSelectedRequest(null)}
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

      {/* Модальное окно изменения статуса */}
      {showStatusModal && statusUpdateRequest && (
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
        onClick={() => setShowStatusModal(false)}
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
            <h3 style={{ margin: '0 0 20px 0' }}>⚡ Изменить статус</h3>
            <p style={{ color: '#7f8c8d', marginBottom: '15px' }}>
              Заявка #{statusUpdateRequest.id}<br/>
              Текущий статус: <strong>{getStatusText(statusUpdateRequest.status)}</strong>
            </p>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>Новый статус:</label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #ddd',
                  fontSize: '14px'
                }}
              >
                <option value="">Выберите статус</option>
                {getAvailableStatuses(statusUpdateRequest.status).map(status => (
                  <option key={status} value={status}>{getStatusText(status)}</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowStatusModal(false)}
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
                onClick={handleStatusChange}
                disabled={!newStatus}
                style={{
                  padding: '10px 20px',
                  backgroundColor: newStatus ? '#27ae60' : '#bdc3c7',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: newStatus ? 'pointer' : 'not-allowed'
                }}
              >
                Применить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
