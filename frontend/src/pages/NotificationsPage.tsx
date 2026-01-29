import { useState, useEffect } from 'react';
import { notificationsApi } from '../api/notifications';
import type { Notification } from '../types/notification';
import { useNavigate } from 'react-router-dom';

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const navigate = useNavigate();

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await notificationsApi.getAll({
        is_read: filter === 'unread' ? false : undefined,
        limit: 100
      });
      setNotifications(data);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [filter]);

  const handleMarkAsRead = async (id: number) => {
    try {
      await notificationsApi.markAsRead(id);
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Удалить это уведомление?')) return;
    
    try {
      await notificationsApi.delete(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const handleNotificationClick = async (notif: Notification) => {
    if (!notif.is_read) {
      await handleMarkAsRead(notif.id);
    }

    const data = notif.data;
    if (data) {
      if (notif.notification_type.includes('material_request')) {
        navigate('/material-requests');
      } else if (notif.notification_type.includes('equipment')) {
        navigate('/equipment-orders');
      } else if (notif.notification_type.includes('timesheet')) {
        navigate('/timesheets');
      }
    }
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getNotificationIcon = (type: string) => {
    if (type.includes('material')) return '📦';
    if (type.includes('equipment')) return '🚜';
    if (type.includes('timesheet')) return '⏰';
    if (type.includes('approved')) return '✅';
    if (type.includes('rejected')) return '❌';
    return '🔔';
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div style={{ padding: '30px', maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ margin: 0, marginBottom: '10px', color: '#2c3e50' }}>
          Уведомления
        </h1>
        <p style={{ margin: 0, color: '#7f8c8d' }}>
          {unreadCount > 0 ? `${unreadCount} непрочитанных` : 'Все уведомления прочитаны'}
        </p>
      </div>

      {/* Filters and Actions */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          padding: '15px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px'
        }}
      >
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => setFilter('all')}
            style={{
              padding: '8px 16px',
              backgroundColor: filter === 'all' ? '#3498db' : 'white',
              color: filter === 'all' ? 'white' : '#2c3e50',
              border: '1px solid #ddd',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Все ({notifications.length})
          </button>
          <button
            onClick={() => setFilter('unread')}
            style={{
              padding: '8px 16px',
              backgroundColor: filter === 'unread' ? '#3498db' : 'white',
              color: filter === 'unread' ? 'white' : '#2c3e50',
              border: '1px solid #ddd',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Непрочитанные ({unreadCount})
          </button>
        </div>

        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllAsRead}
            style={{
              padding: '8px 16px',
              backgroundColor: '#27ae60',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Отметить все как прочитанные
          </button>
        )}
      </div>

      {/* Notifications List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
          Загрузка...
        </div>
      ) : notifications.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '60px 20px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px'
          }}
        >
          <div style={{ fontSize: '64px', marginBottom: '20px' }}>🔕</div>
          <h3 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>Нет уведомлений</h3>
          <p style={{ margin: 0, color: '#7f8c8d' }}>
            {filter === 'unread' 
              ? 'Все уведомления прочитаны' 
              : 'У вас пока нет уведомлений'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {notifications.map((notif) => (
            <div
              key={notif.id}
              style={{
                padding: '20px',
                backgroundColor: notif.is_read ? 'white' : '#e3f2fd',
                border: '1px solid #ecf0f1',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                position: 'relative'
              }}
              onClick={() => handleNotificationClick(notif)}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'none';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ fontSize: '32px', flexShrink: 0 }}>
                  {getNotificationIcon(notif.notification_type)}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <h3
                      style={{
                        margin: 0,
                        fontSize: '16px',
                        fontWeight: notif.is_read ? 'normal' : 'bold',
                        color: '#2c3e50'
                      }}
                    >
                      {notif.title}
                    </h3>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(notif.id);
                      }}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: 'transparent',
                        color: '#e74c3c',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '18px'
                      }}
                    >
                      🗑️
                    </button>
                  </div>
                  <p style={{ margin: '0 0 10px 0', color: '#555', fontSize: '14px' }}>
                    {notif.message}
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', color: '#95a5a6' }}>
                      {formatDateTime(notif.created_at)}
                    </span>
                    {!notif.is_read && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleMarkAsRead(notif.id);
                        }}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#3498db',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Отметить прочитанным
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
