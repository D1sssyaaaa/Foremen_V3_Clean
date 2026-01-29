import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/AdminAccessRequests.css';

interface AccessRequest {
  id: number;
  object_id: number;
  object_name: string;
  object_code: string;
  foreman_id: number;
  foreman_name: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  reason?: string;
  created_at: string;
  processed_at?: string;
  processed_by?: string;
  rejection_reason?: string;
}

interface CostObject {
  id: number;
  name: string;
  code: string;
}

type FilterStatus = 'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED';

export const AdminAccessRequests: React.FC = () => {
  const { token } = useAuth();
  const [objects, setObjects] = useState<CostObject[]>([]);
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [filteredRequests, setFilteredRequests] = useState<AccessRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [selectedObjectId, setSelectedObjectId] = useState<number | null>(null);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('PENDING');
  const [selectedRequest, setSelectedRequest] = useState<AccessRequest | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [processingId, setProcessingId] = useState<number | null>(null);

  useEffect(() => {
    fetchObjects();
  }, [token]);

  useEffect(() => {
    if (selectedObjectId) {
      fetchAccessRequests(selectedObjectId);
    }
  }, [selectedObjectId, token]);

  useEffect(() => {
    filterRequests();
  }, [requests, filterStatus]);

  const fetchObjects = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/objects/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setObjects(data);
        // Выбираем первый объект по умолчанию
        if (data.length > 0) {
          setSelectedObjectId(data[0].id);
        }
      }
    } catch (err) {
      setError('Ошибка загрузки объектов');
      console.error(err);
    }
  };

  const fetchAccessRequests = async (objectId: number) => {
    try {
      setLoading(true);
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/objects/${objectId}/access-requests`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setRequests(data);
      }
    } catch (err) {
      setError('Ошибка загрузки запросов');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filterRequests = () => {
    let filtered = requests;

    if (filterStatus !== 'ALL') {
      filtered = filtered.filter((r) => r.status === filterStatus);
    }

    setFilteredRequests(filtered);
  };

  const handleApprove = async (request: AccessRequest) => {
    try {
      setProcessingId(request.id);
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/objects/${request.object_id}/access-requests/${request.id}/approve`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        setSuccess(`✅ Запрос ${request.id} одобрен`);
        // Перезагружаем список
        if (selectedObjectId) {
          await fetchAccessRequests(selectedObjectId);
        }
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError('Ошибка при одобрении запроса');
      }
    } catch (err) {
      setError('Ошибка при обработке запроса');
      console.error(err);
    } finally {
      setProcessingId(null);
    }
  };

  const handleRejectClick = (request: AccessRequest) => {
    setSelectedRequest(request);
    setRejectReason('');
    setShowRejectModal(true);
  };

  const handleRejectSubmit = async () => {
    if (!selectedRequest) return;

    try {
      setProcessingId(selectedRequest.id);
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/objects/${selectedRequest.object_id}/access-requests/${selectedRequest.id}/reject`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ reason: rejectReason }),
        }
      );

      if (response.ok) {
        setSuccess(`❌ Запрос ${selectedRequest.id} отклонен`);
        setShowRejectModal(false);
        setRejectReason('');
        setSelectedRequest(null);

        // Перезагружаем список
        if (selectedObjectId) {
          await fetchAccessRequests(selectedObjectId);
        }
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError('Ошибка при отклонении запроса');
      }
    } catch (err) {
      setError('Ошибка при обработке запроса');
      console.error(err);
    } finally {
      setProcessingId(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PENDING':
        return '⏳';
      case 'APPROVED':
        return '✅';
      case 'REJECTED':
        return '❌';
      default:
        return '❓';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'На рассмотрении';
      case 'APPROVED':
        return 'Одобрено';
      case 'REJECTED':
        return 'Отклонено';
      default:
        return status;
    }
  };

  const getPendingCount = () => {
    return requests.filter((r) => r.status === 'PENDING').length;
  };

  return (
    <div className="admin-requests-container">
      <h1>🔐 Управление запросами доступа</h1>

      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)} className="btn-close">
            ×
          </button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
          <button onClick={() => setSuccess(null)} className="btn-close">
            ×
          </button>
        </div>
      )}

      <div className="admin-layout">
        {/* Боковая панель: выбор объекта и фильтр */}
        <aside className="admin-sidebar">
          <div className="sidebar-section">
            <h3>🏗️ Объекты</h3>
            <div className="object-list">
              {loading && !selectedObjectId ? (
                <div className="loading">Загрузка...</div>
              ) : objects.length === 0 ? (
                <div className="info">Нет объектов</div>
              ) : (
                objects.map((obj) => {
                  const pendingCount = requests.filter(
                    (r) => r.object_id === obj.id && r.status === 'PENDING'
                  ).length;

                  return (
                    <button
                      key={obj.id}
                      className={`object-button ${
                        selectedObjectId === obj.id ? 'active' : ''
                      }`}
                      onClick={() => setSelectedObjectId(obj.id)}
                    >
                      <span className="object-name">
                        {obj.code} - {obj.name}
                      </span>
                      {pendingCount > 0 && (
                        <span className="pending-badge">{pendingCount}</span>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </div>

          <div className="sidebar-section">
            <h3>📊 Фильтр</h3>
            <div className="filter-group">
              {(['ALL', 'PENDING', 'APPROVED', 'REJECTED'] as FilterStatus[]).map(
                (status) => (
                  <label key={status} className="filter-radio">
                    <input
                      type="radio"
                      name="status-filter"
                      value={status}
                      checked={filterStatus === status}
                      onChange={() => setFilterStatus(status)}
                    />
                    <span className="filter-label">
                      {status === 'ALL' && '📋 Все'}
                      {status === 'PENDING' && '⏳ На рассмотрении'}
                      {status === 'APPROVED' && '✅ Одобрено'}
                      {status === 'REJECTED' && '❌ Отклонено'}
                    </span>
                  </label>
                )
              )}
            </div>
          </div>

          <div className="sidebar-section sidebar-stats">
            <h3>📈 Статистика</h3>
            <div className="stat-item">
              <span className="stat-label">Всего запросов:</span>
              <span className="stat-value">{requests.length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">На рассмотрении:</span>
              <span className="stat-value pending">{getPendingCount()}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Одобрено:</span>
              <span className="stat-value approved">
                {requests.filter((r) => r.status === 'APPROVED').length}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Отклонено:</span>
              <span className="stat-value rejected">
                {requests.filter((r) => r.status === 'REJECTED').length}
              </span>
            </div>
          </div>
        </aside>

        {/* Основная область: список запросов */}
        <main className="admin-main">
          {!selectedObjectId ? (
            <div className="empty-state">
              <h2>Выберите объект</h2>
              <p>Выберите объект из списка слева для просмотра запросов</p>
            </div>
          ) : loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Загрузка запросов...</p>
            </div>
          ) : filteredRequests.length === 0 ? (
            <div className="empty-state">
              <h2>Нет запросов</h2>
              <p>
                {filterStatus === 'ALL'
                  ? 'Для этого объекта нет запросов на доступ'
                  : `Для этого объекта нет ${getStatusText(filterStatus).toLowerCase()} запросов`}
              </p>
            </div>
          ) : (
            <div className="requests-grid">
              {filteredRequests.map((request) => (
                <div
                  key={request.id}
                  className={`request-card status-${request.status.toLowerCase()}`}
                >
                  <div className="card-header">
                    <div className="header-title">
                      <span className="status-icon">
                        {getStatusIcon(request.status)}
                      </span>
                      <div>
                        <h4>{request.foreman_name}</h4>
                        <p className="foreman-info">Бригадир #{request.foreman_id}</p>
                      </div>
                    </div>
                    <span className={`status-badge ${request.status.toLowerCase()}`}>
                      {getStatusText(request.status)}
                    </span>
                  </div>

                  <div className="card-body">
                    <div className="info-row">
                      <span className="label">Объект:</span>
                      <span className="value">
                        {request.object_code} - {request.object_name}
                      </span>
                    </div>

                    <div className="info-row">
                      <span className="label">Дата запроса:</span>
                      <span className="value">
                        {new Date(request.created_at).toLocaleDateString('ru-RU', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>

                    {request.reason && (
                      <div className="info-row">
                        <span className="label">Причина:</span>
                        <p className="reason-text">{request.reason}</p>
                      </div>
                    )}

                    {request.rejection_reason && (
                      <div className="rejection-info">
                        <span className="label">Причина отклонения:</span>
                        <p>{request.rejection_reason}</p>
                      </div>
                    )}

                    {request.processed_at && (
                      <div className="processed-info">
                        <span className="label">Обработано:</span>
                        <span className="value">
                          {new Date(request.processed_at).toLocaleDateString('ru-RU')}
                          {request.processed_by && ` (${request.processed_by})`}
                        </span>
                      </div>
                    )}
                  </div>

                  {request.status === 'PENDING' && (
                    <div className="card-actions">
                      <button
                        className="btn btn-success"
                        onClick={() => handleApprove(request)}
                        disabled={processingId === request.id}
                      >
                        {processingId === request.id ? '⏳' : '✅'} Одобрить
                      </button>
                      <button
                        className="btn btn-danger"
                        onClick={() => handleRejectClick(request)}
                        disabled={processingId === request.id}
                      >
                        {processingId === request.id ? '⏳' : '❌'} Отклонить
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Модальное окно для отклонения */}
      {showRejectModal && selectedRequest && (
        <div className="modal-overlay" onClick={() => setShowRejectModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>❌ Отклонить запрос</h3>

            <div className="modal-body">
              <p>
                <strong>Бригадир:</strong> {selectedRequest.foreman_name}
              </p>
              <p>
                <strong>Объект:</strong> {selectedRequest.object_code} -{' '}
                {selectedRequest.object_name}
              </p>

              <div className="form-group">
                <label htmlFor="reject-reason">Причина отклонения:</label>
                <textarea
                  id="reject-reason"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Укажите причину отклонения запроса..."
                  rows={4}
                  className="form-control"
                />
              </div>
            </div>

            <div className="modal-actions">
              <button
                className="btn btn-secondary"
                onClick={() => setShowRejectModal(false)}
              >
                Отмена
              </button>
              <button
                className="btn btn-danger"
                onClick={handleRejectSubmit}
                disabled={!rejectReason.trim() || processingId === selectedRequest.id}
              >
                {processingId === selectedRequest.id ? '⏳ Отклонение...' : '❌ Отклонить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminAccessRequests;
