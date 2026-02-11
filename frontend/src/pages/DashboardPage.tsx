import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { apiClient } from '../api/client';
import { motion } from 'framer-motion';
import {
  Building2,
  FileText,
  Package,
  Truck,
  BarChart3
} from 'lucide-react';
import { TopObjectsChart } from '../components/TopObjectsChart';
import { TopEquipmentChart } from '../components/TopEquipmentChart';

interface DashboardStats {
  objects: number;
  upd: number;
  newUPD?: number;
  materialRequests: number;
  equipmentOrders: number;
  timesheets?: number;
  newMaterialRequests?: number;
  pendingEquipment?: number;
  completedObjects?: number;
}

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    objects: 0,
    upd: 0,
    newUPD: 0,
    materialRequests: 0,
    equipmentOrders: 0,
    newMaterialRequests: 0,
    pendingEquipment: 0,
  });

  const [activeModal, setActiveModal] = useState<'upd' | null>(null);

  useEffect(() => {
    const loadStats = async () => {
      if (!user) return;

      try {
        const [objectsRes, updRes, materialsRes, equipmentRes] = await Promise.all([
          apiClient.get<any[]>('/objects/').catch(() => []),
          apiClient.get<any[]>('/upd/').catch(() => []),
          apiClient.get<any[]>('/material-requests/').catch(() => []),
          apiClient.get<any[]>('/equipment-orders/').catch(() => []),
        ]);

        setStats({
          objects: Array.isArray(objectsRes) ? objectsRes.length : 0,
          upd: Array.isArray(updRes) ? updRes.length : 0,
          newUPD: Array.isArray(updRes) ? updRes.filter((u: any) => u.status === 'NEW').length : 0,
          materialRequests: Array.isArray(materialsRes) ? materialsRes.length : 0,
          equipmentOrders: Array.isArray(equipmentRes) ? equipmentRes.length : 0,
          newMaterialRequests: Array.isArray(materialsRes) ? materialsRes.filter((r: any) => r.status === 'NEW').length : 0,
          pendingEquipment: Array.isArray(equipmentRes) ? equipmentRes.filter((o: any) => o.status === 'NEW').length : 0,
        });
      } catch (error) {
        console.error('Failed to load dashboard stats:', error);
      }
    };

    loadStats();
  }, [user]);

  const cards = [
    {
      title: 'Объекты',
      value: stats.objects,
      icon: Building2,
      color: 'text-blue-500',
      bg: 'bg-blue-50',
      path: '/objects',
      subtitle: 'активных'
    },
    {
      title: 'УПД документы',
      value: stats.upd,
      icon: FileText,
      color: 'text-purple-500',
      bg: 'bg-purple-50',
      path: '/upd',
      type: 'upd' as const,
      subtitle: stats.newUPD ? `${stats.newUPD} новых` : 'все обработаны',
      highlight: !!stats.newUPD
    },
    {
      title: 'Заявки на материалы',
      value: stats.materialRequests,
      icon: Package,
      color: 'text-orange-500',
      bg: 'bg-orange-50',
      path: '/material-requests',
      subtitle: stats.newMaterialRequests ? `${stats.newMaterialRequests} новых` : 'в работе'
    },
    {
      title: 'Заявки на технику',
      value: stats.equipmentOrders,
      icon: Truck,
      color: 'text-green-500',
      bg: 'bg-green-50',
      path: '/equipment-orders',
      subtitle: stats.pendingEquipment ? `${stats.pendingEquipment} ожидают` : 'в работе'
    }
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">
            Добро пожаловать, {user?.full_name || user?.username}
          </h2>
          <p className="text-[var(--text-secondary)] mt-1">
            Обзор текущего состояния системы
          </p>
        </div>
        <div className="px-4 py-2 bg-[var(--bg-card)] rounded-xl border border-[var(--separator)] text-sm font-medium text-[var(--text-secondary)] shadow-sm">
          {new Date().toLocaleDateString('ru-RU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card, index) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={index}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                if (card.type === 'upd' && stats.newUPD! > 0) {
                  setActiveModal('upd');
                } else {
                  navigate(card.path);
                }
              }}
              className="bg-[var(--bg-card)] rounded-2xl p-6 shadow-sm border border-[var(--separator)] cursor-pointer relative overflow-hidden group transition-all hover:shadow-md"
            >
              <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl ${card.bg} ${card.color}`}>
                  <Icon size={24} strokeWidth={2} />
                </div>
                {card.highlight && (
                  <span className="flex h-3 w-3 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                  </span>
                )}
              </div>

              <div className="space-y-1">
                <div className="text-3xl font-bold text-[var(--text-primary)]">
                  {card.value}
                </div>
                <div className="font-medium text-[var(--text-primary)]">
                  {card.title}
                </div>
                <div className={`text-sm ${card.highlight ? 'text-red-500 font-bold' : 'text-[var(--text-secondary)]'}`}>
                  {card.subtitle}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[var(--bg-card)] rounded-2xl p-6 shadow-sm border border-[var(--separator)]">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="text-blue-500" size={20} />
            <h3 className="text-lg font-semibold text-[var(--text-primary)] m-0">
              Топ объектов по доставкам
            </h3>
          </div>
          <TopObjectsChart />
        </div>

        <div className="bg-[var(--bg-card)] rounded-2xl p-6 shadow-sm border border-[var(--separator)]">
          <div className="flex items-center gap-2 mb-6">
            <Truck className="text-green-500" size={20} />
            <h3 className="text-lg font-semibold text-[var(--text-primary)] m-0">
              Расходы на технику
            </h3>
          </div>
          <TopEquipmentChart />
        </div>
      </div>

      {stats.objects === 0 && (
        <div className="bg-yellow-50 border border-yellow-100 rounded-2xl p-6">
          <h4 className="text-yellow-800 font-bold mb-2 m-0 text-lg">💡 Начало работы</h4>
          <p className="text-yellow-700 m-0">
            Для начала работы создайте объекты учёта, загрузите УПД документы или используйте Telegram бот для создания заявок.
          </p>
        </div>
      )}

      {/* Modern Modal */}
      {activeModal === 'upd' && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-[var(--bg-card)] rounded-2xl shadow-2xl max-w-sm w-full overflow-hidden border border-[var(--separator)]"
          >
            <div className="p-6 text-center">
              <div className="mx-auto bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mb-4">
                <FileText className="text-purple-600" size={32} />
              </div>
              <h3 className="text-xl font-bold mb-2 text-[var(--text-primary)]">
                УПД Документы
              </h3>

              <div className="space-y-3 mb-6">
                <div className="p-3 bg-[var(--bg-ios)] rounded-xl flex justify-between items-center">
                  <span className="text-[var(--text-secondary)] text-sm">Всего</span>
                  <span className="text-lg font-bold text-[var(--text-primary)]">{stats.upd}</span>
                </div>

                {stats.newUPD! > 0 && (
                  <div className="p-3 bg-green-50 rounded-xl border border-green-100 flex justify-between items-center">
                    <span className="text-green-700 text-sm font-medium">Требуют внимания</span>
                    <span className="text-lg font-bold text-green-700">{stats.newUPD}</span>
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <button
                  onClick={() => { setActiveModal(null); navigate('/upd'); }}
                  className="w-full py-3.5 bg-[var(--blue-ios)] text-white rounded-xl font-semibold text-[17px] active:scale-[0.98] transition-transform"
                >
                  Перейти к списку
                </button>
                <button
                  onClick={() => setActiveModal(null)}
                  className="w-full py-3.5 text-[var(--blue-ios)] hover:bg-[var(--bg-ios)] rounded-xl font-medium transition-colors"
                >
                  Отмена
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
