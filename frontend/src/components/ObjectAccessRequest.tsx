import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/ObjectAccessRequest.css';

interface CostObject {
  id: number;
  name: string;
  code: string;
  status: string;
  contract_number?: string;
}

interface AccessRequest {
  id: number;
  object_id: number;
  object_name: string;
  object_code: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  reason?: string;
  created_at: string;
  rejection_reason?: string;
  processed_by?: string;
}

export const ObjectAccessRequest: React.FC = () => {
  const { token } = useAuth();
  const [objects, setObjects] = useState<CostObject[]>([]);
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedObjectId, setSelectedObjectId] = useState<number | null>(null);
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    fetchObjects();
    fetchMyRequests();
  }, [token]);

  const fetchObjects = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${import.meta.env.VITE_API_URL}/objects/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setObjects(data);
      }
    } catch (err) {
      setError('Ошибка загрузки объектов');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchMyRequests = async () => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/objects/access-requests/my`,
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
      console.error('Ошибка загрузки запросов:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedObjectId) return;

    try {
      setSubmitting(true);
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/objects/${selectedObjectId}/request-access`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ reason: reason || null }),
        }
      );

      if (response.ok) {
        setSubmitted(true);
        setSelectedObjectId(null);
        setReason('');
        
        // Перезагружаем запросы
        setTimeout(() => {
          fetchMyRequests();
          setSubmitted(false);
        }, 2000);
      } else if (response.status === 400) {
        const data = await response.json();
        setError(data.detail || 'Ошибка при отправке запроса');
      }
    } catch (err) {
      setError('Ошибка при отправке запроса');
      console.error(err);
    } finally {
      setSubmitting(false);
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

  const hasRequestForObject = (objectId: number) => {
    return requests.some(
      (r) => r.object_id === objectId && r.status === 'PENDING'
    );
  };

  return (
    <div className="object-access-container">
      <h1>🏗️ Запрос доступа к объектам</h1>

      {error && <div className="alert alert-error">{error}</div>}
      {submitted && (
        <div className="alert alert-success">
          ✅ Запрос успешно отправлен!
        </div>
      )}

      <div className="access-content">
        {/* Левая колонка: Форма запроса */}
        <div className="request-form-section">
          <h2>Новый запрос</h2>

          {loading ? (
            <div className="loading">Загрузка объектов...</div>
          ) : objects.length === 0 ? (
            <div className="info-box">
              ℹ️ В системе нет доступных объектов
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="object-select">Выберите объект:</label>
                <select
                  id="object-select"
                  value={selectedObjectId || ''}
                  onChange={(e) => setSelectedObjectId(Number(e.target.value))}
                  disabled={submitting}
                  className="form-control"
                >
                  <option value="">-- Выберите объект --</option>
                  {objects.map((obj) => (
                    <option
                      key={obj.id}
                      value={obj.id}
                      disabled={hasRequestForObject(obj.id)}
                    >
                      {obj.code} - {obj.name}
                      {hasRequestForObject(obj.id) ? ' (запрос отправлен)' : ''}
                    </option>
                  ))}
                </select>
              </div>

              {selectedObjectId && (
                <>
                  <div className="object-details">
                    {objects
                      .filter((obj) => obj.id === selectedObjectId)
                      .map((obj) => (
                        <div key={obj.id} className="details-card">
                          <p>
                            <strong>Название:</strong> {obj.name}
                          </p>
                          <p>
                            <strong>Код:</strong> {obj.code}
                          </p>
                          {obj.contract_number && (
                            <p>
                              <strong>Контракт:</strong> {obj.contract_number}
                            </p>
                          )}
                          <p>
                            <strong>Статус:</strong> {obj.status}
                          </p>
                        </div>
                      ))}
                  </div>

                  <div className="form-group">
                    <label htmlFor="reason">Причина запроса (опционально):</label>
                    <textarea
                      id="reason"
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="Укажите причину, почему вам нужен доступ к этому объекту..."
                      className="form-control"
                      rows={4}
                      disabled={submitting}
                    />
                  </div>
                </>
              )}

              <button
                type="submit"
                disabled={!selectedObjectId || submitting}
                className="btn btn-primary btn-block"
              >
                {submitting ? '📤 Отправка...' : '✅ Отправить запрос'}
              </button>
            </form>
          )}
        </div>

        {/* Правая колонка: История запросов */}
        <div className="requests-history-section">
          <h2>📋 История запросов</h2>

          {requests.length === 0 ? (
            <div className="info-box">
              У вас пока нет запросов на доступ
            </div>
          ) : (
            <div className="requests-list">
              {requests.map((req) => (
                <div
                  key={req.id}
                  className={`request-card status-${req.status.toLowerCase()}`}
                >
                  <div className="request-header">
                    <span className="status-icon">
                      {getStatusIcon(req.status)}
                    </span>
                    <h4>{req.object_name}</h4>
                  </div>

                  <div className="request-body">
                    <p>
                      <strong>Код объекта:</strong> {req.object_code}
                    </p>
                    <p>
                      <strong>Статус:</strong>{' '}
                      <span className={`status-badge ${req.status.toLowerCase()}`}>
                        {getStatusText(req.status)}
                      </span>
                    </p>
                    <p>
                      <strong>Дата:</strong>{' '}
                      {new Date(req.created_at).toLocaleDateString('ru-RU')}
                    </p>

                    {req.reason && (
                      <p>
                        <strong>Причина:</strong> {req.reason}
                      </p>
                    )}

                    {req.rejection_reason && (
                      <div className="rejection-reason">
                        <strong>⚠️ Причина отклонения:</strong>
                        <p>{req.rejection_reason}</p>
                      </div>
                    )}

                    {req.processed_by && req.status !== 'PENDING' && (
                      <p className="processed-by">
                        <em>Обработано: {req.processed_by}</em>
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ObjectAccessRequest;
