import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

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
  { value: 'ADMIN', label: 'Администратор', color: '#e74c3c' },
  { value: 'MANAGER', label: 'Менеджер', color: '#9b59b6' },
  { value: 'ACCOUNTANT', label: 'Бухгалтер', color: '#3498db' },
  { value: 'HR_MANAGER', label: 'HR Менеджер', color: '#1abc9c' },
  { value: 'EQUIPMENT_MANAGER', label: 'Менеджер техники', color: '#f39c12' },
  { value: 'MATERIALS_MANAGER', label: 'Менеджер материалов', color: '#e67e22' },
  { value: 'PROCUREMENT_MANAGER', label: 'Менеджер закупок', color: '#16a085' },
  { value: 'FOREMAN', label: 'Бригадир', color: '#34495e' },
];

export function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<User[]>('/users');
      setUsers(data);
    } catch (error) {
      console.error('Failed to load users:', error);
      alert('Не удалось загрузить пользователей');
    } finally {
      setLoading(false);
    }
  };

  const startEditing = (user: User) => {
    setEditingUserId(user.id);
    setSelectedRoles([...user.roles]);
  };

  const cancelEditing = () => {
    setEditingUserId(null);
    setSelectedRoles([]);
  };

  const saveRoles = async (userId: number) => {
    try {
      await apiClient.put(`/users/${userId}/roles`, { roles: selectedRoles });
      await loadUsers();
      setEditingUserId(null);
      setSelectedRoles([]);
      alert('Роли успешно обновлены!');
    } catch (error: any) {
      console.error('Failed to update roles:', error);
      const errorMessage = error?.response?.data?.detail || 'Не удалось обновить роли';
      alert(errorMessage);
    }
  };

  const toggleRole = (role: string) => {
    if (selectedRoles.includes(role)) {
      setSelectedRoles(selectedRoles.filter(r => r !== role));
    } else {
      setSelectedRoles([...selectedRoles, role]);
    }
  };

  const toggleUserActive = async (userId: number, currentStatus: boolean) => {
    try {
      await apiClient.put(`/users/${userId}/active`, { is_active: !currentStatus });
      await loadUsers();
    } catch (error: any) {
      console.error('Failed to toggle user status:', error);
      const errorMessage = error?.response?.data?.detail || 'Не удалось изменить статус пользователя';
      alert(errorMessage);
    }
  };

  const getRoleInfo = (roleValue: string) => {
    return ALL_ROLES.find(r => r.value === roleValue) || { label: roleValue, color: '#95a5a6' };
  };

  return (
    <div style={{ padding: '30px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ margin: 0, marginBottom: '10px', color: '#2c3e50' }}>
          🔐 Администрирование
        </h1>
        <p style={{ margin: 0, color: '#7f8c8d' }}>
          Управление пользователями и их ролями
        </p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
          Загрузка...
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {users.map((user) => (
            <div
              key={user.id}
              style={{
                backgroundColor: 'white',
                border: '1px solid #ecf0f1',
                borderRadius: '8px',
                padding: '20px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '10px' }}>
                    <h3 style={{ margin: 0, color: '#2c3e50' }}>
                      {user.full_name || user.username}
                    </h3>
                    {!user.is_active && (
                      <span
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#e74c3c',
                          color: 'white',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: 'bold'
                        }}
                      >
                        ОТКЛЮЧЕН
                      </span>
                    )}
                    {user.telegram_chat_id && (
                      <span
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#3498db',
                          color: 'white',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}
                      >
                        📱 Telegram
                      </span>
                    )}
                  </div>
                  
                  <div style={{ fontSize: '14px', color: '#7f8c8d', marginBottom: '15px' }}>
                    <div>👤 @{user.username}</div>
                    <div>📞 {user.phone}</div>
                    {user.email && <div>📧 {user.email}</div>}
                  </div>

                  {/* Роли */}
                  {editingUserId === user.id ? (
                    <div>
                      <div style={{ marginBottom: '10px', fontWeight: 'bold', color: '#2c3e50' }}>
                        Выберите роли:
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '15px' }}>
                        {ALL_ROLES.map((role) => (
                          <button
                            key={role.value}
                            onClick={() => toggleRole(role.value)}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: selectedRoles.includes(role.value) ? role.color : 'white',
                              color: selectedRoles.includes(role.value) ? 'white' : '#2c3e50',
                              border: `2px solid ${role.color}`,
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '13px',
                              fontWeight: selectedRoles.includes(role.value) ? 'bold' : 'normal'
                            }}
                          >
                            {selectedRoles.includes(role.value) ? '✓ ' : ''}{role.label}
                          </button>
                        ))}
                      </div>
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <button
                          onClick={() => saveRoles(user.id)}
                          disabled={selectedRoles.length === 0}
                          style={{
                            padding: '8px 16px',
                            backgroundColor: selectedRoles.length > 0 ? '#27ae60' : '#95a5a6',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: selectedRoles.length > 0 ? 'pointer' : 'not-allowed',
                            fontSize: '14px'
                          }}
                        >
                          ✓ Сохранить
                        </button>
                        <button
                          onClick={cancelEditing}
                          style={{
                            padding: '8px 16px',
                            backgroundColor: '#95a5a6',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '14px'
                          }}
                        >
                          Отмена
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {user.roles.length === 0 ? (
                        <span style={{ color: '#95a5a6', fontSize: '14px' }}>Нет ролей</span>
                      ) : (
                        user.roles.map((role) => {
                          const roleInfo = getRoleInfo(role);
                          return (
                            <span
                              key={role}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: roleInfo.color,
                                color: 'white',
                                borderRadius: '6px',
                                fontSize: '13px',
                                fontWeight: 'bold'
                              }}
                            >
                              {roleInfo.label}
                            </span>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>

                {/* Действия */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginLeft: '20px' }}>
                  {editingUserId !== user.id && (
                    <>
                      <button
                        onClick={() => startEditing(user)}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: '#3498db',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        ✏️ Изменить роли
                      </button>
                      <button
                        onClick={() => toggleUserActive(user.id, user.is_active)}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: user.is_active ? '#e74c3c' : '#27ae60',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {user.is_active ? '🔒 Отключить' : '🔓 Включить'}
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Справка */}
      <div
        style={{
          marginTop: '30px',
          padding: '20px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          border: '1px solid #ecf0f1'
        }}
      >
        <h3 style={{ margin: '0 0 15px 0', color: '#2c3e50' }}>ℹ️ Описание ролей</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '10px' }}>
          {ALL_ROLES.map((role) => (
            <div key={role.value} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  width: '12px',
                  height: '12px',
                  backgroundColor: role.color,
                  borderRadius: '50%',
                  flexShrink: 0
                }}
              />
              <span style={{ fontSize: '14px', color: '#2c3e50' }}>
                <strong>{role.label}</strong>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
