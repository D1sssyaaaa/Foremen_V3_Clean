import React, { useEffect, useState } from 'react';
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

interface MaterialItem {
  id: number;
  name: string;
  quantity: number;
  unit: string;
  price: number;
  amount: number;
}

interface CostDetail {
  id: number | string;
  date: string | null;
  amount: number;
  description: string;
  document_number?: string;
  type?: string;
  hours?: number;
  items?: MaterialItem[];
}

interface CostSummary {
  materials_total: number;
  equipment_deliveries_total: number;
  labor_total: number;
  other_total: number;
  work_total: number;
  grand_total: number;
}

interface ObjectCosts {
  object_id: number;
  object_name: string;
  summary: CostSummary;
  materials: CostDetail[];
  equipment_deliveries: CostDetail[];
  labor: CostDetail[];
  other: CostDetail[];
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
  const [expandedRows, setExpandedRows] = useState<Set<string | number>>(new Set());

  const toggleRow = (id: string | number) => {
    setExpandedRows(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

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
          {/* Новый Финансовый Дашборд */}
          {/* Финансовая таблица План/Факт */}
          {costs && stats && (
            <div style={{ marginBottom: '30px', overflow: 'hidden', borderRadius: '8px', border: '1px solid #e0e0e0', backgroundColor: '#fff' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'right' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa', color: '#7f8c8d', fontSize: '12px', textTransform: 'uppercase' }}>
                    <th style={{ padding: '12px 16px', textAlign: 'left' }}>Категория</th>
                    <th style={{ padding: '12px 16px' }}>Сумма по договору</th>
                    <th style={{ padding: '12px 16px' }}>Факт затрат</th>
                    <th style={{ padding: '12px 16px' }}>Разница</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Строка Материалы */}
                  <tr style={{ borderBottom: '1px solid #ecf0f1' }}>
                    <td style={{ padding: '12px 16px', textAlign: 'left', fontWeight: '500' }}>Материалы</td>
                    <td style={{ padding: '12px 16px' }}>{stats.budget.material_budget.toLocaleString('ru')} ₽</td>
                    <td style={{ padding: '12px 16px', color: '#2c3e50' }}>{costs.summary.materials_total.toLocaleString('ru')} ₽</td>
                    <td style={{ padding: '12px 16px', fontWeight: 'bold', color: (stats.budget.material_budget - costs.summary.materials_total) >= 0 ? '#27ae60' : '#e74c3c' }}>
                      {(stats.budget.material_budget - costs.summary.materials_total).toLocaleString('ru')} ₽
                    </td>
                  </tr>
                  {/* Строка Работы */}
                  <tr style={{ borderBottom: '1px solid #ecf0f1' }}>
                    <td style={{ padding: '12px 16px', textAlign: 'left', fontWeight: '500' }}>Работы</td>
                    <td style={{ padding: '12px 16px' }}>{stats.budget.labor_budget.toLocaleString('ru')} ₽</td>
                    <td style={{ padding: '12px 16px', color: '#2c3e50' }}>{costs.summary.work_total.toLocaleString('ru')} ₽</td>
                    <td style={{ padding: '12px 16px', fontWeight: 'bold', color: (stats.budget.labor_budget - costs.summary.work_total) >= 0 ? '#27ae60' : '#e74c3c' }}>
                      {(stats.budget.labor_budget - costs.summary.work_total).toLocaleString('ru')} ₽
                    </td>
                  </tr>
                  {/* Итого */}
                  <tr style={{ backgroundColor: '#fdfdfd', fontWeight: 'bold', fontSize: '15px' }}>
                    <td style={{ padding: '16px', textAlign: 'left' }}>ИТОГО</td>
                    <td style={{ padding: '16px' }}>{stats.budget.total_budget.toLocaleString('ru')} ₽</td>
                    <td style={{ padding: '16px' }}>{costs.summary.grand_total.toLocaleString('ru')} ₽</td>
                    <td style={{ padding: '16px', color: (stats.budget.total_budget - costs.summary.grand_total) >= 0 ? '#27ae60' : '#e74c3c' }}>
                      {(stats.budget.total_budget - costs.summary.grand_total).toLocaleString('ru')} ₽
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Свод и мини-таблицы затрат (как в Google Sheets) */}
          {showDetails && costs && (
            <div style={sectionStyle}>

              {/* 4 мини-таблицы в сетке 2x2 */}
              <div style={miniTablesGridStyle}>
                {/* 1. Зарплата рабочих (РТБ) */}
                <div style={miniTableContainerStyle}>
                  <div style={miniTableHeaderStyle}>ЗАРПЛАТА РАБОЧИХ</div>
                  <table style={miniTableStyle}>
                    <thead>
                      <tr>
                        <th style={miniThStyle}>ВИД РАБОТ</th>
                        <th style={miniThStyle}>ДАТА</th>
                        <th style={miniThStyle}>СУММА ОПЛАТЫ</th>
                      </tr>
                    </thead>
                    <tbody>
                      {costs.labor.length > 0 ? costs.labor.slice(0, 10).map((cost) => (
                        <tr key={cost.id}>
                          <td style={miniTdStyle}>{cost.description || '—'}</td>
                          <td style={miniTdStyle}>{cost.date || '—'}</td>
                          <td style={miniTdStyle}>{cost.amount.toLocaleString('ru')} ₽</td>
                        </tr>
                      )) : (
                        <tr><td colSpan={3} style={{ ...miniTdStyle, textAlign: 'center', color: '#999' }}>Нет данных</td></tr>
                      )}
                    </tbody>
                    <tfoot>
                      <tr style={{ backgroundColor: '#f0f0f0' }}>
                        <td colSpan={2} style={{ ...miniTdStyle, fontWeight: 'bold' }}>сумма</td>
                        <td style={{ ...miniTdStyle, fontWeight: 'bold' }}>{costs.summary.labor_total.toLocaleString('ru')} ₽</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>

                {/* 2. Иные затраты */}
                <div style={miniTableContainerStyle}>
                  <div style={miniTableHeaderStyle}>ИНЫЕ ЗАТРАТЫ</div>
                  <table style={miniTableStyle}>
                    <thead>
                      <tr>
                        <th style={miniThStyle}>ВИД ЗАТРАТ</th>
                        <th style={miniThStyle}>ДАТА</th>
                        <th style={miniThStyle}>СУММА ОПЛАТЫ</th>
                      </tr>
                    </thead>
                    <tbody>
                      {costs.other.length > 0 ? costs.other.slice(0, 10).map((cost) => (
                        <tr key={cost.id}>
                          <td style={miniTdStyle}>{cost.description || '—'}</td>
                          <td style={miniTdStyle}>{cost.date ? new Date(cost.date).toLocaleDateString('ru') : '—'}</td>
                          <td style={miniTdStyle}>{cost.amount.toLocaleString('ru')} ₽</td>
                        </tr>
                      )) : (
                        <tr><td colSpan={3} style={{ ...miniTdStyle, textAlign: 'center', color: '#999' }}>Нет данных</td></tr>
                      )}
                    </tbody>
                    <tfoot>
                      <tr style={{ backgroundColor: '#f0f0f0' }}>
                        <td colSpan={2} style={{ ...miniTdStyle, fontWeight: 'bold' }}>сумма</td>
                        <td style={{ ...miniTdStyle, fontWeight: 'bold' }}>{costs.summary.other_total.toLocaleString('ru')} ₽</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>

                {/* 3. Техника и доставки */}
                <div style={miniTableContainerStyle}>
                  <div style={miniTableHeaderStyle}>ОПЛАТА СПЕЦТЕХНИКИ, ДОСТАВОК</div>
                  <table style={miniTableStyle}>
                    <thead>
                      <tr>
                        <th style={miniThStyle}>ВИД РАБОТЫ ТЕХНИКИ</th>
                        <th style={miniThStyle}>ДАТА</th>
                        <th style={miniThStyle}>СУММА ОПЛАТЫ</th>
                      </tr>
                    </thead>
                    <tbody>
                      {costs.equipment_deliveries.length > 0 ? costs.equipment_deliveries.slice(0, 10).map((cost) => (
                        <tr key={cost.id}>
                          <td style={miniTdStyle}>{cost.description || '—'}</td>
                          <td style={miniTdStyle}>{cost.date ? new Date(cost.date).toLocaleDateString('ru') : '—'}</td>
                          <td style={miniTdStyle}>{cost.amount.toLocaleString('ru')} ₽</td>
                        </tr>
                      )) : (
                        <tr><td colSpan={3} style={{ ...miniTdStyle, textAlign: 'center', color: '#999' }}>Нет данных</td></tr>
                      )}
                    </tbody>
                    <tfoot>
                      <tr style={{ backgroundColor: '#f0f0f0' }}>
                        <td colSpan={2} style={{ ...miniTdStyle, fontWeight: 'bold' }}>сумма</td>
                        <td style={{ ...miniTdStyle, fontWeight: 'bold' }}>{costs.summary.equipment_deliveries_total.toLocaleString('ru')} ₽</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>

                {/* 4. Закупка материала */}
                <div style={miniTableContainerStyle}>
                  <div style={{ ...miniTableHeaderStyle, backgroundColor: '#c6efce' }}>ЗАКУПКА МАТЕРИАЛА</div>
                  <table style={miniTableStyle}>
                    <thead>
                      <tr>
                        <th style={miniThStyle}>НАИМЕНОВАНИЕ ПОСТАВЩИКА</th>
                        <th style={miniThStyle}>ДАТА</th>
                        <th style={miniThStyle}>СУММА ОПЛАТЫ</th>
                        <th style={miniThStyle}>№ УПД</th>
                      </tr>
                    </thead>
                    <tbody>
                      {costs.materials.length > 0 ? costs.materials.slice(0, 10).map((cost) => (
                        <React.Fragment key={cost.id}>
                          <tr
                            onClick={() => toggleRow(cost.id)}
                            style={{ cursor: 'pointer', backgroundColor: expandedRows.has(cost.id) ? '#e8f5e9' : 'transparent' }}
                          >
                            <td style={miniTdStyle}>
                              <span style={{ marginRight: '6px' }}>{expandedRows.has(cost.id) ? '▼' : '▶'}</span>
                              {cost.description || '—'}
                            </td>
                            <td style={miniTdStyle}>{cost.date ? new Date(cost.date).toLocaleDateString('ru') : '—'}</td>
                            <td style={miniTdStyle}>{cost.amount.toLocaleString('ru')} ₽</td>
                            <td style={miniTdStyle}>{cost.document_number || '—'}</td>
                          </tr>
                          {expandedRows.has(cost.id) && cost.items && cost.items.length > 0 && (
                            <tr>
                              <td colSpan={4} style={{ padding: '0 0 0 20px', backgroundColor: '#f5f5f5' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                                  <thead>
                                    <tr style={{ backgroundColor: '#e0e0e0' }}>
                                      <th style={{ padding: '4px 8px', textAlign: 'left' }}>Наименование</th>
                                      <th style={{ padding: '4px 8px', textAlign: 'right', width: '80px' }}>Кол-во</th>
                                      <th style={{ padding: '4px 8px', textAlign: 'left', width: '50px' }}>Ед.</th>
                                      <th style={{ padding: '4px 8px', textAlign: 'right', width: '100px' }}>Цена</th>
                                      <th style={{ padding: '4px 8px', textAlign: 'right', width: '100px' }}>Сумма</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {cost.items.map((item) => (
                                      <tr key={item.id} style={{ borderBottom: '1px solid #ddd' }}>
                                        <td style={{ padding: '4px 8px' }}>{item.name}</td>
                                        <td style={{ padding: '4px 8px', textAlign: 'right' }}>{item.quantity}</td>
                                        <td style={{ padding: '4px 8px' }}>{item.unit}</td>
                                        <td style={{ padding: '4px 8px', textAlign: 'right' }}>{item.price.toLocaleString('ru')} ₽</td>
                                        <td style={{ padding: '4px 8px', textAlign: 'right' }}>{item.amount.toLocaleString('ru')} ₽</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      )) : (
                        <tr><td colSpan={4} style={{ ...miniTdStyle, textAlign: 'center', color: '#999' }}>Нет данных</td></tr>
                      )}
                    </tbody>
                    <tfoot>
                      <tr style={{ backgroundColor: '#f0f0f0' }}>
                        <td colSpan={3} style={{ ...miniTdStyle, fontWeight: 'bold' }}>сумма</td>
                        <td style={{ ...miniTdStyle, fontWeight: 'bold' }}>{costs.summary.materials_total.toLocaleString('ru')} ₽</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
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

// Mini-tables styles (Google Sheets style)
const summaryRowStyle: React.CSSProperties = {
  display: 'flex',
  gap: '20px',
  marginBottom: '20px',
  padding: '15px',
  backgroundColor: '#f8f9fa',
  borderRadius: '8px',
};

const summaryBoxStyle: React.CSSProperties = {
  flex: 1,
  padding: '10px 15px',
  backgroundColor: 'white',
  borderRadius: '6px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
};

const miniTablesGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(2, 1fr)',
  gap: '20px',
};

const miniTableContainerStyle: React.CSSProperties = {
  border: '1px solid #ddd',
  borderRadius: '4px',
  overflow: 'hidden',
};

const miniTableHeaderStyle: React.CSSProperties = {
  backgroundColor: '#fff2cc',
  padding: '8px 12px',
  fontWeight: 'bold',
  fontSize: '12px',
  textAlign: 'center',
  borderBottom: '1px solid #ddd',
};

const miniTableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: '12px',
};

const miniThStyle: React.CSSProperties = {
  backgroundColor: '#f0f0f0',
  padding: '6px 8px',
  textAlign: 'left',
  borderBottom: '1px solid #ddd',
  fontWeight: '600',
  fontSize: '10px',
  color: '#333',
};

const miniTdStyle: React.CSSProperties = {
  padding: '6px 8px',
  borderBottom: '1px solid #eee',
  fontSize: '11px',
};
