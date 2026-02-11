import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { motion } from 'framer-motion';
import {
  BarChart3,
  Calendar,
  Download,
  TrendingUp,
  Hammer,
  HardHat,
  Truck,
  Filter
} from 'lucide-react';

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
  color: string;
  icon: any;
  bg: string;
}

export function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<CostAnalytics[]>([]);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Set defaults
  useEffect(() => {
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

    // Adjust for timezone offset to avoid "yesterday" issues
    const formatDate = (date: Date) => {
      const d = new Date(date.getTime() - (date.getTimezoneOffset() * 60000));
      return d.toISOString().split('T')[0];
    };

    setStartDate(formatDate(firstDay));
    setEndDate(formatDate(lastDay));
  }, []);

  useEffect(() => {
    if (startDate && endDate) {
      loadAnalytics();
    }
  }, [startDate, endDate]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        period_start: startDate,
        period_end: endDate,
      });
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

      const response = await fetch(`/api/v1/analytics/export?${params}`, {
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

  const getTotalCosts = () => analytics.reduce((sum, item) => sum + item.total_costs, 0);

  const getCostDistributions = (): CostByType[] => {
    const total = getTotalCosts();
    const labor = analytics.reduce((sum, item) => sum + item.labor_costs, 0);
    const materials = analytics.reduce((sum, item) => sum + item.material_costs, 0);
    const equipment = analytics.reduce((sum, item) => sum + item.equipment_costs, 0);

    return [
      {
        type: 'Материалы',
        amount: materials,
        percentage: total > 0 ? (materials / total) * 100 : 0,
        color: 'text-green-600',
        bg: 'bg-green-100',
        icon: Hammer
      },
      {
        type: 'ФОТ',
        amount: labor,
        percentage: total > 0 ? (labor / total) * 100 : 0,
        color: 'text-blue-600',
        bg: 'bg-blue-100',
        icon: HardHat
      },
      {
        type: 'Техника',
        amount: equipment,
        percentage: total > 0 ? (equipment / total) * 100 : 0,
        color: 'text-orange-600',
        bg: 'bg-orange-100',
        icon: Truck
      },
    ].sort((a, b) => b.amount - a.amount);
  };

  const totalCosts = getTotalCosts();
  const distributions = getCostDistributions();

  return (
    <div className="space-y-6 animate-fade-in pb-20 max-w-7xl mx-auto">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2">
            <BarChart3 className="text-[var(--blue-ios)]" /> Аналитика затрат
          </h1>
          <p className="text-[var(--text-secondary)]">Финансовые показатели по проектам</p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto bg-[var(--bg-card)] p-2 rounded-xl border border-[var(--separator)] shadow-sm">
          <div className="flex items-center gap-2 px-2">
            <Calendar size={16} className="text-[var(--text-secondary)]" />
            <input
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
              className="bg-transparent border-none outline-none text-sm font-medium w-32"
            />
            <span className="text-[var(--text-secondary)]">-</span>
            <input
              type="date"
              value={endDate}
              onChange={e => setEndDate(e.target.value)}
              className="bg-transparent border-none outline-none text-sm font-medium w-32"
            />
          </div>

          <div className="w-[1px] h-6 bg-[var(--separator)] hidden md:block"></div>

          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-ios)] hover:bg-[var(--separator)] rounded-lg text-sm font-medium transition-colors ml-auto md:ml-0"
          >
            <Download size={16} /> Экспорт
          </button>
        </div>
      </div>

      {loading && !totalCosts ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-32 bg-[var(--bg-card)] rounded-2xl animate-pulse" />)}
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-5 text-white shadow-lg relative overflow-hidden"
            >
              <div className="relative z-10">
                <div className="text-indigo-100 text-sm font-medium mb-1 flex items-center gap-2">
                  <TrendingUp size={16} /> Всего затрат
                </div>
                <div className="text-3xl font-bold tracking-tight">
                  {totalCosts.toLocaleString('ru-RU')} ₽
                </div>
              </div>
              <div className="absolute right-0 bottom-0 opacity-10 transform translate-x-4 translate-y-4">
                <BarChart3 size={120} />
              </div>
            </motion.div>

            {/* Distribution Cards */}
            {distributions.map((item, idx) => (
              <motion.div
                key={item.type}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-[var(--bg-card)] rounded-2xl p-5 border border-[var(--separator)] shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className={`p-2 rounded-xl ${item.bg} ${item.color}`}>
                    <item.icon size={20} />
                  </div>
                  <span className={`text-xs font-bold px-2 py-1 rounded-full ${item.bg} ${item.color}`}>
                    {item.percentage.toFixed(1)}%
                  </span>
                </div>
                <div>
                  <div className="text-[var(--text-secondary)] text-sm font-medium">{item.type}</div>
                  <div className="text-xl font-bold text-[var(--text-primary)]">
                    {item.amount.toLocaleString('ru-RU')} ₽
                  </div>
                  <div className="w-full h-1.5 bg-[var(--bg-ios)] rounded-full mt-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${item.bg.replace('bg-', 'bg-opacity-100 bg-')}`}
                      style={{ width: `${item.percentage}%`, backgroundColor: 'currentColor' }}
                    />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Objects Table */}
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--separator)] shadow-sm overflow-hidden">
            <div className="p-4 border-b border-[var(--separator)] bg-[var(--bg-ios)] flex justify-between items-center">
              <h3 className="font-bold text-[var(--text-primary)]">Детализация по объектам</h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--separator)] bg-[var(--bg-card)]">
                    <th className="text-left p-4 font-medium text-[var(--text-secondary)]">Объект</th>
                    <th className="text-right p-4 font-medium text-[var(--text-secondary)]">Материалы</th>
                    <th className="text-right p-4 font-medium text-[var(--text-secondary)]">ФОТ</th>
                    <th className="text-right p-4 font-medium text-[var(--text-secondary)]">Техника</th>
                    <th className="text-right p-4 font-medium text-[var(--text-primary)]">Итого</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--separator)]">
                  {analytics.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-[var(--text-secondary)]">
                        Нет данных за выбранный период
                      </td>
                    </tr>
                  ) : (
                    analytics.map(item => (
                      <tr key={item.object_id} className="hover:bg-[var(--bg-ios)] transition-colors group">
                        <td className="p-4 font-medium text-[var(--text-primary)]">
                          {item.object_name}
                        </td>
                        <td className="p-4 text-right tabular-nums text-[var(--text-secondary)]">
                          {item.material_costs.toLocaleString('ru-RU')}
                        </td>
                        <td className="p-4 text-right tabular-nums text-[var(--text-secondary)]">
                          {item.labor_costs.toLocaleString('ru-RU')}
                        </td>
                        <td className="p-4 text-right tabular-nums text-[var(--text-secondary)]">
                          {item.equipment_costs.toLocaleString('ru-RU')}
                        </td>
                        <td className="p-4 text-right tabular-nums font-bold text-[var(--text-primary)] group-hover:text-[var(--blue-ios)]">
                          {item.total_costs.toLocaleString('ru-RU')}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
                {analytics.length > 0 && (
                  <tfoot>
                    <tr className="bg-[var(--bg-ios)] font-bold text-[var(--text-primary)]">
                      <td className="p-4">ИТОГО</td>
                      <td className="p-4 text-right tabular-nums text-green-700">
                        {distributions.find(d => d.type === 'Материалы')?.amount.toLocaleString('ru-RU')}
                      </td>
                      <td className="p-4 text-right tabular-nums text-blue-700">
                        {distributions.find(d => d.type === 'ФОТ')?.amount.toLocaleString('ru-RU')}
                      </td>
                      <td className="p-4 text-right tabular-nums text-orange-700">
                        {distributions.find(d => d.type === 'Техника')?.amount.toLocaleString('ru-RU')}
                      </td>
                      <td className="p-4 text-right tabular-nums text-lg">
                        {totalCosts.toLocaleString('ru-RU')}
                      </td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
