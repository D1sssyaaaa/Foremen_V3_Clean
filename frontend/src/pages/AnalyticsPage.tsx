import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface CostAnalytics {
  object_id: number;
  object_name: string;
  total_costs: number;
  labor_costs: number;
  material_costs: number;
  equipment_costs: number;
  period_start: string;
  period_end: string;
}

interface CostByType {
  type: string;
  amount: number;
  percentage: number;
}

export function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<CostAnalytics[]>([]);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  // Фильтр по объекту - будет использован в будущем (setter с _ чтобы избежать warning)
  const [selectedObject, _setSelectedObject] = useState<number | null>(null);

  useEffect(() => {
    // Установка дат по умолчанию (текущий месяц)
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    setStartDate(firstDay.toISOString().split('T')[0]);
    setEndDate(lastDay.toISOString().split('T')[0]);
  }, []);

  useEffect(() => {
    if (startDate && endDate) {
      loadAnalytics();
    }
  }, [startDate, endDate, selectedObject]);

  const loadAnalytics = async () => {
    try {
      const params = new URLSearchParams({
        period_start: startDate,
        period_end: endDate,
      });
      if (selectedObject) {
        params.append('object_id', selectedObject.toString());
      }
      
      const data = await apiClient.get<CostAnalytics[]>(`/analytics/costs?${params}`);
      setAnalytics(data);
    } catch (err) {
      console.error('Ошибка загрузки аналитики:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const params = new URLSearchParams({
        period_start: startDate,
        period_end: endDate,
      });
      if (selectedObject) {
        params.append('object_id', selectedObject.toString());
      }

      // Скачивание Excel файла
      const response = await fetch(`http://192.168.0.235:8000/api/v1/analytics/export?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (!response.ok) throw new Error('Ошибка экспорта');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics_${startDate}_${endDate}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert('Ошибка экспорта: ' + (err.message || 'Неизвестная ошибка'));
    }
  };

  const getTotalCosts = () => {
    return analytics.reduce((sum, item) => sum + item.total_costs, 0);
  };

  const getTotalByType = (): CostByType[] => {
    const total = getTotalCosts();
    const laborTotal = analytics.reduce((sum, item) => sum + item.labor_costs, 0);
    const materialTotal = analytics.reduce((sum, item) => sum + item.material_costs, 0);
    const equipmentTotal = analytics.reduce((sum, item) => sum + item.equipment_costs, 0);

    return [
      { type: 'ФОТ', amount: laborTotal, percentage: total > 0 ? (laborTotal / total) * 100 : 0 },
      { type: 'Материалы', amount: materialTotal, percentage: total > 0 ? (materialTotal / total) * 100 : 0 },
      { type: 'Техника', amount: equipmentTotal, percentage: total > 0 ? (equipmentTotal / total) * 100 : 0 },
    ];
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'ФОТ': return '#3498db';
      case 'Материалы': return '#2ecc71';
      case 'Техника': return '#f39c12';
      default: return '#95a5a6';
    }
  };

  if (loading && !startDate) {
    return <div>Загрузка...</div>;
  }

  const costsByType = getTotalByType();
  const totalCosts = getTotalCosts();

  return (
    <div>
      <h1 style={{ marginTop: 0, marginBottom: '20px' }}>Аналитика затрат</h1>

      {/* Фильтры */}
      <div style={{ 
        backgroundColor: 'white', 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'end', flexWrap: 'wrap' }}>
          <div style={{ flex: '1', minWidth: '200px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: '500' }}>
              Период с:
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
          </div>
          <div style={{ flex: '1', minWidth: '200px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: '500' }}>
              Период по:
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
          </div>
          <button
            onClick={loadAnalytics}
            style={{
              padding: '10px 24px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            Применить
          </button>
          <button
            onClick={handleExport}
            style={{
              padding: '10px 24px',
              backgroundColor: '#2ecc71',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            📊 Экспорт Excel
          </button>
        </div>
      </div>

      {/* Общая статистика */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '20px',
        marginBottom: '20px'
      }}>
        <div style={{
          backgroundColor: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          borderLeft: '4px solid #9b59b6'
        }}>
          <div style={{ fontSize: '14px', color: '#7f8c8d', marginBottom: '10px' }}>
            Всего затрат
          </div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#9b59b6' }}>
            {totalCosts.toLocaleString('ru')} ₽
          </div>
        </div>

        {costsByType.map(item => (
          <div
            key={item.type}
            style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              borderLeft: `4px solid ${getTypeColor(item.type)}`
            }}
          >
            <div style={{ fontSize: '14px', color: '#7f8c8d', marginBottom: '10px' }}>
              {item.type}
            </div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', color: getTypeColor(item.type) }}>
              {item.amount.toLocaleString('ru')} ₽
            </div>
            <div style={{ fontSize: '12px', color: '#95a5a6', marginTop: '5px' }}>
              {item.percentage.toFixed(1)}% от общей суммы
            </div>
          </div>
        ))}
      </div>

      {/* График распределения по типам */}
      <div style={{ 
        backgroundColor: 'white', 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '20px' }}>Распределение затрат</h3>
        <div style={{ display: 'flex', gap: '5px', height: '40px', borderRadius: '8px', overflow: 'hidden' }}>
          {costsByType.map(item => (
            item.percentage > 0 && (
              <div
                key={item.type}
                style={{
                  flex: item.percentage,
                  backgroundColor: getTypeColor(item.type),
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '12px',
                  fontWeight: '600'
                }}
                title={`${item.type}: ${item.amount.toLocaleString('ru')} ₽ (${item.percentage.toFixed(1)}%)`}
              >
                {item.percentage > 10 ? `${item.percentage.toFixed(0)}%` : ''}
              </div>
            )
          ))}
        </div>
        <div style={{ display: 'flex', gap: '20px', marginTop: '15px', flexWrap: 'wrap' }}>
          {costsByType.map(item => (
            <div key={item.type} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '16px',
                height: '16px',
                borderRadius: '3px',
                backgroundColor: getTypeColor(item.type)
              }} />
              <span style={{ fontSize: '14px', color: '#7f8c8d' }}>
                {item.type}: <strong>{item.amount.toLocaleString('ru')} ₽</strong>
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Таблица по объектам */}
      <div style={{ 
        backgroundColor: 'white', 
        borderRadius: '8px',
        overflow: 'hidden',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #ecf0f1' }}>
          <h3 style={{ margin: 0 }}>Детализация по объектам</h3>
        </div>
        
        {analytics.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#7f8c8d' }}>
            Нет данных за выбранный период
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Объект</th>
                <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>ФОТ</th>
                <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>Материалы</th>
                <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>Техника</th>
                <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>Всего</th>
                <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>% от общих</th>
              </tr>
            </thead>
            <tbody>
              {analytics.map(item => (
                <tr key={item.object_id} style={{ borderBottom: '1px solid #ecf0f1' }}>
                  <td style={{ padding: '12px', fontWeight: '500' }}>{item.object_name}</td>
                  <td style={{ padding: '12px', textAlign: 'right', color: '#3498db' }}>
                    {item.labor_costs.toLocaleString('ru')} ₽
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', color: '#2ecc71' }}>
                    {item.material_costs.toLocaleString('ru')} ₽
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', color: '#f39c12' }}>
                    {item.equipment_costs.toLocaleString('ru')} ₽
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', fontWeight: '600', fontSize: '15px' }}>
                    {item.total_costs.toLocaleString('ru')} ₽
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', color: '#7f8c8d' }}>
                    {totalCosts > 0 ? ((item.total_costs / totalCosts) * 100).toFixed(1) : 0}%
                  </td>
                </tr>
              ))}
              <tr style={{ backgroundColor: '#f8f9fa', fontWeight: '600' }}>
                <td style={{ padding: '12px' }}>ИТОГО</td>
                <td style={{ padding: '12px', textAlign: 'right', color: '#3498db' }}>
                  {costsByType.find(c => c.type === 'ФОТ')?.amount.toLocaleString('ru')} ₽
                </td>
                <td style={{ padding: '12px', textAlign: 'right', color: '#2ecc71' }}>
                  {costsByType.find(c => c.type === 'Материалы')?.amount.toLocaleString('ru')} ₽
                </td>
                <td style={{ padding: '12px', textAlign: 'right', color: '#f39c12' }}>
                  {costsByType.find(c => c.type === 'Техника')?.amount.toLocaleString('ru')} ₽
                </td>
                <td style={{ padding: '12px', textAlign: 'right', fontSize: '16px' }}>
                  {totalCosts.toLocaleString('ru')} ₽
                </td>
                <td style={{ padding: '12px', textAlign: 'right' }}>100%</td>
              </tr>
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
