import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiClient } from '../api/client';

interface ObjectData {
  name: string;
  deliveries: number;
}

export function TopObjectsChart() {
  const [data, setData] = useState<ObjectData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get<ObjectData[]>('/analytics/top-objects-by-deliveries');
        setData(response);
      } catch (err: any) {
        console.error('Ошибка загрузки данных:', err);
        setError(err.message || 'Не удалось загрузить данные');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
        Загрузка данных...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '40px',
        color: '#e74c3c',
        backgroundColor: '#fee',
        borderRadius: '8px',
        border: '1px solid #fcc'
      }}>
        ⚠️ {error}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: '#95a5a6' }}>
        Нет данных для отображения
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: 400 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            angle={-15}
            textAnchor="end"
            height={80}
            style={{ fontSize: '12px' }}
          />
          <YAxis
            label={{ value: 'Сумма доставок (₽)', angle: -90, position: 'insideLeft' }}
            style={{ fontSize: '12px' }}
          />
          <Tooltip
            formatter={(value: any) => [`${value.toLocaleString('ru')} ₽`, 'Доставки']}
            labelStyle={{ color: '#2c3e50' }}
          />
          <Legend />
          <Bar
            dataKey="deliveries"
            fill="#3498db"
            name="Доставки материалов"
            radius={[8, 8, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
