import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../hooks/useAuth';

interface TimeSheet {
  id: number;
  brigade_id: number;
  brigade_name?: string;
  period_start: string;
  period_end: string;
  status: string;
  notes?: string;
  total_hours?: number;
  total_amount?: number;
  created_at: string;
}

export function TimeSheetsPage() {
  const { user } = useAuth();
  const [timesheets, setTimesheets] = useState<TimeSheet[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadTimesheets();
  }, []);

  const loadTimesheets = async () => {
    try {
      const data = await apiClient.get<TimeSheet[]>('/time-sheets/');
      setTimesheets(data);
    } catch (err) {
      console.error('Ошибка загрузки табелей:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'DRAFT': return '#95a5a6';
      case 'SUBMITTED': return '#3498db';
      case 'CORRECTED': return '#e67e22';
      case 'APPROVED': return '#2ecc71';
      default: return '#7f8c8d';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'DRAFT': return 'Черновик';
      case 'SUBMITTED': return 'На рассмотрении';
      case 'CORRECTED': return 'Откорректирован';
      case 'APPROVED': return 'Утверждён';
      default: return status;
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await apiClient.post(`/time-sheets/${id}/approve`);
      await loadTimesheets();
      alert('Табель утверждён');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка утверждения');
    }
  };

  const handleReject = async (id: number) => {
    const comment = prompt('Укажите причину отклонения:');
    if (!comment) return;

    try {
      await apiClient.post(`/time-sheets/${id}/reject`, { comment });
      await loadTimesheets();
      alert('Табель отклонён');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка отклонения');
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await fetch('http://192.168.0.235:8000/api/v1/time-sheets/template', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Ошибка скачивания шаблона');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `timesheet_template_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Ошибка скачивания шаблона:', err);
      alert('Ошибка скачивания шаблона');
    }
  };

  const filteredTimesheets = timesheets.filter(ts => {
    if (filter === 'all') return true;
    return ts.status === filter;
  });

  if (loading) {
    return <div>Загрузка...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>Табели рабочего времени бригад</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleDownloadTemplate}
            style={{
              padding: '12px 24px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 'bold'
            }}
          >
            📥 Скачать шаблон Excel
          </button>
          <label style={{
            padding: '12px 24px',
            backgroundColor: '#2ecc71',
            color: 'white',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'inline-block',
            fontSize: '14px',
            fontWeight: 'bold'
          }}>
            📤 Загрузить Excel
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  alert(`Выбран файл: ${file.name}\n\nФункция загрузки Excel табеля в разработке.\n\nИспользуйте Telegram Bot для отправки табелей!`);
                  e.target.value = '';
                }
              }}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {['all', 'DRAFT', 'SUBMITTED', 'CORRECTED', 'APPROVED'].map(status => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            style={{
              padding: '8px 16px',
              backgroundColor: filter === status ? '#2ecc71' : '#ecf0f1',
              color: filter === status ? 'white' : '#2c3e50',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            {status === 'all' ? 'Все' : getStatusText(status)}
          </button>
        ))}
      </div>

      {filteredTimesheets.length === 0 ? (
        <div style={{ 
          backgroundColor: 'white', 
          padding: '40px', 
          borderRadius: '8px',
          textAlign: 'center',
          color: '#7f8c8d'
        }}>
          Табели не найдены
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '15px' }}>
          {filteredTimesheets.map(ts => (
            <div
              key={ts.id}
              style={{
                backgroundColor: 'white',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                borderLeft: `4px solid ${getStatusColor(ts.status)}`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <h3 style={{ margin: 0, color: '#2c3e50' }}>Табель #{ts.id}</h3>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '500',
                      backgroundColor: getStatusColor(ts.status) + '20',
                      color: getStatusColor(ts.status)
                    }}>
                      {getStatusText(ts.status)}
                    </span>
                  </div>
                  
                  <div style={{ color: '#7f8c8d', fontSize: '14px', marginBottom: '10px' }}>
                    Бригада: <strong>{ts.brigade_name || `ID ${ts.brigade_id}`}</strong>
                    {' • '}
                    Период: <strong>
                      {new Date(ts.period_start).toLocaleDateString('ru')} - {new Date(ts.period_end).toLocaleDateString('ru')}
                    </strong>
                  </div>

                  {ts.total_hours && (
                    <div style={{ fontSize: '14px', marginBottom: '5px' }}>
                      Всего часов: <strong>{ts.total_hours} ч</strong>
                    </div>
                  )}

                  {ts.total_amount && (
                    <div style={{ fontSize: '14px', marginBottom: '10px' }}>
                      Сумма ФОТ: <strong>{ts.total_amount.toLocaleString('ru')} ₽</strong>
                    </div>
                  )}

                  {ts.notes && (
                    <div style={{ 
                      padding: '10px', 
                      backgroundColor: '#fff3cd', 
                      borderRadius: '4px',
                      fontSize: '13px',
                      marginTop: '10px',
                      whiteSpace: 'pre-wrap'
                    }}>
                      <strong>Примечания:</strong><br />
                      {ts.notes}
                    </div>
                  )}
                </div>

                {user?.roles.includes('HR_MANAGER') && ts.status === 'SUBMITTED' && (
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => handleApprove(ts.id)}
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
                      Утвердить
                    </button>
                    <button
                      onClick={() => handleReject(ts.id)}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#e74c3c',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '14px'
                      }}
                    >
                      Отклонить
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
