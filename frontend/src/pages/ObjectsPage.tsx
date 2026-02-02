import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { CostObject } from '../types';

export function ObjectsPage() {
  const navigate = useNavigate();
  const [objects, setObjects] = useState<CostObject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newObject, setNewObject] = useState({
    name: '',
    customer_name: '',
    contract_number: '',
    material_amount: '',
    labor_amount: ''
  });

  useEffect(() => {
    loadObjects();
  }, []);

  const loadObjects = async () => {
    try {
      const data = await apiClient.get<CostObject[]>('/objects/');
      setObjects(data);
    } catch (err) {
      console.error('Ошибка загрузки объектов:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateObject = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/objects/', {
        ...newObject,
        material_amount: newObject.material_amount ? parseFloat(newObject.material_amount) : undefined,
        labor_amount: newObject.labor_amount ? parseFloat(newObject.labor_amount) : undefined
      });
      setShowCreateModal(false);
      setNewObject({ name: '', customer_name: '', contract_number: '', material_amount: '', labor_amount: '' });
      await loadObjects();
      alert('Объект успешно создан!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка создания объекта');
    }
  };

  const formatMoney = (amount?: number | null) => {
    if (amount === undefined || amount === null) return '-';
    return amount.toLocaleString('ru-RU', { style: 'decimal', minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const formatPercent = (percent?: number | null) => {
    if (percent === undefined || percent === null) return '-';
    // If percent is 0 and diff is 0, show 0. If data missing, show -
    if (isNaN(percent)) return '-';
    return `${percent.toFixed(1)}%`;
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'ACTIVE': return '#27ae60'; // Green
      case 'CLOSED': return '#95a5a6'; // Gray
      case 'ARCHIVE': return '#7f8c8d'; // Dark Gray
      case 'PREPARATION_TO_CLOSE': return '#f39c12'; // Orange
      default: return '#2c3e50';
    }
  };

  const getStatusText = (status?: string) => {
    switch (status) {
      case 'ACTIVE': return 'В работе';
      case 'CLOSED': return 'Закрыт';
      case 'ARCHIVE': return 'Архив';
      case 'PREPARATION_TO_CLOSE': return 'На закрытии';
      default: return status || 'Новый';
    }
  };

  const getColorForValue = (val?: number) => {
    if (!val) return 'inherit';
    return val >= 0 ? 'green' : 'red';
  };

  if (loading) {
    return <div>Загрузка...</div>;
  }

  // Styles
  const thStyle = {
    padding: '10px',
    borderRight: '1px solid #bdc3c7',
    borderBottom: '1px solid #bdc3c7',
    backgroundColor: '#ecf0f1',
    fontSize: '12px',
    fontWeight: 'bold',
    textAlign: 'center' as const,
    verticalAlign: 'middle',
    minWidth: '80px'
  };

  const tdStyle = {
    padding: '8px 10px',
    borderRight: '1px solid #ecf0f1',
    borderBottom: '1px solid #ecf0f1',
    fontSize: '13px',
    verticalAlign: 'middle'
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>Сводная таблица объектов</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          style={{
            padding: '10px 20px',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Добавить объект
        </button>
      </div>

      <div style={{
        flex: 1,
        overflow: 'auto',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        border: '1px solid #bdc3c7'
      }}>
        <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, minWidth: '1500px' }}>
          <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
            <tr>
              <th rowSpan={2} style={{ ...thStyle, left: 0, zIndex: 11, borderRight: '2px solid #bdc3c7' }}>Статус</th>
              <th rowSpan={2} style={{ ...thStyle, left: '80px', zIndex: 11, minWidth: '200px' }}>Наименование объекта</th>
              <th rowSpan={2} style={thStyle}>Заказчик</th>
              <th rowSpan={2} style={thStyle}>Договор</th>

              <th colSpan={2} style={{ ...thStyle, backgroundColor: '#d1f2eb' }}>СТОИМОСТЬ ПО ДОГОВОРУ (ПЛАН)</th>
              <th colSpan={2} style={{ ...thStyle, backgroundColor: '#fadbd8' }}>ФАКТИЧЕСКИЕ ЗАТРАТЫ</th>
              <th colSpan={3} style={{ ...thStyle, backgroundColor: '#d6eaf8' }}>РАЗНИЦА (ПРИБЫЛЬ)</th>
              <th colSpan={2} style={{ ...thStyle, backgroundColor: '#fcf3cf' }}>РЕНТАБЕЛЬНОСТЬ %</th>
            </tr>
            <tr>
              {/* PLAN */}
              <th style={{ ...thStyle, backgroundColor: '#d1f2eb' }}>Работа</th>
              <th style={{ ...thStyle, backgroundColor: '#d1f2eb' }}>Материал</th>

              {/* FACT */}
              <th style={{ ...thStyle, backgroundColor: '#fadbd8' }}>Работа</th>
              <th style={{ ...thStyle, backgroundColor: '#fadbd8' }}>Материал</th>

              {/* DIFF */}
              <th style={{ ...thStyle, backgroundColor: '#d6eaf8' }}>Работа</th>
              <th style={{ ...thStyle, backgroundColor: '#d6eaf8' }}>Материал</th>
              <th style={{ ...thStyle, backgroundColor: '#d6eaf8', fontWeight: '800' }}>ИТОГО</th>

              {/* MARGIN */}
              <th style={{ ...thStyle, backgroundColor: '#fcf3cf' }}>Работа</th>
              <th style={{ ...thStyle, backgroundColor: '#fcf3cf' }}>Материал</th>
            </tr>
          </thead>
          <tbody>
            {objects.map(obj => {
              const stats = obj.stats || {
                plan: { materials: 0, labor: 0, total: 0 },
                fact: { materials: 0, labor: 0, total: 0 },
                balance: { materials: 0, labor: 0, total: 0 },
                margin_pct: { materials: 0, labor: 0 }
              };

              return (
                <tr
                  key={obj.id}
                  onClick={() => navigate(`/objects/${obj.id}`)}
                  style={{ cursor: 'pointer', transition: 'background-color 0.1s' }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f4f6f7'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
                >
                  {/* Status */}
                  <td style={{ ...tdStyle, textAlign: 'center' }}>
                    <span style={{
                      padding: '4px 8px',
                      borderRadius: '12px',
                      fontSize: '11px',
                      fontWeight: 'bold',
                      color: 'white',
                      backgroundColor: getStatusColor(obj.status),
                      whiteSpace: 'nowrap'
                    }}>
                      {getStatusText(obj.status)}
                    </span>
                  </td>
                  {/* Name */}
                  <td style={{ ...tdStyle, fontWeight: '500' }}>
                    {obj.name}
                    <div style={{ fontSize: '10px', color: '#7f8c8d' }}>{obj.code}</div>
                  </td>
                  {/* Customer */}
                  <td style={tdStyle}>{obj.customer_name || '-'}</td>
                  {/* Contract */}
                  <td style={tdStyle}>{obj.contract_number || '-'}</td>

                  {/* PLAN */}
                  <td style={{ ...tdStyle, textAlign: 'right' }}>{formatMoney(stats.plan.labor)}</td>
                  <td style={{ ...tdStyle, textAlign: 'right' }}>{formatMoney(stats.plan.materials)}</td>

                  {/* FACT */}
                  <td style={{ ...tdStyle, textAlign: 'right', color: '#c0392b' }}>{formatMoney(stats.fact.labor)}</td>
                  <td style={{ ...tdStyle, textAlign: 'right', color: '#c0392b' }}>{formatMoney(stats.fact.materials)}</td>

                  {/* DIFF */}
                  <td style={{ ...tdStyle, textAlign: 'right', fontWeight: 'bold', color: getColorForValue(stats.balance.labor) }}>
                    {formatMoney(stats.balance.labor)}
                  </td>
                  <td style={{ ...tdStyle, textAlign: 'right', fontWeight: 'bold', color: getColorForValue(stats.balance.materials) }}>
                    {formatMoney(stats.balance.materials)}
                  </td>
                  <td style={{ ...tdStyle, textAlign: 'right', fontWeight: '800', backgroundColor: '#ebf5fb', color: getColorForValue(stats.balance.total) }}>
                    {formatMoney(stats.balance.total)}
                  </td>

                  {/* MARGIN */}
                  <td style={{ ...tdStyle, textAlign: 'center', color: getColorForValue(stats.balance.labor) }}>
                    {formatPercent(stats.margin_pct.labor)}
                  </td>
                  <td style={{ ...tdStyle, textAlign: 'center', color: getColorForValue(stats.balance.materials) }}>
                    {formatPercent(stats.margin_pct.materials)}
                  </td>
                </tr>
              );
            })}
            {objects.length === 0 && (
              <tr>
                <td colSpan={13} style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
                  Нет данных
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showCreateModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '8px', width: '90%', maxWidth: '500px' }}>
            <h2>Новый объект</h2>
            <form onSubmit={handleCreateObject}>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Название *</label>
                <input required type="text" value={newObject.name} onChange={(e) => setNewObject({ ...newObject, name: e.target.value })} style={{ width: '100%', padding: '8px' }} />
              </div>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Заказчик</label>
                <input type="text" value={newObject.customer_name} onChange={(e) => setNewObject({ ...newObject, customer_name: e.target.value })} style={{ width: '100%', padding: '8px' }} />
              </div>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Договор №</label>
                <input type="text" value={newObject.contract_number} onChange={(e) => setNewObject({ ...newObject, contract_number: e.target.value })} style={{ width: '100%', padding: '8px' }} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px' }}>План Материалы</label>
                  <input type="number" step="0.01" value={newObject.material_amount} onChange={(e) => setNewObject({ ...newObject, material_amount: e.target.value })} style={{ width: '100%', padding: '8px' }} />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px' }}>План Работы</label>
                  <input type="number" step="0.01" value={newObject.labor_amount} onChange={(e) => setNewObject({ ...newObject, labor_amount: e.target.value })} style={{ width: '100%', padding: '8px' }} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px' }}>
                <button type="button" onClick={() => setShowCreateModal(false)}>Отмена</button>
                <button type="submit" style={{ backgroundColor: '#3498db', color: 'white', border: 'none', padding: '10px 20px' }}>Создать</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
