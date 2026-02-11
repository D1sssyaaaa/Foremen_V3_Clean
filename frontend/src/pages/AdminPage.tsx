import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  Smartphone,
  Phone,
  Edit2,
  Check,
  X,
  Search,
  Lock,
  Unlock,
  Plus,
  Trash2,
  Database
} from 'lucide-react';
import { objectFields, FieldDefinition } from '../utils/objectFields';

interface User {
  id: number;
  username: string;
  phone: string;
  email: string | null;
  roles: string[];
  telegram_chat_id: number | null;
  is_active: boolean;
  full_name: string | null;
  created_at: string;
}

const ALL_ROLES = [
  { value: 'ADMIN', label: 'Администратор', color: 'bg-red-100 text-red-700 border-red-200' },
  { value: 'MANAGER', label: 'Менеджер', color: 'bg-purple-100 text-purple-700 border-purple-200' },
  { value: 'ACCOUNTANT', label: 'Бухгалтер', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  { value: 'HR_MANAGER', label: 'HR Менеджер', color: 'bg-green-100 text-green-700 border-green-200' },
  { value: 'EQUIPMENT_MANAGER', label: 'Мех. Техники', color: 'bg-orange-100 text-orange-700 border-orange-200' },
  { value: 'MATERIALS_MANAGER', label: 'Снабженец', color: 'bg-amber-100 text-amber-700 border-amber-200' },
  { value: 'PROCUREMENT_MANAGER', label: 'Закупщик', color: 'bg-teal-100 text-teal-700 border-teal-200' },
  { value: 'FOREMAN', label: 'Бригадир', color: 'bg-slate-100 text-slate-700 border-slate-200' },
];

export function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'users' | 'fields'>('users');

  // Edit Users State
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [showEditModal, setShowEditModal] = useState(false);

  // Edit Fields State
  const [fields, setFields] = useState<FieldDefinition[]>([]);
  const [newField, setNewField] = useState<Partial<FieldDefinition>>({ type: 'text' });

  useEffect(() => {
    loadUsers();
    setFields(objectFields.getFields());
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<User[]>('/users');
      setUsers(data);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };

  const startEditing = (user: User) => {
    setEditingUserId(user.id);
    setSelectedRoles([...user.roles]);
    setShowEditModal(true);
  };

  const saveRoles = async () => {
    if (!editingUserId) return;
    try {
      await apiClient.put(`/users/${editingUserId}/roles`, { roles: selectedRoles });
      await loadUsers();
      setShowEditModal(false);
      setEditingUserId(null);
    } catch (error: any) {
      alert(error?.response?.data?.detail || 'Ошибка обновления ролей');
    }
  };

  const toggleRole = (role: string) => {
    if (selectedRoles.includes(role)) {
      setSelectedRoles(prev => prev.filter(r => r !== role));
    } else {
      setSelectedRoles(prev => [...prev, role]);
    }
  };

  const toggleUserActive = async (userId: number, currentStatus: boolean, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.put(`/users/${userId}/active`, { is_active: !currentStatus });
      setUsers(users.map(u => u.id === userId ? { ...u, is_active: !currentStatus } : u));
    } catch (error) {
      alert('Ошибка изменения статуса');
    }
  };

  const getRoleInfo = (roleValue: string) => {
    return ALL_ROLES.find(r => r.value === roleValue) || { label: roleValue, color: 'bg-gray-100 text-gray-600' };
  };

  const handleAddField = () => {
    if (!newField.id || !newField.label) {
      alert('Заполните ID и название поля');
      return;
    }
    const updated = [...fields, newField as FieldDefinition];
    setFields(updated);
    objectFields.saveFields(updated);
    setNewField({ type: 'text', id: '', label: '' });
  };

  const handleDeleteField = (id: string) => {
    const updated = fields.filter(f => f.id !== id);
    setFields(updated);
    objectFields.saveFields(updated);
  };

  const filteredUsers = users.filter(user =>
    (user.full_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.phone.includes(searchQuery)
  );

  return (
    <div className="space-y-6 animate-fade-in pb-20 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2">
            <Shield className="text-[var(--blue-ios)]" /> Администрирование
          </h1>
          <p className="text-[var(--text-secondary)]">Управление системой</p>
        </div>

        <div className="flex bg-[var(--bg-ios)] p-1 rounded-xl">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'users' ? 'bg-white shadow-sm text-[var(--text-primary)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
          >
            Пользователи
          </button>
          <button
            onClick={() => setActiveTab('fields')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'fields' ? 'bg-white shadow-sm text-[var(--text-primary)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
          >
            Поля объектов
          </button>
        </div>
      </div>

      {activeTab === 'users' ? (
        <>
          <div className="relative w-full md:w-64 mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" size={18} />
            <input
              type="text"
              placeholder="Поиск сотрудников..."
              className="w-full pl-10 pr-4 py-2.5 bg-[var(--bg-card)] border border-[var(--separator)] rounded-xl outline-none focus:ring-2 focus:ring-[var(--blue-ios)]"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="h-40 bg-[var(--bg-card)] rounded-2xl animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              <AnimatePresence>
                {filteredUsers.map(user => (
                  <motion.div
                    key={user.id}
                    layout
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    onClick={() => startEditing(user)}
                    className={`
                              bg-[var(--bg-card)] p-5 rounded-2xl border transition-all cursor-pointer group hover:shadow-md relative overflow-hidden
                              ${!user.is_active ? 'opacity-75 border-red-200 bg-red-50/10' : 'border-[var(--separator)] hover:border-[var(--blue-ios)]'}
                           `}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`
                                    w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold
                                    ${user.is_active ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white' : 'bg-gray-200 text-gray-500'}
                                 `}>
                          {(user.full_name || user.username).substring(0, 1).toUpperCase()}
                        </div>
                        <div>
                          <h3 className="font-bold text-[var(--text-primary)] leading-tight">{user.full_name || 'Без имени'}</h3>
                          <div className="text-sm text-[var(--text-secondary)]">@{user.username}</div>
                        </div>
                      </div>
                      <button
                        onClick={(e) => toggleUserActive(user.id, user.is_active, e)}
                        className={`p-2 rounded-full transition-colors ${user.is_active ? 'text-green-600 bg-green-50 hover:bg-green-100' : 'text-red-600 bg-red-50 hover:bg-red-100'}`}
                        title={user.is_active ? 'Активен' : 'Заблокирован'}
                      >
                        {user.is_active ? <Unlock size={18} /> : <Lock size={18} />}
                      </button>
                    </div>

                    <div className="space-y-2 mb-4 text-sm text-[var(--text-secondary)]">
                      <div className="flex items-center gap-2">
                        <Phone size={14} /> {user.phone}
                      </div>
                      {user.telegram_chat_id && (
                        <div className="flex items-center gap-2 text-blue-600">
                          <Smartphone size={14} /> Telegram подключен
                        </div>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2 mt-auto">
                      {user.roles.length > 0 ? user.roles.map(role => {
                        const info = getRoleInfo(role);
                        return (
                          <span key={role} className={`px-2 py-1 rounded-lg text-xs font-bold border ${info.color}`}>
                            {info.label}
                          </span>
                        );
                      }) : (
                        <span className="text-xs text-[var(--text-secondary)] bg-[var(--bg-ios)] px-2 py-1 rounded-lg">Нет ролей</span>
                      )}
                    </div>

                    <div className="absolute inset-0 bg-white/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[1px]">
                      <span className="bg-[var(--blue-ios)] text-white px-4 py-2 rounded-full font-bold shadow-lg transform translate-y-2 group-hover:translate-y-0 transition-transform">
                        <Edit2 size={16} className="inline mr-2" /> Изменить роли
                      </span>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </>
      ) : (
        <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--separator)] overflow-hidden">
          <div className="p-6 border-b border-[var(--separator)] bg-[var(--bg-ios)]">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <Database size={20} className="text-[var(--blue-ios)]" /> Настройка полей объекта
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">Добавьте поля, которые будут отображаться в карточке объекта.</p>
          </div>

          {/* Add Field Form */}
          <div className="p-6 bg-white border-b border-[var(--separator)] grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div>
              <label className="block text-xs font-bold uppercase text-[var(--text-secondary)] mb-1">ID (лат.)</label>
              <input
                type="text"
                value={newField.id || ''}
                onChange={e => setNewField({ ...newField, id: e.target.value })}
                placeholder="example_field"
                className="w-full p-2 rounded-lg border border-[var(--separator)] bg-[var(--bg-ios)]"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase text-[var(--text-secondary)] mb-1">Название</label>
              <input
                type="text"
                value={newField.label || ''}
                onChange={e => setNewField({ ...newField, label: e.target.value })}
                placeholder="Пример Поля"
                className="w-full p-2 rounded-lg border border-[var(--separator)] bg-[var(--bg-ios)]"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase text-[var(--text-secondary)] mb-1">Тип</label>
              <select
                value={newField.type}
                onChange={e => setNewField({ ...newField, type: e.target.value as any })}
                className="w-full p-2 rounded-lg border border-[var(--separator)] bg-[var(--bg-ios)]"
              >
                <option value="text">Текст</option>
                <option value="number">Число</option>
                <option value="link">Ссылка/Файл</option>
                <option value="select">Выбор</option>
                <option value="date">Дата</option>
              </select>
            </div>
            <button
              onClick={handleAddField}
              className="flex items-center justify-center gap-2 p-2 rounded-lg bg-[var(--blue-ios)] text-white font-bold hover:bg-blue-600 transition-colors"
            >
              <Plus size={18} /> Добавить
            </button>
          </div>

          {/* Field List */}
          <div className="divide-y divide-[var(--separator)]">
            {fields.map((field, idx) => (
              <div key={idx} className="p-4 flex items-center justify-between hover:bg-[var(--bg-ios)] transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center text-gray-500 font-mono text-xs">
                    {field.type}
                  </div>
                  <div>
                    <div className="font-bold text-[var(--text-primary)]">{field.label}</div>
                    <div className="text-xs text-[var(--text-secondary)] font-mono">{field.id}</div>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteField(field.id)}
                  className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  title="Удалить"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
            {fields.length === 0 && (
              <div className="p-10 text-center text-[var(--text-secondary)]">Нет созданных полей. Добавьте первое поле.</div>
            )}
          </div>
        </div>
      )}

      {/* Edit Roles Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowEditModal(false)}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-[var(--bg-card)] rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-5 border-b border-[var(--separator)] bg-[var(--bg-ios)] flex justify-between items-center">
              <h2 className="text-lg font-bold">Управление доступом</h2>
              <button onClick={() => setShowEditModal(false)}><X size={20} /></button>
            </div>

            <div className="p-6">
              <p className="text-sm text-[var(--text-secondary)] mb-4">Выберите роли для сотрудника. Это определит доступ к разделам системы.</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {ALL_ROLES.map(role => {
                  const isSelected = selectedRoles.includes(role.value);
                  return (
                    <button
                      key={role.value}
                      onClick={() => toggleRole(role.value)}
                      className={`
                                 p-3 rounded-xl border flex items-center gap-3 transition-all text-left relative overflow-hidden
                                 ${isSelected
                          ? `border-[var(--blue-ios)] bg-blue-50/50`
                          : 'border-[var(--separator)] hover:bg-[var(--bg-ios)]'}
                              `}
                    >
                      <div className={`
                                 w-5 h-5 rounded-full border flex items-center justify-center flex-shrink-0
                                 ${isSelected ? 'bg-[var(--blue-ios)] border-[var(--blue-ios)]' : 'border-gray-300'}
                              `}>
                        {isSelected && <Check size={12} className="text-white" />}
                      </div>
                      <span className={`text-sm font-medium ${isSelected ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}`}>
                        {role.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="p-4 border-t border-[var(--separator)] bg-[var(--bg-card)] flex gap-3">
              <button onClick={() => setShowEditModal(false)} className="flex-1 py-3 rounded-xl bg-[var(--bg-ios)] font-medium">Отмена</button>
              <button onClick={saveRoles} className="flex-1 py-3 rounded-xl bg-[var(--blue-ios)] text-white font-bold shadow-lg">Сохранить</button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
