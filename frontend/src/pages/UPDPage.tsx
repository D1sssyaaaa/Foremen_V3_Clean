import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import type { UPDDocument, UPDDetailResponse, CostObject } from '../types';

export function UPDPage() {
  const [upds, setUpds] = useState<UPDDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  // Состояние для expandable rows
  const [expandedRowId, setExpandedRowId] = useState<number | null>(null);
  const [detailsCache, setDetailsCache] = useState<Record<number, UPDDetailResponse>>({});
  const [detailsLoading, setDetailsLoading] = useState<Record<number, boolean>>({});

  // Состояние для распределения
  const [objects, setObjects] = useState<CostObject[]>([]);
  const [distributeModalOpen, setDistributeModalOpen] = useState(false);
  const [selectedUpdForDistribution, setSelectedUpdForDistribution] = useState<number | null>(null);
  const [selectedObjectId, setSelectedObjectId] = useState<number | null>(null);

  useEffect(() => {
    loadUPDs();
    loadObjects();
  }, []);

  const loadObjects = async () => {
    try {
      const data = await apiClient.get<CostObject[]>('/objects/');
      console.log('Загружены объекты:', data);
      setObjects(data);
    } catch (err) {
      console.error('Ошибка загрузки объектов:', err);
      // alert('Ошибка загрузки списка объектов'); // Временно раскомментируйте для отладки
    }
  };

  const openDistributeModal = async (id: number) => {
    setSelectedUpdForDistribution(id);
    setSelectedObjectId(null);
    setDistributeModalOpen(true);

    // Убедимся что детали загружены
    if (!detailsCache[id]) {
      try {
        const detail = await apiClient.get<UPDDetailResponse>(`/material-costs/${id}`);
        setDetailsCache(prev => ({ ...prev, [id]: detail }));
      } catch (err) {
        console.error('Ошибка загрузки деталей для распределения:', err);
        alert('Не удалось загрузить данные документа');
        setDistributeModalOpen(false);
      }
    }
  };

  const handleDistribute = async () => {
    if (!selectedUpdForDistribution || !selectedObjectId) return;

    const details = detailsCache[selectedUpdForDistribution];
    if (!details) return;

    // Формируем запрос на полное распределение (все строки на один объект)
    const distributions = details.items.map(item => ({
      material_cost_item_id: item.id,
      cost_object_id: selectedObjectId,
      distributed_quantity: item.quantity,
      distributed_amount: item.amount
    }));

    try {
      await apiClient.post(`/material-costs/${selectedUpdForDistribution}/distribute`, { distributions });
      alert('УПД успешно распределен!');
      setDistributeModalOpen(false);
      loadUPDs(); // Обновляем список, чтобы сменился статус
    } catch (err: any) {
      console.error('Ошибка распределения:', err);
      alert(err.response?.data?.detail || 'Ошибка при распределении');
    }
  };

  const toggleRow = async (id: number) => {
    if (expandedRowId === id) {
      setExpandedRowId(null);
      return;
    }

    setExpandedRowId(id);

    // Загружаем детали если их нет в кеше
    if (!detailsCache[id] && !detailsLoading[id]) {
      setDetailsLoading(prev => ({ ...prev, [id]: true }));
      try {
        const detail = await apiClient.get<UPDDetailResponse>(`/material-costs/${id}`);
        setDetailsCache(prev => ({ ...prev, [id]: detail }));
      } catch (err) {
        console.error('Ошибка загрузки деталей:', err);
      } finally {
        setDetailsLoading(prev => ({ ...prev, [id]: false }));
      }
    }
  };

  const loadUPDs = async () => {
    try {
      const data = await apiClient.get<UPDDocument[]>('/material-costs/unprocessed');
      setUpds(data);
    } catch (err: any) {
      setError('Ошибка загрузки УПД');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError('');

    try {
      await apiClient.uploadFile('/material-costs/upload', file);
      await loadUPDs();
      alert('УПД успешно загружен!');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки файла');
    } finally {
      setUploading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NEW': return '#3498db';
      case 'DISTRIBUTED': return '#2ecc71';
      case 'ARCHIVED': return '#95a5a6';
      default: return '#7f8c8d';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'NEW': return 'Новый';
      case 'DISTRIBUTED': return 'Распределен';
      case 'ARCHIVED': return 'Архив';
      default: return status;
    }
  };

  if (loading) {
    return <div>Загрузка...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>УПД Документы</h1>
        <label style={{
          padding: '12px 24px',
          backgroundColor: '#3498db',
          color: 'white',
          borderRadius: '6px',
          cursor: uploading ? 'not-allowed' : 'pointer',
          opacity: uploading ? 0.6 : 1
        }}>
          {uploading ? 'Загрузка...' : 'Загрузить XML'}
          <input
            type="file"
            accept=".xml"
            onChange={handleFileUpload}
            disabled={uploading}
            style={{ display: 'none' }}
          />
        </label>
      </div>

      {error && (
        <div style={{
          padding: '12px',
          backgroundColor: '#fee',
          color: '#c33',
          borderRadius: '6px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {upds.length === 0 ? (
        <div style={{
          backgroundColor: 'white',
          padding: '40px',
          borderRadius: '8px',
          textAlign: 'center',
          color: '#7f8c8d'
        }}>
          Нет необработанных УПД. Загрузите XML файл для начала работы.
        </div>
      ) : (
        <div style={{ backgroundColor: 'white', borderRadius: '8px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
                <th style={{ width: '40px' }}></th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Номер</th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Дата</th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Поставщик</th>
                <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>Сумма</th>
                <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>Позиций</th>
                <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>Статус</th>
                <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>Действия</th>
              </tr>
            </thead>
            <tbody>
              {upds.map(upd => (
                <React.Fragment key={upd.id}>
                  <tr
                    style={{ borderBottom: '1px solid #dee2e6', cursor: 'pointer', backgroundColor: expandedRowId === upd.id ? '#f0f7ff' : 'transparent' }}
                    onClick={() => toggleRow(upd.id)}
                  >
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      {expandedRowId === upd.id ? '▼' : '▶'}
                    </td>
                    <td style={{ padding: '12px' }}>{upd.document_number}</td>
                    <td style={{ padding: '12px' }}>{new Date(upd.document_date).toLocaleDateString('ru')}</td>
                    <td style={{ padding: '12px' }}>{upd.supplier_name}</td>
                    <td style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>
                      {upd.total_with_vat.toLocaleString('ru')} ₽
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>{upd.items_count}</td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '500',
                        backgroundColor: getStatusColor(upd.status) + '20',
                        color: getStatusColor(upd.status)
                      }}>
                        {getStatusText(upd.status)}
                      </span>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }} onClick={e => e.stopPropagation()}>
                      <button
                        onClick={() => openDistributeModal(upd.id)}
                        disabled={upd.status !== 'NEW'}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: upd.status === 'NEW' ? '#3498db' : '#ccc',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: upd.status === 'NEW' ? 'pointer' : 'not-allowed',
                          fontSize: '12px'
                        }}
                      >
                        Распределить
                      </button>
                    </td>
                  </tr>
                  {expandedRowId === upd.id && (
                    <tr style={{ backgroundColor: '#f8f9fa' }}>
                      <td colSpan={8} style={{ padding: '20px' }}>
                        {detailsLoading[upd.id] ? (
                          <div style={{ textAlign: 'center', color: '#666' }}>Загрузка деталей...</div>
                        ) : detailsCache[upd.id]?.items ? (
                          <div style={{
                            backgroundColor: 'white',
                            padding: '16px',
                            borderRadius: '8px',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                          }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#333' }}>Товары и услуги</h4>
                            <table style={{ width: '100%', fontSize: '14px', borderCollapse: 'collapse' }}>
                              <thead>
                                <tr style={{ borderBottom: '1px solid #eee', color: '#666' }}>
                                  <th style={{ textAlign: 'left', padding: '8px' }}>Наименование</th>
                                  <th style={{ textAlign: 'right', padding: '8px', width: '80px' }}>Кол-во</th>
                                  <th style={{ textAlign: 'center', padding: '8px', width: '60px' }}>Ед.</th>
                                  <th style={{ textAlign: 'right', padding: '8px', width: '100px' }}>Цена</th>
                                  <th style={{ textAlign: 'right', padding: '8px', width: '100px' }}>НДС</th>
                                  <th style={{ textAlign: 'right', padding: '8px', width: '120px' }}>Сумма</th>
                                </tr>
                              </thead>
                              <tbody>
                                {detailsCache[upd.id].items.map((item, idx) => (
                                  <tr key={idx} style={{ borderBottom: '1px solid #f5f5f5' }}>
                                    <td style={{ padding: '8px', color: '#333' }}>{item.product_name}</td>
                                    <td style={{ padding: '8px', textAlign: 'right' }}>{item.quantity}</td>
                                    <td style={{ padding: '8px', textAlign: 'center', color: '#666' }}>{item.unit}</td>
                                    <td style={{ padding: '8px', textAlign: 'right' }}>{item.price.toLocaleString('ru')}</td>
                                    <td style={{ padding: '8px', textAlign: 'right', color: '#666' }}>{item.vat_amount.toLocaleString('ru')}</td>
                                    <td style={{ padding: '8px', textAlign: 'right', fontWeight: '500' }}>
                                      {item.total_with_vat.toLocaleString('ru')}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div style={{ textAlign: 'center', color: '#c33' }}>Не удалось загрузить детали</div>
                        )}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {distributeModalOpen && selectedUpdForDistribution && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            width: '500px',
            maxWidth: '90%'
          }}>
            <h2 style={{ marginTop: 0 }}>Распределение УПД</h2>
            <p>Выберите объект для привязки всех затрат из документа:</p>

            <select
              value={selectedObjectId || ''}
              onChange={e => setSelectedObjectId(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '8px',
                marginBottom: '20px',
                borderRadius: '4px',
                border: '1px solid #ddd'
              }}
            >
              <option value="">-- Выберите объект ({objects.length}) --</option>
              {objects.map(obj => (
                <option key={obj.id} value={obj.id}>{obj.name} ({obj.code})</option>
              ))}
            </select>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => setDistributeModalOpen(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#f8f9fa',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Отмена
              </button>
              <button
                onClick={handleDistribute}
                disabled={!selectedObjectId}
                style={{
                  padding: '8px 16px',
                  backgroundColor: selectedObjectId ? '#2ecc71' : '#ccc',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: selectedObjectId ? 'pointer' : 'not-allowed'
                }}
              >
                Подтвердить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
