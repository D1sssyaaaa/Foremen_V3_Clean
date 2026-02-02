import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';

interface ObjectStats {
  object_id: number;
  object_name: string;
  object_code: string;
  object_status: string;
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

interface MaterialItemDetail {
  id: number;
  product_name: string;
  quantity: number;
  unit: string;
  price: number;
  amount: number;
  document_date: string | null;
  document_number: string;
  supplier_name: string;
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

interface EditableObject {
  id: number;
  name: string;
  customer_name: string;
  contract_number: string;
  description: string;
  contract_amount: number;
  material_amount: number;
  labor_amount: number;
  status: string;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'ACTIVE': return '#27ae60';
    case 'PREPARATION_TO_CLOSE': return '#f39c12';
    case 'CLOSED': return '#7f8c8d';
    case 'ARCHIVE': return '#95a5a6';
    default: return '#bdc3c7';
  }
};

// Styles
const containerStyle: React.CSSProperties = {
  padding: '30px',
  maxWidth: '1200px',
  margin: '0 auto',
};

const cardStyle: React.CSSProperties = {
  backgroundColor: 'white',
  borderRadius: '12px',
  boxShadow: '0 4px 15px rgba(0,0,0,0.05)',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
  minHeight: '80vh'
};

const headerStyle: React.CSSProperties = {
  padding: '24px 30px',
  borderBottom: '1px solid #ecf0f1',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  backgroundColor: '#fff',
};

const backButtonStyle: React.CSSProperties = {
  padding: '8px 16px',
  backgroundColor: '#f8f9fa',
  border: '1px solid #dee2e6',
  borderRadius: '6px',
  cursor: 'pointer',
  fontSize: '14px',
  color: '#2c3e50',
  fontWeight: '500',
  transition: 'background-color 0.2s',
};

const secondaryButtonStyle: React.CSSProperties = {
  padding: '8px 16px',
  backgroundColor: '#fff',
  border: '1px solid #3498db',
  borderRadius: '6px',
  cursor: 'pointer',
  fontSize: '14px',
  color: '#3498db',
  fontWeight: '500',
  display: 'flex',
  alignItems: 'center',
  gap: '5px'
};

const bodyStyle: React.CSSProperties = {
  padding: '30px',
  flex: 1,
};

const sectionStyle: React.CSSProperties = {
  marginBottom: '24px',
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

const modalOverlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0,0,0,0.5)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000
};

const modalContentStyle: React.CSSProperties = {
  backgroundColor: 'white',
  padding: '30px',
  borderRadius: '8px',
  width: '90%',
  maxWidth: '500px',
  maxHeight: '90vh',
  overflowY: 'auto'
};

const formGroupStyle: React.CSSProperties = {
  marginBottom: '15px'
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  marginBottom: '5px',
  fontWeight: '500'
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px',
  borderRadius: '4px',
  border: '1px solid #ddd',
  fontSize: '14px'
};

const tabContainerStyle: React.CSSProperties = {
  display: 'flex',
  borderBottom: '1px solid #ecf0f1',
  backgroundColor: '#fff',
  padding: '0 30px'
};

const tabStyle = (isActive: boolean): React.CSSProperties => ({
  padding: '15px 20px',
  cursor: 'pointer',
  borderBottom: isActive ? '3px solid #3498db' : '3px solid transparent',
  color: isActive ? '#2c3e50' : '#7f8c8d',
  fontWeight: isActive ? 600 : 500,
  transition: 'all 0.2s',
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  marginBottom: '-1px'
});

export function ObjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const objectId = id ? parseInt(id, 10) : 0;

  const [stats, setStats] = useState<ObjectStats | null>(null);
  const [costs, setCosts] = useState<ObjectCosts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string | number>>(new Set());

  // Edit Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editFormData, setEditFormData] = useState<Partial<EditableObject>>({});
  const [loadingEdit, setLoadingEdit] = useState(false);

  // Tabs State
  const [activeTab, setActiveTab] = useState<'summary' | 'materials'>('summary');
  const [materialItems, setMaterialItems] = useState<MaterialItemDetail[]>([]);
  const [loadingMaterials, setLoadingMaterials] = useState(false);

  const loadMaterialItems = async () => {
    if (materialItems.length > 0) return; // Cache for this session
    setLoadingMaterials(true);
    try {
      const data = await apiClient.get<MaterialItemDetail[]>(`/objects/${objectId}/material-items`);
      setMaterialItems(data);
    } catch (err) {
      console.error('Failed to load material items:', err);
    } finally {
      setLoadingMaterials(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'materials') {
      loadMaterialItems();
    }
  }, [activeTab]);

  const toggleRow = (id: string | number) => {
    setExpandedRows(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  useEffect(() => {
    if (objectId) {
      loadStats();
      loadCosts();
    }
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
    } catch (err: any) {
      console.error('Ошибка загрузки затрат:', err);
    }
  };

  const handleOpenEdit = async () => {
    setLoadingEdit(true);
    setShowEditModal(true);
    try {
      const data = await apiClient.get<EditableObject>(`/objects/${objectId}`);
      setEditFormData({
        name: data.name,
        customer_name: data.customer_name || '',
        contract_number: data.contract_number || '',
        description: data.description || '',
        material_amount: data.material_amount || 0,
        labor_amount: data.labor_amount || 0,
        // contract_amount: data.contract_amount || 0, // We calculate this
        status: data.status || 'ACTIVE'
      });
    } catch (err) {
      alert('Не удалось загрузить данные для редактирования');
      setShowEditModal(false);
    } finally {
      setLoadingEdit(false);
    }
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const material = editFormData.material_amount || 0;
      const labor = editFormData.labor_amount || 0;
      const total = material + labor;

      const dataToSend = {
        ...editFormData,
        contract_amount: total // Force total to be sum of parts
      };

      await apiClient.put(`/objects/${objectId}`, dataToSend);
      alert('Объект обновлен');
      setShowEditModal(false);
      loadStats();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  // Status Change Handler
  const handleStatusChange = async (newStatus: string) => {
    try {
      // Optimistic update mechanism could be added here, but for now just wait
      await apiClient.patch(`/objects/${objectId}/status`, { status: newStatus });
      loadStats(); // Reload to confirm and update UI
    } catch (err: any) {
      alert(`Ошибка изменения статуса: ${err.response?.data?.detail || err.message}`);
    }
  }

  const handleBack = () => {
    navigate('/objects');
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>Загрузка...</div>
    );
  }

  if (error) {
    return (
      <div style={containerStyle}>
        <div style={cardStyle}>
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ color: '#e74c3c', marginBottom: '15px' }}>{error}</div>
            <button onClick={handleBack} style={primaryButtonStyle}>
              Вернуться к списку
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        {/* Header */}
        <div style={headerStyle}>
          <div>
            <h2 style={{ margin: 0, marginBottom: '5px' }}>{stats.object_name}</h2>
            <div style={{ color: '#7f8c8d', fontSize: '14px' }}>Код: {stats.object_code}</div>
          </div>

          <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
            {/* Status Selector */}
            <div style={{ position: 'relative' }}>
              <select
                value={stats.object_status}
                onChange={(e) => handleStatusChange(e.target.value)}
                style={{
                  padding: '8px 30px 8px 15px',
                  backgroundColor: getStatusColor(stats.object_status),
                  color: 'white',
                  border: 'none',
                  borderRadius: '20px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  appearance: 'none',
                  outline: 'none',
                  boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
                }}
              >
                <option value="ACTIVE">В работе</option>
                <option value="PREPARATION_TO_CLOSE">Гот. к закрытию</option>
                <option value="CLOSED">Закрыт</option>
                <option value="ARCHIVE">Архив</option>
              </select>
              {/* Arrow Icon */}
              <div style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                pointerEvents: 'none',
                color: 'white',
                fontSize: '10px'
              }}>▼</div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={handleOpenEdit} style={secondaryButtonStyle}>
                ✏️ Редактировать
              </button>
              <button onClick={handleBack} style={backButtonStyle}>
                ← Назад к списку
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div style={tabContainerStyle}>
          <div style={tabStyle(activeTab === 'summary')} onClick={() => setActiveTab('summary')}>
            📊 Сводка
          </div>
          <div style={tabStyle(activeTab === 'materials')} onClick={() => setActiveTab('materials')}>
            📦 Материалы
          </div>
        </div>

        {/* Body */}
        <div style={bodyStyle}>
          {activeTab === 'materials' ? (
            <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ margin: 0 }}>Отгруженные материалы</h3>
                <div style={{ color: '#7f8c8d', fontSize: '13px' }}>Всего позиций: {materialItems.length}</div>
              </div>

              {loadingMaterials ? (
                <div style={{ padding: '40px', textAlign: 'center', color: '#7f8c8d' }}>Загрузка данных...</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #ecf0f1', color: '#7f8c8d' }}>
                      <th style={{ padding: '12px 10px', textAlign: 'left' }}>Дата</th>
                      <th style={{ padding: '12px 10px', textAlign: 'left' }}>№ УПД</th>
                      <th style={{ padding: '12px 10px', textAlign: 'left' }}>Поставщик</th>
                      <th style={{ padding: '12px 10px', textAlign: 'left' }}>Наименование</th>
                      <th style={{ padding: '12px 10px', textAlign: 'center' }}>Ед.</th>
                      <th style={{ padding: '12px 10px', textAlign: 'right' }}>Кол-во</th>
                      <th style={{ padding: '12px 10px', textAlign: 'right' }}>Цена</th>
                      <th style={{ padding: '12px 10px', textAlign: 'right' }}>Сумма</th>
                    </tr>
                  </thead>
                  <tbody>
                    {materialItems.length > 0 ? materialItems.map((item) => (
                      <tr key={item.id} style={{ borderBottom: '1px solid #ecf0f1', transition: 'background-color 0.1s' }}>
                        <td style={{ padding: '10px' }}>{item.document_date ? new Date(item.document_date).toLocaleDateString('ru') : '-'}</td>
                        <td style={{ padding: '10px' }}>{item.document_number}</td>
                        <td style={{ padding: '10px' }}>{item.supplier_name}</td>
                        <td style={{ padding: '10px', fontWeight: '500', maxWidth: '300px' }}>{item.product_name}</td>
                        <td style={{ padding: '10px', textAlign: 'center' }}>{item.unit}</td>
                        <td style={{ padding: '10px', textAlign: 'right' }}>{item.quantity.toLocaleString('ru')}</td>
                        <td style={{ padding: '10px', textAlign: 'right', whiteSpace: 'nowrap' }}>{item.price.toLocaleString('ru')} ₽</td>
                        <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold', whiteSpace: 'nowrap' }}>{item.amount.toLocaleString('ru')} ₽</td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan={8} style={{ padding: '30px', textAlign: 'center', color: '#999' }}>Нет данных о закупках</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}
            </div>
          ) : (
            <>
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

              {/* Свод и мини-таблицы затрат */}
              {costs && (
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
            </>
          )}
        </div>
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <div style={modalOverlayStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px', marginTop: 0 }}>Редактирование объекта</h2>
            {loadingEdit ? <div>Загрузка данных...</div> : (
              <form onSubmit={handleSaveEdit}>
                <div style={formGroupStyle}>
                  <label style={labelStyle}>Название</label>
                  <input required type="text" style={inputStyle} value={editFormData.name} onChange={e => setEditFormData({ ...editFormData, name: e.target.value })} />
                </div>
                <div style={formGroupStyle}>
                  <label style={labelStyle}>Заказчик</label>
                  <input type="text" style={inputStyle} value={editFormData.customer_name} onChange={e => setEditFormData({ ...editFormData, customer_name: e.target.value })} />
                </div>
                <div style={formGroupStyle}>
                  <label style={labelStyle}>Договор</label>
                  <input type="text" style={inputStyle} value={editFormData.contract_number} onChange={e => setEditFormData({ ...editFormData, contract_number: e.target.value })} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                  <div style={formGroupStyle}>
                    <label style={labelStyle}>План материалы (₽)</label>
                    <input type="number" step="0.01" style={inputStyle} value={editFormData.material_amount} onChange={e => setEditFormData({ ...editFormData, material_amount: parseFloat(e.target.value) })} />
                  </div>
                  <div style={formGroupStyle}>
                    <label style={labelStyle}>План работы (₽)</label>
                    <input type="number" step="0.01" style={inputStyle} value={editFormData.labor_amount} onChange={e => setEditFormData({ ...editFormData, labor_amount: parseFloat(e.target.value) })} />
                  </div>
                </div>

                {/* Removed Contract Amount Input */}
                {/* Removed Status Select */}

                <div style={formGroupStyle}>
                  <label style={labelStyle}>Описание</label>
                  <textarea style={{ ...inputStyle, height: '80px', resize: 'vertical' }} value={editFormData.description} onChange={e => setEditFormData({ ...editFormData, description: e.target.value })} />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px', paddingTop: '15px', borderTop: '1px solid #eee' }}>
                  <button type="button" onClick={() => setShowEditModal(false)} style={backButtonStyle}>Отмена</button>
                  <button type="submit" style={primaryButtonStyle}>Сохранить</button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


