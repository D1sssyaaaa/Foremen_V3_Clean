import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

interface ObjectStats {
  object_id: number;
  object_name: string;
  object_code: string;
  material_requests: {
    count: number;
    total: number;
    by_status: Record<string, number>;
  };
  equipment_orders: {
    count: number;
    total: number;
  };
  upd_documents: {
    count: number;
    total: number;
  };
  timesheets: {
    count: number;
    labor_costs_total: number;
  };
  total_costs: number;
  budget: {
    material_budget: number;
    labor_budget: number;
    total_budget: number;
  };
}

interface CostDetail {
  id: number;
  date: string;
  amount: number;
  description: string;
  reference_id?: number;
  reference_type?: string;
}

interface ObjectCosts {
  object_id: number;
  object_name: string;
  materials: CostDetail[];
  equipment: CostDetail[];
  labor: CostDetail[];
}

interface ObjectDetailsModalProps {
  objectId: number;
  onClose: () => void;
  onViewFull: () => void;
}

export function ObjectDetailsModal({ objectId, onClose, onViewFull }: ObjectDetailsModalProps) {
  const [stats, setStats] = useState<ObjectStats | null>(null);
  const [costs, setCosts] = useState<ObjectCosts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    loadStats();
    loadCosts(); // Автоматически загружаем детали при открытии
  }, [objectId]);

  const loadStats = async () => {
    setError(null);
    try {
      const data = await apiClient.get<ObjectStats>(`/objects/${objectId}/stats`);
      setStats(data);
    } catch (err: any) {
      console.error('Ошибка загрузки статистики:', err);
      if (err.response?.status === 403) {
        setError('Недостаточно прав для просмотра');
      } else if (err.response?.status === 404) {
        setError('Объект не найден');
      } else {
        setError(`Ошибка: ${err.message || 'Не удалось загрузить данные'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadCosts = async () => {
    try {
      const data = await apiClient.get<ObjectCosts>(`/objects/${objectId}/costs`);
      setCosts(data);
      setShowDetails(true);
    } catch (err: any) {
      console.error('Ошибка загрузки затрат:', err);
      alert('Не удалось загрузить детали затрат');
    }
  };

  if (loading) {
    return (
      <div style={overlayStyle} onClick={onClose}>
        <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
          <div style={{ textAlign: 'center', padding: '40px' }}>Загрузка...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={overlayStyle} onClick={onClose}>
        <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ color: '#e74c3c', marginBottom: '15px' }}>{error}</div>
            <button onClick={onClose} style={{
              padding: '10px 20px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}>
              Закрыть
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const budgetUsage = stats.budget.total_budget > 0
    ? (stats.total_costs / stats.budget.total_budget) * 100
    : 0;

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={headerStyle}>
          <div>
            <h2 style={{ margin: 0, marginBottom: '5px' }}>{stats.object_name}</h2>
            <div style={{ color: '#7f8c8d', fontSize: '14px' }}>Код: {stats.object_code}</div>
          </div>
          <button onClick={onClose} style={closeButtonStyle}>✕</button>
        </div>

        {/* Body */}
        <div style={bodyStyle}>
          {/* Бюджет и использование */}
          <div style={sectionStyle}>
            <h3 style={sectionTitleStyle}>💰 Бюджет и затраты</h3>
            <div style={{ marginBottom: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <span>Общий бюджет:</span>
                <strong>{stats.budget.total_budget.toLocaleString('ru')} ₽</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <span>Использовано:</span>
                <strong style={{ color: budgetUsage > 90 ? '#e74c3c' : '#27ae60' }}>
                  {stats.total_costs.toLocaleString('ru')} ₽
                </strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span>Остаток:</span>
                <strong>{(stats.budget.total_budget - stats.total_costs).toLocaleString('ru')} ₽</strong>
              </div>
              {/* Progress bar */}
              <div style={progressBarBgStyle}>
                <div
                  style={{
                    ...progressBarFillStyle,
                    width: `${Math.min(budgetUsage, 100)}%`,
                    backgroundColor: budgetUsage > 90 ? '#e74c3c' : budgetUsage > 70 ? '#f39c12' : '#27ae60'
                  }}
                />
              </div>
              <div style={{ textAlign: 'center', marginTop: '5px', fontSize: '12px', color: '#7f8c8d' }}>
                {budgetUsage.toFixed(1)}% использовано
              </div>
            </div>
          </div>

          {/* Статистика по категориям */}
          <div style={statsGridStyle}>
            {/* Материалы */}
            <div style={statCardStyle}>
              <div style={{ fontSize: '24px', marginBottom: '5px' }}>📦</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '5px' }}>
                {stats.material_requests.count}
              </div>
              <div style={{ color: '#7f8c8d', fontSize: '14px', marginBottom: '5px' }}>Заявок на материалы</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#3498db' }}>
                {stats.material_requests.total.toLocaleString('ru')} ₽
              </div>
            </div>

            {/* Техника */}
            <div style={statCardStyle}>
              <div style={{ fontSize: '24px', marginBottom: '5px' }}>🚜</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '5px' }}>
                {stats.equipment_orders.count}
              </div>
              <div style={{ color: '#7f8c8d', fontSize: '14px', marginBottom: '5px' }}>Заявок на технику</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#3498db' }}>
                {stats.equipment_orders.total.toLocaleString('ru')} ₽
              </div>
            </div>

            {/* РТБ */}
            <div style={statCardStyle}>
              <div style={{ fontSize: '24px', marginBottom: '5px' }}>👷</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '5px' }}>
                {stats.timesheets.count}
              </div>
              <div style={{ color: '#7f8c8d', fontSize: '14px', marginBottom: '5px' }}>Табелей РТБ</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#3498db' }}>
                {stats.timesheets.labor_costs_total.toLocaleString('ru')} ₽
              </div>
            </div>

            {/* УПД */}
            <div style={statCardStyle}>
              <div style={{ fontSize: '24px', marginBottom: '5px' }}>📄</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '5px' }}>
                {stats.upd_documents.count}
              </div>
              <div style={{ color: '#7f8c8d', fontSize: '14px', marginBottom: '5px' }}>УПД документов</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#3498db' }}>
                {stats.upd_documents.total.toLocaleString('ru')} ₽
              </div>
            </div>
          </div>

          {/* Распределение затрат (простой график) */}
          <div style={sectionStyle}>
            <h3 style={sectionTitleStyle}>📊 Распределение затрат</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {stats.material_requests.total > 0 && (
                <CostBar
                  label="Материалы"
                  value={stats.material_requests.total}
                  total={stats.total_costs}
                  color="#3498db"
                />
              )}
              {stats.equipment_orders.total > 0 && (
                <CostBar
                  label="Техника"
                  value={stats.equipment_orders.total}
                  total={stats.total_costs}
                  color="#f39c12"
                />
              )}
              {stats.timesheets.labor_costs_total > 0 && (
                <CostBar
                  label="РТБ"
                  value={stats.timesheets.labor_costs_total}
                  total={stats.total_costs}
                  color="#27ae60"
                />
              )}
              {stats.upd_documents.total > 0 && (
                <CostBar
                  label="УПД"
                  value={stats.upd_documents.total}
                  total={stats.total_costs}
                  color="#9b59b6"
                />
              )}
            </div>
          </div>

          {/* Детальные таблицы затрат */}
          {showDetails && costs && (
            <div style={sectionStyle}>
              <h3 style={sectionTitleStyle}>📋 Детализация затрат</h3>

              {/* Материалы */}
              {costs.materials.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <h4 style={{ fontSize: '16px', marginBottom: '10px', color: '#2c3e50' }}>📦 Материалы</h4>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>Дата</th>
                          <th style={thStyle}>Описание</th>
                          <th style={thStyle}>Сумма</th>
                        </tr>
                      </thead>
                      <tbody>
                        {costs.materials.map((cost) => (
                          <tr key={cost.id}>
                            <td style={tdStyle}>{new Date(cost.date).toLocaleDateString('ru')}</td>
                            <td style={tdStyle}>{cost.description || '—'}</td>
                            <td style={tdStyle}>{cost.amount.toLocaleString('ru')} ₽</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Техника */}
              {costs.equipment.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <h4 style={{ fontSize: '16px', marginBottom: '10px', color: '#2c3e50' }}>🚜 Техника</h4>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>Дата</th>
                          <th style={thStyle}>Описание</th>
                          <th style={thStyle}>Сумма</th>
                        </tr>
                      </thead>
                      <tbody>
                        {costs.equipment.map((cost) => (
                          <tr key={cost.id}>
                            <td style={tdStyle}>{new Date(cost.date).toLocaleDateString('ru')}</td>
                            <td style={tdStyle}>{cost.description || '—'}</td>
                            <td style={tdStyle}>{cost.amount.toLocaleString('ru')} ₽</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* РТБ */}
              {costs.labor.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <h4 style={{ fontSize: '16px', marginBottom: '10px', color: '#2c3e50' }}>👷 РТБ</h4>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>Дата</th>
                          <th style={thStyle}>Описание</th>
                          <th style={thStyle}>Сумма</th>
                        </tr>
                      </thead>
                      <tbody>
                        {costs.labor.map((cost) => (
                          <tr key={cost.id}>
                            <td style={tdStyle}>{new Date(cost.date).toLocaleDateString('ru')}</td>
                            <td style={tdStyle}>{cost.description || '—'}</td>
                            <td style={tdStyle}>{cost.amount.toLocaleString('ru')} ₽</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {costs.materials.length === 0 && costs.equipment.length === 0 && costs.labor.length === 0 && (
                <div style={{ textAlign: 'center', color: '#7f8c8d', padding: '20px' }}>
                  Нет детальных записей затрат
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={footerStyle}>
          <button onClick={onClose} style={secondaryButtonStyle}>
            Закрыть
          </button>
          <button onClick={onViewFull} style={primaryButtonStyle}>
            Открыть полный отчет →
          </button>
        </div>
      </div>
    </div>
  );
}

function CostBar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const percentage = total > 0 ? (value / total) * 100 : 0;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', fontSize: '14px' }}>
        <span>{label}</span>
        <span style={{ fontWeight: 'bold' }}>
          {value.toLocaleString('ru')} ₽ ({percentage.toFixed(1)}%)
        </span>
      </div>
      <div style={progressBarBgStyle}>
        <div style={{ ...progressBarFillStyle, width: `${percentage}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

// Styles
const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.5)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
};

const modalStyle: React.CSSProperties = {
  backgroundColor: 'white',
  borderRadius: '12px',
  width: '90%',
  maxWidth: '900px',
  maxHeight: '90vh',
  display: 'flex',
  flexDirection: 'column',
  boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
};

const headerStyle: React.CSSProperties = {
  padding: '24px',
  borderBottom: '1px solid #ecf0f1',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'start',
};

const closeButtonStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  fontSize: '24px',
  cursor: 'pointer',
  color: '#7f8c8d',
  padding: '0',
  width: '32px',
  height: '32px',
};

const bodyStyle: React.CSSProperties = {
  padding: '24px',
  overflowY: 'auto',
  flex: 1,
};

const sectionStyle: React.CSSProperties = {
  marginBottom: '24px',
};

const sectionTitleStyle: React.CSSProperties = {
  margin: '0 0 15px 0',
  fontSize: '18px',
  color: '#2c3e50',
};

const statsGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
  gap: '15px',
  marginBottom: '24px',
};

const statCardStyle: React.CSSProperties = {
  backgroundColor: '#f8f9fa',
  padding: '15px',
  borderRadius: '8px',
  textAlign: 'center',
};

const progressBarBgStyle: React.CSSProperties = {
  backgroundColor: '#ecf0f1',
  borderRadius: '10px',
  height: '20px',
  overflow: 'hidden',
};

const progressBarFillStyle: React.CSSProperties = {
  height: '100%',
  transition: 'width 0.3s ease',
  borderRadius: '10px',
};

const footerStyle: React.CSSProperties = {
  padding: '16px 24px',
  borderTop: '1px solid #ecf0f1',
  display: 'flex',
  justifyContent: 'flex-end',
  gap: '12px',
};

const primaryButtonStyle: React.CSSProperties = {
  padding: '10px 20px',
  backgroundColor: '#3498db',
  color: 'white',
  border: 'none',
  borderRadius: '6px',
  cursor: 'pointer',
  fontSize: '14px',
  fontWeight: '500',
};

const secondaryButtonStyle: React.CSSProperties = {
  padding: '10px 20px',
  backgroundColor: 'transparent',
  color: '#7f8c8d',
  border: '1px solid #bdc3c7',
  borderRadius: '6px',
  cursor: 'pointer',
  fontSize: '14px',
};

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: '14px',
};

const thStyle: React.CSSProperties = {
  backgroundColor: '#f8f9fa',
  padding: '12px',
  textAlign: 'left',
  borderBottom: '2px solid #dee2e6',
  fontWeight: '600',
  color: '#2c3e50',
};

const tdStyle: React.CSSProperties = {
  padding: '12px',
  borderBottom: '1px solid #dee2e6',
};
