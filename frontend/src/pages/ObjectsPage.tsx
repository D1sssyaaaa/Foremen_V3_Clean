import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { CostObject } from '../types';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Search,
  Building2,
  FileText,
  TrendingUp,
  AlertTriangle,
  X,
  Upload,
  Briefcase
} from 'lucide-react';

export function ObjectsPage() {
  const navigate = useNavigate();
  const [objects, setObjects] = useState<CostObject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Form State
  const [file, setFile] = useState<File | null>(null);
  const [newObject, setNewObject] = useState({
    name: '',
    customer_name: '',
    contract_number: '',
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

    if (!file) {
      alert("Необходимо загрузить файл сметы!");
      return;
    }

    try {
      await apiClient.uploadFile('/objects/', file, {
        ...newObject,
        labor_amount: newObject.labor_amount && !isNaN(parseFloat(newObject.labor_amount)) ? parseFloat(newObject.labor_amount) : undefined
      });

      setShowCreateModal(false);
      setNewObject({ name: '', customer_name: '', contract_number: '', labor_amount: '' });
      setFile(null);
      await loadObjects();
    } catch (err: any) {
      console.error("Error creating object:", err);
      alert('Ошибка при создании объекта. Проверьте консоль для деталей.');
    }
  };

  const formatMoney = (amount?: number | null) => {
    if (amount === undefined || amount === null) return '-';
    return amount.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'ACTIVE': return 'bg-green-100 text-green-700 border-green-200';
      case 'CLOSED': return 'bg-gray-100 text-gray-600 border-gray-200';
      case 'ARCHIVE': return 'bg-gray-100 text-gray-500 border-gray-200';
      case 'PREPARATION_TO_CLOSE': return 'bg-orange-100 text-orange-700 border-orange-200';
      default: return 'bg-blue-100 text-blue-700 border-blue-200';
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

  const filteredObjects = objects.filter(obj =>
    obj.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    obj.contract_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    obj.customer_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Объекты</h1>
          <p className="text-[var(--text-secondary)]">Управление строительными объектами</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-[var(--blue-ios)] text-white px-5 py-2.5 rounded-xl font-medium active:scale-95 transition-transform shadow-sm hover:shadow-md"
        >
          <Plus size={20} />
          <span>Добавить объект</span>
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
        <input
          type="text"
          placeholder="Поиск по названию, договору или заказчику..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-11 pr-4 py-3 bg-[var(--bg-card)] border border-[var(--separator)] rounded-xl text-[var(--text-primary)] focus:ring-2 focus:ring-[var(--blue-ios)] focus:border-transparent outline-none transition-all"
        />
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--blue-ios)]"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <AnimatePresence>
            {filteredObjects.map(obj => {
              const stats = obj.stats || {
                plan: { materials: 0, labor: 0, total: 0 },
                fact: { materials: 0, labor: 0, total: 0 },
                balance: { materials: 0, labor: 0, total: 0 },
                margin_pct: { materials: 0, labor: 0 }
              };
              const margin = stats.balance.total ?? 0;
              const isProfit = margin >= 0;

              return (
                <motion.div
                  key={obj.id}
                  layout
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  onClick={() => navigate(`/objects/${obj.id}`)}
                  className="bg-[var(--bg-card)] rounded-2xl p-6 shadow-sm border border-[var(--separator)] cursor-pointer hover:shadow-md transition-shadow group relative overflow-hidden"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
                      <Building2 size={24} />
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(obj.status)}`}>
                      {getStatusText(obj.status)}
                    </span>
                  </div>

                  <h3 className="text-xl font-bold text-[var(--text-primary)] mb-1 group-hover:text-[var(--blue-ios)] transition-colors line-clamp-1">
                    {obj.name}
                  </h3>
                  <div className="flex items-center gap-2 text-[var(--text-secondary)] text-sm mb-6">
                    <FileText size={14} />
                    <span>{obj.contract_number || 'Нет договора'}</span>
                    <span>•</span>
                    <span>{obj.customer_name || 'Заказчик не указан'}</span>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between items-center py-2 border-b border-[var(--separator-opaque)]">
                      <span className="text-[var(--text-secondary)] text-sm">Бюджет (План)</span>
                      <span className="font-semibold text-[var(--text-primary)]">
                        {formatMoney(stats.plan.total)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-[var(--separator-opaque)]">
                      <span className="text-[var(--text-secondary)] text-sm">Затраты (Факт)</span>
                      <span className="font-semibold text-red-600">
                        {formatMoney(stats.fact.total)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center pt-2">
                      <span className="text-[var(--text-secondary)] text-sm flex items-center gap-1">
                        Прибыль
                        {isProfit ? <TrendingUp size={14} className="text-green-500" /> : <AlertTriangle size={14} className="text-red-500" />}
                      </span>
                      <span className={`font-bold ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
                        {formatMoney(margin)}
                      </span>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      {!loading && filteredObjects.length === 0 && (
        <div className="text-center py-20 text-[var(--text-secondary)]">
          <div className="bg-gray-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Search size={32} className="text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-[var(--text-primary)]">Объекты не найдены</h3>
          <p>Попробуйте изменить параметры поиска или создайте новый объект</p>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="bg-[var(--bg-card)] rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden flex flex-col max-h-[90vh]"
          >
            <div className="flex justify-between items-center p-6 border-b border-[var(--separator)]">
              <h2 className="text-xl font-bold text-[var(--text-primary)]">Новый объект</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-[var(--bg-ios)] rounded-full text-[var(--text-secondary)] transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleCreateObject} className="p-6 overflow-y-auto space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Название объекта *</label>
                <input
                  required
                  type="text"
                  value={newObject.name}
                  onChange={(e) => setNewObject({ ...newObject, name: e.target.value })}
                  className="w-full p-3 bg-[var(--bg-ios)] rounded-xl border-none focus:ring-2 focus:ring-[var(--blue-ios)] outline-none transition-all"
                  placeholder="Жилой комплекс..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Заказчик</label>
                  <input
                    type="text"
                    value={newObject.customer_name}
                    onChange={(e) => setNewObject({ ...newObject, customer_name: e.target.value })}
                    className="w-full p-3 bg-[var(--bg-ios)] rounded-xl border-none focus:ring-2 focus:ring-[var(--blue-ios)] outline-none"
                    placeholder="ООО Строй..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Договор №</label>
                  <input
                    type="text"
                    value={newObject.contract_number}
                    onChange={(e) => setNewObject({ ...newObject, contract_number: e.target.value })}
                    className="w-full p-3 bg-[var(--bg-ios)] rounded-xl border-none focus:ring-2 focus:ring-[var(--blue-ios)] outline-none"
                    placeholder="123/23-К"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">ФОТ (План)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newObject.labor_amount}
                  onChange={(e) => setNewObject({ ...newObject, labor_amount: e.target.value })}
                  className="w-full p-3 bg-[var(--bg-ios)] rounded-xl border-none focus:ring-2 focus:ring-[var(--blue-ios)] outline-none"
                  placeholder="0.00"
                />
              </div>

              <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                <label className="block text-sm font-bold text-blue-800 mb-2 flex items-center gap-2">
                  <Upload size={16} />
                  Смета (Excel) *
                </label>
                <p className="text-xs text-blue-600 mb-3">
                  Бюджет на материалы и этапы работ будут созданы автоматически из файла сметы.
                </p>
                <input
                  required
                  type="file"
                  accept=".xlsx, .xls"
                  onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                  className="block w-full text-sm text-blue-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-full file:border-0
                      file:text-sm file:font-semibold
                      file:bg-blue-100 file:text-blue-700
                      hover:file:bg-blue-200 transaction-colors
                    "
                />
              </div>

              <div className="pt-4 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 py-3 bg-[var(--bg-ios)] text-[var(--text-primary)] rounded-xl font-medium hover:bg-gray-200 transition-colors"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={!file}
                  className="flex-1 py-3 bg-[var(--blue-ios)] text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 transition-all shadow-md hover:shadow-lg"
                >
                  Создать
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
