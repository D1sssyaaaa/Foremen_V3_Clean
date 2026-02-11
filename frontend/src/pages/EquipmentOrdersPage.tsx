
import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Truck,
  Calendar,
  MapPin,
  User,
  CheckCircle2,
  AlertCircle,
  Plus,
  X,
  CreditCard,
  DollarSign,
  Info
} from 'lucide-react';

interface EquipmentOrder {
  id: number;
  cost_object_id: number;
  cost_object_name?: string;
  foreman_id: number;
  foreman_name?: string;
  foreman_phone?: string;
  equipment_type: string;
  quantity: number;
  start_date: string;
  end_date: string;
  status: string;
  rejection_reason?: string;
  total_cost?: number;
  hour_rate?: number;
  hours_worked?: number;
  description?: string;
  comment?: string;
  created_at: string;
  updated_at?: string;
}

const ALL_STATUSES = [
  { value: 'all', label: 'Все' },
  { value: 'НОВАЯ', label: 'Новая' },
  { value: 'УТВЕРЖДЕНА', label: 'Утверждена' },
  { value: 'В РАБОТЕ', label: 'В работе' },
  { value: 'ЗАВЕРШЕНА', label: 'Завершена' },
  { value: 'ОТМЕНА ЗАПРОШЕНА', label: 'Запрос отмены' },
  { value: 'ОТМЕНЕНА', label: 'Отменена' },
];

const equipmentTypeLabels: Record<string, string> = {
  'excavator': 'Экскаватор',
  'crane': 'Кран',
  'loader': 'Погрузчик',
  'bulldozer': 'Бульдозер',
  'truck': 'Грузовик',
  'concrete_mixer': 'Бетоносмеситель',
  'dump_truck': 'Самосвал',
  'forklift': 'Вилочный погрузчик',
  'roller': 'Каток',
  'grader': 'Грейдер',
  'scaffolding': 'Строительные леса',
  'generator': 'Генератор',
  'compressor': 'Компрессор',
  'welding_machine': 'Сварочный аппарат',
  'jackhammer': 'Отбойный молоток',
  'drill': 'Дрель',
  'concrete_pump': 'Бетононасос',
  'tower_crane': 'Башенный кран',
  'mobile_crane': 'Автокран',
  'mini_excavator': 'Мини-экскаватор',
  'backhoe': 'Экскаватор-погрузчик',
  'other': 'Другое',
};

export function EquipmentOrdersPage() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<EquipmentOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [selectedOrder, setSelectedOrder] = useState<EquipmentOrder | null>(null);
  const [showCostModal, setShowCostModal] = useState(false);
  const [costOrder, setCostOrder] = useState<EquipmentOrder | null>(null);
  const [hourRate, setHourRate] = useState('');

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const data = await apiClient.get<EquipmentOrder[]>('/equipment-orders/');
      setOrders(data);
    } catch (err) {
      console.error('Ошибка загрузки заявок:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'НОВАЯ': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'УТВЕРЖДЕНА': return 'bg-green-100 text-green-700 border-green-200';
      case 'В РАБОТЕ': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'ЗАВЕРШЕНА': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'ОТМЕНЕНА': return 'bg-gray-100 text-gray-600 border-gray-200';
      case 'ОТМЕНА ЗАПРОШЕНА': return 'bg-red-100 text-red-700 border-red-200';
      case 'ОТКЛОНЕНА': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-gray-100 text-gray-500 border-gray-200';
    }
  };

  const getStatusText = (status: string) => status;

  const getEquipmentTypeText = (type: string) => {
    return equipmentTypeLabels[type.toLowerCase()] || equipmentTypeLabels[type] || type;
  };

  const handleApprove = async (id: number) => {
    try {
      await apiClient.post(`/equipment-orders/${id}/approve`, {});
      await loadOrders();
      alert('Заявка утверждена');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка утверждения');
    }
  };

  const handleSetCost = async () => {
    if (!costOrder || !hourRate) return;

    try {
      await apiClient.put(`/equipment-orders/${costOrder.id}/cost`, {
        hour_rate: parseFloat(hourRate)
      });
      await loadOrders();
      setShowCostModal(false);
      setCostOrder(null);
      setHourRate('');
      alert('Стоимость установлена');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка установки стоимости');
    }
  };

  const openCostModal = (order: EquipmentOrder) => {
    setCostOrder(order);
    setHourRate(order.hour_rate?.toString() || '');
    setShowCostModal(true);
  };

  const calculateDays = (start: string, end: string) => {
    const diff = new Date(end).getTime() - new Date(start).getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24)) + 1;
  };

  const canManageOrders = () => {
    if (!user) return false;
    return user.roles.some(role =>
      ['ADMIN', 'MANAGER', 'EQUIPMENT_MANAGER'].includes(role)
    );
  };

  const filteredOrders = orders.filter(order => {
    if (filter === 'all') return true;
    return order.status === filter;
  });

  const statusCounts = ALL_STATUSES.reduce((acc, status) => {
    if (status.value === 'all') {
      acc[status.value] = orders.length;
    } else {
      acc[status.value] = orders.filter(o => o.status === status.value).length;
    }
    return acc;
  }, {} as Record<string, number>);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="animate-spin text-[var(--blue-ios)]">
          <Truck size={40} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in pb-20">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Аренда техники</h1>
          <p className="text-[var(--text-secondary)]">Управление спецтехникой и инструменты</p>
        </div>
        <button
          onClick={() => alert('Используйте Telegram Bot для создания заявок на технику!')}
          className="flex items-center gap-2 bg-[var(--blue-ios)] text-white px-5 py-2.5 rounded-xl font-medium active:scale-95 transition-transform shadow-sm hover:shadow-md"
        >
          <Plus size={20} />
          <span>Создать заявку</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0 no-scrollbar">
        {ALL_STATUSES.map(status => (
          <button
            key={status.value}
            onClick={() => setFilter(status.value)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-xl whitespace-nowrap transition-colors font-medium text-sm
              ${filter === status.value
                ? 'bg-[var(--blue-ios)] text-white shadow-md'
                : 'bg-[var(--bg-card)] text-[var(--text-secondary)] border border-[var(--separator)] hover:bg-[var(--bg-ios)]'}
            `}
          >
            {status.label}
            <span className={`
              px-2 py-0.5 rounded-md text-xs font-bold
              ${filter === status.value ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'}
            `}>
              {statusCounts[status.value] || 0}
            </span>
          </button>
        ))}
      </div>

      {filteredOrders.length === 0 ? (
        <div className="bg-[var(--bg-card)] p-10 rounded-2xl border border-[var(--separator)] text-center text-[var(--text-secondary)]">
          <div className="bg-yellow-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Truck size={32} className="text-yellow-500" />
          </div>
          <h3 className="text-lg font-medium text-[var(--text-primary)]">Заявки не найдены</h3>
          <p>Нет заявок с выбранным статусом</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          <AnimatePresence>
            {filteredOrders.map(order => (
              <motion.div
                key={order.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-[var(--bg-card)] rounded-2xl p-5 shadow-sm border border-[var(--separator)] hover:shadow-md transition-shadow relative overflow-hidden"
              >
                <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${getStatusColor(order.status).split(' ')[0]}`} />

                <div className="flex flex-col md:flex-row justify-between gap-4">
                  <div className="flex-1 pl-3">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                      <h3 className="text-lg font-bold text-[var(--text-primary)]">Заявка #{order.id}</h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(order.status)}`}>
                        {getStatusText(order.status)}
                      </span>
                    </div>

                    <div className="text-sm text-[var(--text-secondary)] flex flex-wrap gap-x-4 gap-y-1 mb-4">
                      <div className="flex items-center gap-1.5">
                        <MapPin size={14} />
                        <span className="font-medium text-[var(--text-primary)]">{order.cost_object_name || `Объект ${order.cost_object_id}`}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <User size={14} />
                        <span>{order.foreman_name || `Бригадир ${order.foreman_id}`}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Calendar size={14} />
                        <span>{new Date(order.created_at).toLocaleDateString('ru')}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-[var(--bg-ios)] p-4 rounded-xl">
                      <div>
                        <div className="text-xs text-[var(--text-secondary)] mb-1">Техника</div>
                        <div className="font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
                          <Truck size={14} className="text-orange-500" />
                          {getEquipmentTypeText(order.equipment_type)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-[var(--text-secondary)] mb-1">Количество</div>
                        <div className="font-semibold text-[var(--text-primary)]">{order.quantity} ед.</div>
                      </div>
                      <div>
                        <div className="text-xs text-[var(--text-secondary)] mb-1">Период</div>
                        <div className="font-semibold text-[var(--text-primary)] text-xs sm:text-sm">
                          {new Date(order.start_date).toLocaleDateString('ru')} - {new Date(order.end_date).toLocaleDateString('ru')}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-[var(--text-secondary)] mb-1">Стоимость</div>
                        <div className={`font-bold ${order.total_cost ? 'text-green-600' : 'text-gray-400'}`}>
                          {order.total_cost ? `${order.total_cost.toLocaleString('ru')} ₽` : 'Не указана'}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex md:flex-col gap-2 justify-center pl-3 md:pl-0 border-t md:border-t-0 md:border-l border-[var(--separator-opaque)] pt-4 md:pt-0 md:w-40 shrink-0">
                    {canManageOrders() && order.status === 'НОВАЯ' && (
                      <button
                        onClick={() => handleApprove(order.id)}
                        className="flex items-center justify-center gap-2 w-full py-2 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 transition-colors text-sm"
                      >
                        <CheckCircle2 size={16} /> Утвердить
                      </button>
                    )}
                    {canManageOrders() && order.status === 'УТВЕРЖДЕНА' && (
                      <button
                        onClick={() => openCostModal(order)}
                        className="flex items-center justify-center gap-2 w-full py-2 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors text-sm"
                      >
                        <DollarSign size={16} /> Стоимость
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedOrder(order)}
                      className="flex items-center justify-center gap-2 w-full py-2 bg-[var(--blue-ios)] text-white rounded-lg font-medium hover:bg-blue-600 transition-colors text-sm"
                    >
                      <Info size={16} /> Подробнее
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Details Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedOrder(null)}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-[var(--bg-card)] rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-6 border-b border-[var(--separator)] flex justify-between items-center sticky top-0 bg-[var(--bg-card)] z-10">
              <div>
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Truck className="text-[var(--blue-ios)]" />
                  Заявка #{selectedOrder.id}
                </h2>
                <div className="mt-1">
                  <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getStatusColor(selectedOrder.status)}`}>
                    {getStatusText(selectedOrder.status)}
                  </span>
                </div>
              </div>
              <button onClick={() => setSelectedOrder(null)} className="p-2 hover:bg-[var(--bg-ios)] rounded-full text-[var(--text-secondary)]">
                <X size={24} />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Details Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-[var(--bg-ios)] p-4 rounded-xl">
                  <div className="flex items-center gap-2 mb-2 text-[var(--text-secondary)] font-medium text-sm">
                    <User size={16} /> Заявитель
                  </div>
                  <div className="font-semibold text-[var(--text-primary)]">{selectedOrder.foreman_name || 'Неизвестно'}</div>
                  <div className="text-xs text-[var(--text-secondary)] mt-1">{selectedOrder.foreman_phone}</div>
                </div>
                <div className="bg-[var(--bg-ios)] p-4 rounded-xl">
                  <div className="flex items-center gap-2 mb-2 text-[var(--text-secondary)] font-medium text-sm">
                    <MapPin size={16} /> Объект
                  </div>
                  <div className="font-semibold text-[var(--text-primary)]">{selectedOrder.cost_object_name || `Объект ${selectedOrder.cost_object_id}`}</div>
                </div>
                <div className="bg-[var(--bg-ios)] p-4 rounded-xl">
                  <div className="flex items-center gap-2 mb-2 text-[var(--text-secondary)] font-medium text-sm">
                    <Calendar size={16} /> Сроки
                  </div>
                  <div className="font-semibold text-[var(--text-primary)]">
                    {new Date(selectedOrder.start_date).toLocaleDateString('ru')} - {new Date(selectedOrder.end_date).toLocaleDateString('ru')}
                  </div>
                  <div className="text-xs text-[var(--text-secondary)] mt-1">
                    {calculateDays(selectedOrder.start_date, selectedOrder.end_date)} дней
                  </div>
                </div>
                <div className="bg-[var(--bg-ios)] p-4 rounded-xl border border-green-100">
                  <div className="flex items-center gap-2 mb-2 text-[var(--text-secondary)] font-medium text-sm">
                    <CreditCard size={16} /> Финансы
                  </div>
                  <div className="font-semibold text-green-700 text-lg">
                    {selectedOrder.total_cost ? `${selectedOrder.total_cost.toLocaleString('ru')} ₽` : '---'}
                  </div>
                  {selectedOrder.hour_rate && (
                    <div className="text-xs text-[var(--text-secondary)] mt-1">
                      Ставка: {selectedOrder.hour_rate} ₽/ч
                    </div>
                  )}
                </div>
              </div>

              {selectedOrder.description && (
                <div className="bg-yellow-50 border border-yellow-100 p-4 rounded-xl">
                  <h4 className="font-medium text-yellow-800 flex items-center gap-2 mb-2">
                    <Info size={16} /> Описание работ
                  </h4>
                  <p className="text-yellow-900 text-sm whitespace-pre-wrap">{selectedOrder.description}</p>
                </div>
              )}

              {selectedOrder.rejection_reason && (
                <div className="bg-red-50 border border-red-100 p-4 rounded-xl">
                  <h4 className="font-medium text-red-800 flex items-center gap-2 mb-2">
                    <AlertCircle size={16} /> Причина отклонения
                  </h4>
                  <p className="text-red-900 text-sm">{selectedOrder.rejection_reason}</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}

      {/* Cost Modal */}
      {showCostModal && costOrder && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-[60] p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-[var(--bg-card)] rounded-2xl shadow-xl w-full max-w-sm p-6"
          >
            <h3 className="text-lg font-bold mb-4 text-[var(--text-primary)]">Установить стоимость</h3>
            <p className="text-sm text-[var(--text-secondary)] mb-4">
              Укажите почасовую ставку для <strong>{getEquipmentTypeText(costOrder.equipment_type)}</strong>
            </p>

            <div className="mb-6">
              <label className="block text-sm font-medium mb-1.5 text-[var(--text-secondary)]">Ставка (₽/час)</label>
              <input
                type="number"
                value={hourRate}
                onChange={(e) => setHourRate(e.target.value)}
                className="w-full p-3 bg-[var(--bg-ios)] rounded-xl border-none outline-none focus:ring-2 focus:ring-[var(--blue-ios)]"
                placeholder="0.00"
                autoFocus
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowCostModal(false)}
                className="flex-1 py-2.5 bg-gray-100 text-gray-600 rounded-xl font-medium hover:bg-gray-200 transition-colors"
              >
                Отмена
              </button>
              <button
                onClick={handleSetCost}
                disabled={!hourRate}
                className="flex-1 py-2.5 bg-[var(--blue-ios)] text-white rounded-xl font-medium hover:bg-blue-600 transition-colors disabled:opacity-50"
              >
                Сохранить
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
