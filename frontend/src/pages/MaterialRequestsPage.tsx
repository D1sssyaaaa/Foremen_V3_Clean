import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import type { MaterialRequest, CostObject } from '../types';
import { motion } from 'framer-motion';
import {
  Package,
  Plus,
  Trash2,
  Calendar,
  Building2,
  X,
  Loader2,
  CheckCircle2,
  Clock
} from 'lucide-react';

export function MaterialRequestsPage() {
  const [requests, setRequests] = useState<MaterialRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [objects, setObjects] = useState<CostObject[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // New Request Form
  const [newRequest, setNewRequest] = useState({
    cost_object_id: 0,
    material_type: 'regular',
    urgency: 'normal',
    items: [{ name: '', quantity: 1, unit: 'шт', date_required: '' }]
  });

  useEffect(() => {
    loadRequests();
    loadObjects();
  }, []);

  const loadRequests = async () => {
    try {
      const data = await apiClient.get<MaterialRequest[]>('/material-requests/');
      setRequests(data);
    } catch (err) {
      console.error('Ошибка загрузки заявок:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadObjects = async () => {
    try {
      const data = await apiClient.get<CostObject[]>('/objects/');
      setObjects(data);
    } catch (err) {
      console.error('Ошибка загрузки объектов:', err);
    }
  };

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...newRequest,
        items: newRequest.items.map(item => ({
          material_name: item.name,
          quantity: item.quantity,
          unit: item.unit,
          description: item.date_required ? `Required by: ${item.date_required}` : undefined
        }))
      };
      await apiClient.post('/material-requests/', payload);
      setShowCreateModal(false);
      setNewRequest({
        cost_object_id: 0,
        material_type: 'regular',
        urgency: 'normal',
        items: [{ name: '', quantity: 1, unit: 'шт', date_required: '' }]
      });
      await loadRequests();
    } catch (err) {
      console.error('Ошибка создания заявки:', err);
      alert('Ошибка при создании заявки');
    }
  };

  const addItemRow = () => {
    setNewRequest({
      ...newRequest,
      items: [...newRequest.items, { name: '', quantity: 1, unit: 'шт', date_required: '' }]
    });
  };

  const removeItemRow = (index: number) => {
    const updatedItems = newRequest.items.filter((_, i) => i !== index);
    setNewRequest({ ...newRequest, items: updatedItems });
  };

  const updateItemRow = (index: number, field: string, value: any) => {
    const updatedItems = newRequest.items.map((item, i) => {
      if (i === index) return { ...item, [field]: value };
      return item;
    });
    setNewRequest({ ...newRequest, items: updatedItems });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NEW': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'APPROVED': return 'bg-green-100 text-green-700 border-green-200';
      case 'REJECTED': return 'bg-red-100 text-red-700 border-red-200';
      case 'Fulfilled': return 'bg-gray-100 text-gray-600 border-gray-200'; // Assuming 'Fulfilled' or similiar
      default: return 'bg-gray-100 text-gray-500 border-gray-200';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'NEW': return 'Новая';
      case 'APPROVED': return 'Согласована';
      case 'REJECTED': return 'Отклонена';
      default: return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'APPROVED': return <CheckCircle2 size={16} />;
      case 'NEW': return <Clock size={16} />;
      default: return null;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <Loader2 className="animate-spin text-[var(--blue-ios)]" size={40} />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in pb-20">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Заявки на материалы</h1>
          <p className="text-[var(--text-secondary)]">Управление снабжением объектов</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-[var(--blue-ios)] text-white px-5 py-2.5 rounded-xl font-medium active:scale-95 transition-transform shadow-sm hover:shadow-md"
        >
          <Plus size={20} />
          <span>Создать заявку</span>
        </button>
      </div>

      {requests.length === 0 ? (
        <div className="bg-[var(--bg-card)] p-10 rounded-2xl border border-[var(--separator)] text-center text-[var(--text-secondary)]">
          <div className="bg-orange-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Package size={32} className="text-orange-400" />
          </div>
          <h3 className="text-lg font-medium text-[var(--text-primary)]">Нет активных заявок</h3>
          <p>Создайте первую заявку на материалы для объекта</p>
        </div>
      ) : (
        <div className="bg-[var(--bg-card)] rounded-2xl shadow-sm border border-[var(--separator)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[var(--bg-ios)] border-b border-[var(--separator-opaque)] text-[var(--text-secondary)] text-sm font-semibold">
                  <th className="p-4 w-16 text-center">ID</th>
                  <th className="p-4">Дата</th>
                  <th className="p-4">Объект</th>
                  <th className="p-4 text-center">Позиций</th>
                  <th className="p-4 text-center">Статус</th>
                  <th className="p-4 text-right">Автор</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--separator-opaque)]">
                {requests.map(req => (
                  <tr
                    key={req.id}
                    className="hover:bg-[var(--bg-ios)] transition-colors cursor-pointer group"
                  // onClick={() => navigate(`/material-requests/${req.id}`)} // If detail page exists
                  >
                    <td className="p-4 text-center text-[var(--text-secondary)] font-mono text-xs">#{req.id}</td>
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-[var(--text-primary)]">
                        <Calendar size={14} className="text-[var(--text-secondary)]" />
                        {new Date(req.created_at).toLocaleDateString('ru')}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="font-medium text-[var(--text-primary)] flex items-center gap-2">
                        <Building2 size={16} className="text-blue-500" />
                        {objects.find(o => o.id === req.cost_object_id)?.name || 'Неизвестный объект'}
                      </div>
                    </td>
                    <td className="p-4 text-center text-[var(--text-secondary)]">
                      {req.items?.length || 0}
                    </td>
                    <td className="p-4 text-center">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(req.status)} inline-flex items-center gap-1.5`}>
                        {getStatusIcon(req.status)}
                        {getStatusText(req.status)}
                      </span>
                    </td>
                    <td className="p-4 text-right text-[var(--text-secondary)] text-sm">
                      {req.author_id ? `User #${req.author_id}` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="bg-[var(--bg-card)] rounded-2xl shadow-2xl max-w-2xl w-full flex flex-col max-h-[90vh]"
          >
            <div className="flex justify-between items-center p-6 border-b border-[var(--separator)]">
              <h2 className="text-xl font-bold text-[var(--text-primary)]">Новая заявка</h2>
              <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-[var(--bg-ios)] rounded-full transition-colors">
                <X size={24} className="text-[var(--text-secondary)]" />
              </button>
            </div>

            <form onSubmit={handleCreateRequest} className="p-6 overflow-y-auto space-y-6">
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Объект *</label>
                <div className="relative">
                  <select
                    required
                    value={newRequest.cost_object_id}
                    onChange={(e) => setNewRequest({ ...newRequest, cost_object_id: Number(e.target.value) })}
                    className="w-full p-3 pl-10 bg-[var(--bg-ios)] rounded-xl border-none focus:ring-2 focus:ring-[var(--blue-ios)] outline-none appearance-none"
                  >
                    <option value={0}>-- Выберите объект --</option>
                    {objects.map(obj => (
                      <option key={obj.id} value={obj.id}>{obj.name}</option>
                    ))}
                  </select>
                  <Building2 className="absolute left-3 top-3 text-[var(--text-secondary)]" size={18} />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-[var(--text-secondary)]">Материалы</label>
                  <button type="button" onClick={addItemRow} className="text-sm text-[var(--blue-ios)] font-medium hover:underline flex items-center gap-1">
                    <Plus size={14} /> Добавить позицию
                  </button>
                </div>

                <div className="space-y-3">
                  {newRequest.items.map((item, index) => (
                    <div key={index} className="flex gap-3 items-start bg-[var(--bg-ios)] p-3 rounded-xl relative group">
                      <div className="flex-1 space-y-2">
                        <input
                          placeholder="Название материала"
                          value={item.name}
                          onChange={(e) => updateItemRow(index, 'name', e.target.value)}
                          className="w-full p-2 bg-white rounded-lg border border-[var(--separator)] text-sm focus:border-[var(--blue-ios)] outline-none"
                          required
                        />
                        <div className="flex gap-2">
                          <input
                            type="number"
                            placeholder="Кол-во"
                            value={item.quantity}
                            onChange={(e) => updateItemRow(index, 'quantity', Number(e.target.value))}
                            className="w-24 p-2 bg-white rounded-lg border border-[var(--separator)] text-sm outline-none"
                            min="1"
                          />
                          <input
                            placeholder="Ед. изм"
                            value={item.unit}
                            onChange={(e) => updateItemRow(index, 'unit', e.target.value)}
                            className="w-20 p-2 bg-white rounded-lg border border-[var(--separator)] text-sm outline-none"
                          />
                          <input
                            type="date"
                            value={item.date_required}
                            onChange={(e) => updateItemRow(index, 'date_required', e.target.value)}
                            className="flex-1 p-2 bg-white rounded-lg border border-[var(--separator)] text-sm outline-none text-[var(--text-secondary)]"
                          />
                        </div>
                      </div>
                      {newRequest.items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeItemRow(index)}
                          className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 size={18} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
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
                  disabled={newRequest.cost_object_id === 0}
                  className="flex-1 py-3 bg-[var(--blue-ios)] text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 transition-all shadow-md hover:shadow-lg"
                >
                  Создать заявку
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
