import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { CostObject } from '../types';
import { ObjectDetailsModal } from '../components/ObjectDetailsModal';

export function ObjectsPage() {
  const navigate = useNavigate();
  const [objects, setObjects] = useState<CostObject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedObjectId, setSelectedObjectId] = useState<number | null>(null);
  const [newObject, setNewObject] = useState({
    name: '',
    contract_number: '',
    material_amount: '',
    labor_amount: ''
  });

  useEffect(() => {
    loadObjects();
  }, []);

  const loadObjects = async () => {
    try {
      const data = await apiClient.get<CostObject[]>('/objects/');
      setObjects(data);
    } catch (err) {
      console.error('Ошибка загрузки объектов:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateObject = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/objects/', {
        ...newObject,
        material_amount: newObject.material_amount ? parseFloat(newObject.material_amount) : undefined,
        labor_amount: newObject.labor_amount ? parseFloat(newObject.labor_amount) : undefined
      });
      setShowCreateModal(false);
      setNewObject({ name: '', contract_number: '', material_amount: '', labor_amount: '' });
      await loadObjects();
      alert('Объект успешно создан!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка создания объекта');
    }
  };

  if (loading) {
    return <div>Загрузка...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>Объекты учета</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          style={{
            padding: '12px 24px',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Добавить объект
        </button>
      </div>

      <div style={{ display: 'grid', gap: '20px' }}>
        {objects.map(obj => (
          <div
            key={obj.id}
            onClick={() => setSelectedObjectId(obj.id)}
            style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              borderLeft: '4px solid #3498db',
              cursor: 'pointer',
              transition: 'transform 0.2s, box-shadow 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div style={{ flex: 1 }}>
                <h3 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>{obj.name}</h3>
                <div style={{ color: '#7f8c8d', fontSize: '14px', marginBottom: '15px' }}>
                  Код: {obj.code}
                </div>
                {obj.contract_number && (
                  <div style={{ fontSize: '14px', marginBottom: '5px' }}>
                    <span style={{ color: '#7f8c8d' }}>Договор:</span> {obj.contract_number}
                  </div>
                )}
                {obj.material_amount && (
                  <div style={{ fontSize: '14px', marginBottom: '5px' }}>
                    <span style={{ color: '#7f8c8d' }}>Материалы:</span>{' '}
                    <strong>{obj.material_amount.toLocaleString('ru')} ₽</strong>
                  </div>
                )}
                {obj.labor_amount && (
                  <div style={{ fontSize: '14px', marginBottom: '5px' }}>
                    <span style={{ color: '#7f8c8d' }}>Работы:</span>{' '}
                    <strong>{obj.labor_amount.toLocaleString('ru')} ₽</strong>
                  </div>
                )}
                {obj.status && (
                  <div style={{ fontSize: '14px', marginBottom: '5px' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      backgroundColor: obj.status === 'ACTIVE' ? '#27ae60' :
                        obj.status === 'CLOSED' ? '#95a5a6' :
                          obj.status === 'ARCHIVE' ? '#7f8c8d' : '#f39c12',
                      color: 'white'
                    }}>
                      {obj.status === 'ACTIVE' ? 'В работе' :
                        obj.status === 'PREPARATION_TO_CLOSE' ? 'Подготовка к закрытию' :
                          obj.status === 'CLOSED' ? 'Закрыт' :
                            obj.status === 'ARCHIVE' ? 'Архив' : obj.status}
                    </span>
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/objects/${obj.id}`);
                  }}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'transparent',
                    color: '#3498db',
                    border: '1px solid #3498db',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  Полный отчет →
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {objects.length === 0 && (
        <div style={{
          backgroundColor: 'white',
          padding: '40px',
          borderRadius: '8px',
          textAlign: 'center',
          color: '#7f8c8d'
        }}>
          Объекты не найдены. Добавьте первый объект учета.
        </div>
      )}

      {/* Modal с быстрым просмотром */}
      {selectedObjectId && (
        <ObjectDetailsModal
          objectId={selectedObjectId}
          onClose={() => setSelectedObjectId(null)}
          onViewFull={() => {
            setSelectedObjectId(null);
            navigate(`/objects/${selectedObjectId}`);
          }}
        />
      )}

      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '8px',
            width: '90%',
            maxWidth: '500px'
          }}>
            <h2 style={{ marginTop: 0 }}>Создать объект учета</h2>
            <form onSubmit={handleCreateObject}>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Название *</label>
                <input
                  type="text"
                  required
                  value={newObject.name}
                  onChange={(e) => setNewObject({ ...newObject, name: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                />
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '5px' }}>
                  Код объекта будет присвоен автоматически
                </div>
              </div>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Номер договора</label>
                <input
                  type="text"
                  value={newObject.contract_number}
                  onChange={(e) => setNewObject({ ...newObject, contract_number: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                />
              </div>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Сумма материалов (₽)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newObject.material_amount}
                  onChange={(e) => setNewObject({ ...newObject, material_amount: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                  placeholder="Введите сумму материалов"
                />
              </div>
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Сумма работ (₽)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newObject.labor_amount}
                  onChange={(e) => setNewObject({ ...newObject, labor_amount: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                  placeholder="Введите сумму работ"
                />
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '5px' }}>
                  Общая сумма договора рассчитается автоматически
                </div>
              </div>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#95a5a6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#3498db',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  Создать
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
