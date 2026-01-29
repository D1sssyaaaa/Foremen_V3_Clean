import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiClient } from '../api/client';
import { formatPhone } from '../utils/formatters';

export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    birth_date: '',
    profile_photo_url: ''
  });
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [telegramCode, setTelegramCode] = useState<string | null>(null);
  const [telegramLoading, setTelegramLoading] = useState(false);
  const [showTelegramInstructions, setShowTelegramInstructions] = useState(false);

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        email: user.email || '',
        birth_date: user.birth_date || '',
        profile_photo_url: user.profile_photo_url || ''
      });
    }
  }, [user]);

  // Генерация кода привязки Telegram
  const handleGenerateTelegramCode = async () => {
    setTelegramLoading(true);
    setMessage('');
    try {
      const response = await apiClient.post('/users/me/telegram/generate-link-code', {});
      setTelegramCode((response as any).code);
      setShowTelegramInstructions(true);
      setMessage('');
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Ошибка при генерации кода';
      setMessage(errorMsg);
      console.error('Error generating telegram code:', error);
    } finally {
      setTelegramLoading(false);
    }
  };

  // Отвязка Telegram
  const handleUnlinkTelegram = async () => {
    if (!confirm('Отвязать Telegram аккаунт?')) return;
    
    setTelegramLoading(true);
    try {
      await apiClient.delete('/users/me/telegram/unlink');
      setMessage('Telegram успешно отвязан');
      setTelegramCode(null);
      setShowTelegramInstructions(false);
      if (refreshUser) {
        await refreshUser();
      }
    } catch (error) {
      setMessage('Ошибка при отвязке Telegram');
      console.error('Error unlinking telegram:', error);
    } finally {
      setTelegramLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      // Загрузка фото если выбрано
      if (photoFile) {
        const photoData = await apiClient.uploadFile('/auth/me/photo', photoFile);
        formData.profile_photo_url = (photoData as any).profile_photo_url;
      }

      // Обновление профиля
      await apiClient.patch('/auth/me/profile', formData);
      setMessage('Профиль успешно обновлен');
      setEditing(false);
      setPhotoFile(null);
      setPhotoPreview('');
      
      // Обновляем данные пользователя
      if (refreshUser) {
        await refreshUser();
      }
    } catch (error) {
      setMessage('Ошибка при обновлении профиля');
      console.error('Error updating profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Проверка размера (5 МБ)
      if (file.size > 5 * 1024 * 1024) {
        setMessage('Файл слишком большой. Максимум 5 МБ');
        return;
      }

      // Проверка формата
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        setMessage('Недопустимый формат. Разрешены: JPG, PNG, GIF, WebP');
        return;
      }

      setPhotoFile(file);
      
      // Создание превью
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDeletePhoto = async () => {
    if (!confirm('Удалить фото профиля?')) return;

    setLoading(true);
    try {
      await apiClient.delete('/auth/me/photo');
      setMessage('Фото удалено');
      if (refreshUser) {
        await refreshUser();
      }
    } catch (error) {
      setMessage('Ошибка при удалении фото');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <div>Загрузка...</div>;
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Профиль пользователя</h1>

      <div style={{
        backgroundColor: 'white',
        padding: '30px',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        maxWidth: '600px'
      }}>
        {/* Аватар */}
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          {(photoPreview || user.profile_photo_url) ? (
            <div style={{ position: 'relative', display: 'inline-block' }}>
              <img 
                src={photoPreview || `http://192.168.0.235:8000${user.profile_photo_url}`}
                alt="Profile"
                style={{ 
                  width: '120px', 
                  height: '120px', 
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '4px solid #3498db'
                }}
              />
              {editing && user.profile_photo_url && (
                <button
                  type="button"
                  onClick={handleDeletePhoto}
                  disabled={loading}
                  style={{
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    backgroundColor: '#e74c3c',
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    width: '30px',
                    height: '30px',
                    cursor: 'pointer',
                    fontSize: '16px'
                  }}
                  title="Удалить фото"
                >
                  ×
                </button>
              )}
            </div>
          ) : (
            <div style={{
              width: '120px',
              height: '120px',
              borderRadius: '50%',
              backgroundColor: '#3498db',
              color: 'white',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '48px',
              fontWeight: 'bold',
              border: '4px solid #2980b9',
              margin: '0 auto'
            }}>
              {(user.full_name || user.username)[0].toUpperCase()}
            </div>
          )}
        </div>

        {!editing ? (
          <>
            {/* Режим просмотра */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', color: '#7f8c8d', fontSize: '14px', marginBottom: '5px' }}>
                Логин
              </label>
              <div style={{ fontSize: '16px', fontWeight: '500' }}>{user.username}</div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', color: '#7f8c8d', fontSize: '14px', marginBottom: '5px' }}>
                ФИО
              </label>
              <div style={{ fontSize: '16px', fontWeight: '500' }}>
                {user.full_name || <span style={{ color: '#95a5a6' }}>Не указано</span>}
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', color: '#7f8c8d', fontSize: '14px', marginBottom: '5px' }}>
                Телефон
              </label>
              <div style={{ fontSize: '16px', fontWeight: '500' }}>{formatPhone(user.phone)}</div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', color: '#7f8c8d', fontSize: '14px', marginBottom: '5px' }}>
                Email
              </label>
              <div style={{ fontSize: '16px', fontWeight: '500' }}>
                {user.email || <span style={{ color: '#95a5a6' }}>Не указан</span>}
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', color: '#7f8c8d', fontSize: '14px', marginBottom: '5px' }}>
                Дата рождения
              </label>
              <div style={{ fontSize: '16px', fontWeight: '500' }}>
                {user.birth_date ? new Date(user.birth_date).toLocaleDateString('ru') : 
                  <span style={{ color: '#95a5a6' }}>Не указана</span>}
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', color: '#7f8c8d', fontSize: '14px', marginBottom: '5px' }}>
                Роли
              </label>
              <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                {user.roles.map(role => (
                  <span 
                    key={role}
                    style={{
                      padding: '4px 12px',
                      backgroundColor: '#ecf0f1',
                      borderRadius: '4px',
                      fontSize: '14px',
                      color: '#2c3e50'
                    }}
                  >
                    {role}
                  </span>
                ))}
              </div>
            </div>

            {/* Telegram привязка */}
            <div style={{ 
              marginBottom: '20px',
              padding: '15px',
              backgroundColor: '#f0f7ff',
              border: '1px solid #3498db',
              borderRadius: '4px'
            }}>
              <label style={{ display: 'block', color: '#2c3e50', fontSize: '14px', marginBottom: '10px', fontWeight: '600' }}>
                📱 Telegram
              </label>
              
              {user.telegram_chat_id ? (
                <div>
                  <div style={{ fontSize: '14px', color: '#27ae60', marginBottom: '10px' }}>
                    ✅ Telegram привязан (ID: {user.telegram_chat_id})
                  </div>
                  <button
                    type="button"
                    onClick={handleUnlinkTelegram}
                    disabled={telegramLoading}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#e74c3c',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: telegramLoading ? 'not-allowed' : 'pointer',
                      fontSize: '14px',
                      fontWeight: '500',
                      opacity: telegramLoading ? 0.6 : 1
                    }}
                  >
                    {telegramLoading ? 'Обработка...' : 'Отвязать Telegram'}
                  </button>
                </div>
              ) : (
                <div>
                  <div style={{ fontSize: '14px', color: '#e74c3c', marginBottom: '10px' }}>
                    ❌ Telegram не привязан
                  </div>
                  <button
                    type="button"
                    onClick={handleGenerateTelegramCode}
                    disabled={telegramLoading}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#3498db',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: telegramLoading ? 'not-allowed' : 'pointer',
                      fontSize: '14px',
                      fontWeight: '500',
                      marginBottom: '10px',
                      opacity: telegramLoading ? 0.6 : 1
                    }}
                  >
                    {telegramLoading ? 'Генерация кода...' : 'Генерировать код привязки'}
                  </button>

                  {telegramCode && (
                    <div style={{
                      marginTop: '15px',
                      padding: '12px',
                      backgroundColor: '#ecf0f1',
                      borderRadius: '4px',
                      border: '1px solid #bdc3c7'
                    }}>
                      <div style={{ fontSize: '12px', color: '#7f8c8d', marginBottom: '8px' }}>
                        Код действителен 15 минут. Используйте его один раз.
                      </div>
                      <div style={{
                        fontSize: '18px',
                        fontWeight: 'bold',
                        color: '#2c3e50',
                        marginBottom: '10px',
                        padding: '8px',
                        backgroundColor: 'white',
                        borderRadius: '4px',
                        textAlign: 'center',
                        letterSpacing: '2px',
                        fontFamily: 'monospace'
                      }}>
                        {telegramCode}
                      </div>
                      <button
                        type="button"
                        onClick={() => navigator.clipboard.writeText(telegramCode)}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#27ae60',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: '500'
                        }}
                      >
                        Скопировать код
                      </button>

                      {showTelegramInstructions && (
                        <div style={{
                          marginTop: '12px',
                          padding: '10px',
                          backgroundColor: '#fff3cd',
                          borderRadius: '4px',
                          fontSize: '12px',
                          color: '#856404',
                          lineHeight: '1.6'
                        }}>
                          <div style={{ fontWeight: '600', marginBottom: '5px' }}>📋 Инструкция:</div>
                          <div>1. Откройте Telegram бота</div>
                          <div>2. Отправьте команду: <code style={{ backgroundColor: '#ecf0f1', padding: '2px 4px' }}>/link {telegramCode}</code></div>
                          <div>3. Дождитесь подтверждения</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            <button
              onClick={() => setEditing(true)}
              style={{
                padding: '10px 20px',
                backgroundColor: '#3498db',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              Редактировать профиль
            </button>
          </>
        ) : (
          <>
            {/* Режим редактирования */}
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Логин</label>
                <input
                  type="text"
                  value={user.username}
                  disabled
                  style={{ 
                    width: '100%', 
                    padding: '8px', 
                    borderRadius: '4px', 
                    border: '1px solid #ddd',
                    backgroundColor: '#f5f5f5',
                    cursor: 'not-allowed'
                  }}
                />
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '5px' }}>
                  Логин нельзя изменить
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>ФИО</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '8px', 
                    borderRadius: '4px', 
                    border: '1px solid #ddd' 
                  }}
                  placeholder="Введите ваше ФИО"
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Телефон</label>
                <input
                  type="text"
                  value={formatPhone(user.phone)}
                  disabled
                  style={{ 
                    width: '100%', 
                    padding: '8px', 
                    borderRadius: '4px', 
                    border: '1px solid #ddd',
                    backgroundColor: '#f5f5f5',
                    cursor: 'not-allowed'
                  }}
                />
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '5px' }}>
                  Телефон нельзя изменить (используется для входа)
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '8px', 
                    borderRadius: '4px', 
                    border: '1px solid #ddd'
                  }}
                  placeholder="example@email.com"
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Дата рождения</label>
                <input
                  type="date"
                  value={formData.birth_date}
                  onChange={(e) => setFormData({...formData, birth_date: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '8px', 
                    borderRadius: '4px', 
                    border: '1px solid #ddd' 
                  }}
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Фото профиля</label>
                <input
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                  onChange={handlePhotoChange}
                  style={{ 
                    width: '100%', 
                    padding: '8px', 
                    borderRadius: '4px', 
                    border: '1px solid #ddd' 
                  }}
                />
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '5px' }}>
                  Форматы: JPG, PNG, GIF, WebP. Максимум 5 МБ
                </div>
                {photoFile && (
                  <div style={{ 
                    marginTop: '10px',
                    padding: '8px',
                    backgroundColor: '#e8f5e9',
                    borderRadius: '4px',
                    fontSize: '14px',
                    color: '#27ae60'
                  }}>
                    Выбрано: {photoFile.name} ({(photoFile.size / 1024).toFixed(1)} КБ)
                  </div>
                )}
              </div>

              {message && (
                <div style={{ 
                  padding: '10px', 
                  backgroundColor: message.includes('Ошибка') ? '#e74c3c' : '#27ae60',
                  color: 'white',
                  borderRadius: '4px',
                  marginBottom: '15px'
                }}>
                  {message}
                </div>
              )}

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#27ae60',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '500',
                    opacity: loading ? 0.6 : 1
                  }}
                >
                  {loading ? 'Сохранение...' : 'Сохранить'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setEditing(false);
                    setMessage('');
                  }}
                  disabled={loading}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#95a5a6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  Отмена
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
