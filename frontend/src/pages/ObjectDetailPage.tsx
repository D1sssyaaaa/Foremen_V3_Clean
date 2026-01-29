import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';

interface ObjectDetails {
  object: {
    id: number;
    name: string;
    code: string;
    contract_number: string | null;
    contract_amount: number | null;
    material_amount: number | null;
    labor_amount: number | null;
    start_date: string | null;
    end_date: string | null;
    status: string;
    description: string | null;
    is_active: boolean;
  };
  material_requests: Array<{
    id: number;
    number: string | null;
    created_at: string;
    status: string;
    urgency: string;
    supplier: string | null;
    expected_delivery_date: string | null;
  }>;
  equipment_orders: Array<{
    id: number;
    number: string | null;
    created_at: string;
    equipment_type: string;
    status: string;
    supplier: string | null;
    start_date: string | null;
    end_date: string | null;
  }>;
  upd_documents: Array<{
    id: number;
    document_number: string;
    document_date: string;
    supplier_name: string;
    total_amount: number;
  }>;
}

interface ObjectStats {
  total_costs: number;
  budget: {
    total_budget: number;
  };
  material_requests: { total: number };
  equipment_orders: { total: number };
  timesheets: { labor_costs_total: number };
  upd_documents: { total: number };
}

// Детальная информация об УПД (для модального окна)
interface UPDDetail {
  id: number;
  document_number: string;
  document_date: string;
  supplier_name: string;
  supplier_inn: string | null;
  total_amount: number;
  total_vat: number;
  total_with_vat: number;
  items: Array<{
    product_name: string;
    quantity: number;
    unit: string;
    price: number;
    amount: number;
    vat_rate: number;
    vat_amount: number;
    total_with_vat: number;
  }>;
}

type Tab = 'overview' | 'materials' | 'equipment' | 'upd';

export function ObjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [details, setDetails] = useState<ObjectDetails | null>(null);
  const [stats, setStats] = useState<ObjectStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Сначала загружаем детали (основная информация)
      const detailsData = await apiClient.get<ObjectDetails>(`/objects/${id}/details`);
      setDetails(detailsData);

      // Затем пробуем загрузить статистику (может упасть)
      try {
        const statsData = await apiClient.get<ObjectStats>(`/objects/${id}/stats`);
        setStats(statsData);
      } catch (statsErr: any) {
        console.warn('Не удалось загрузить статистику:', statsErr);
        // Устанавливаем дефолтную статистику если не удалось загрузить
        setStats({
          total_costs: 0,
          budget: { total_budget: detailsData.object.contract_amount || 0 },
          material_requests: { total: 0 },
          equipment_orders: { total: 0 },
          timesheets: { labor_costs_total: 0 },
          upd_documents: { total: 0 }
        });
      }
    } catch (err: any) {
      console.error('Ошибка загрузки данных:', err);
      if (err.response?.status === 403) {
        setError('Недостаточно прав для просмотра этого объекта');
      } else if (err.response?.status === 404) {
        setError('Объект не найден');
      } else {
        setError(`Ошибка загрузки: ${err.message || 'Неизвестная ошибка'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Загрузка...</div>;
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ color: '#e74c3c', marginBottom: '20px' }}>{error}</div>
        <button
          onClick={() => navigate('/objects')}
          style={{
            padding: '10px 20px',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Вернуться к списку объектов
        </button>
      </div>
    );
  }

  if (!details || !stats) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Объект не найден</div>;
  }

  const budgetUsage = stats.budget.total_budget > 0
    ? (stats.total_costs / stats.budget.total_budget) * 100
    : 0;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <button
          onClick={() => navigate('/objects')}
          style={{
            padding: '8px 16px',
            backgroundColor: 'transparent',
            border: '1px solid #bdc3c7',
            borderRadius: '6px',
            cursor: 'pointer',
            marginBottom: '16px',
          }}
        >
          ← Назад к списку
        </button>
        <h1 style={{ margin: '0 0 8px 0' }}>{details.object.name}</h1>
        <div style={{ color: '#7f8c8d', fontSize: '14px' }}>
          Код: {details.object.code} | Статус: {getStatusLabel(details.object.status)}
        </div>
      </div>

      {/* Tabs */}
      <div style={tabsContainerStyle}>
        <button
          onClick={() => setActiveTab('overview')}
          style={activeTab === 'overview' ? activeTabStyle : tabStyle}
        >
          📊 Обзор
        </button>
        <button
          onClick={() => setActiveTab('materials')}
          style={activeTab === 'materials' ? activeTabStyle : tabStyle}
        >
          📦 Материалы ({details.material_requests.length})
        </button>
        <button
          onClick={() => setActiveTab('equipment')}
          style={activeTab === 'equipment' ? activeTabStyle : tabStyle}
        >
          🚜 Техника ({details.equipment_orders.length})
        </button>
        <button
          onClick={() => setActiveTab('upd')}
          style={activeTab === 'upd' ? activeTabStyle : tabStyle}
        >
          📄 УПД ({details.upd_documents.length})
        </button>
      </div>

      {/* Tab Content */}
      <div style={contentStyle}>
        {activeTab === 'overview' && (
          <OverviewTab
            details={details.object}
            stats={stats}
            budgetUsage={budgetUsage}
            updDocuments={details.upd_documents}
            onSwitchToUPD={() => setActiveTab('upd')}
          />
        )}
        {activeTab === 'materials' && <MaterialsTab requests={details.material_requests} />}
        {activeTab === 'equipment' && <EquipmentTab orders={details.equipment_orders} />}
        {activeTab === 'upd' && <UPDTab documents={details.upd_documents} />}
      </div>
    </div>
  );
}

// Overview Tab
function OverviewTab({
  details,
  stats,
  budgetUsage,
  updDocuments,
  onSwitchToUPD,
}: {
  details: ObjectDetails['object'];
  stats: ObjectStats;
  budgetUsage: number;
  updDocuments: ObjectDetails['upd_documents'];
  onSwitchToUPD: () => void;
}) {
  const [selectedUPD, setSelectedUPD] = useState<UPDDetail | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loadingUPD, setLoadingUPD] = useState(false);

  const loadUPDDetails = async (updId: number) => {
    setLoadingUPD(true);
    try {
      const response = await apiClient.get<UPDDetail>(`/material-costs/${updId}`);
      setSelectedUPD(response);
      setIsModalOpen(true);
    } catch (err) {
      console.error('Ошибка загрузки деталей УПД:', err);
    } finally {
      setLoadingUPD(false);
    }
  };
  return (
    <div>
      {/* Budget Chart */}
      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>💰 Бюджет и исполнение</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '20px' }}>
          <div>
            <div style={{ color: '#7f8c8d', fontSize: '14px' }}>Общий бюджет</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
              {stats.budget.total_budget.toLocaleString('ru')} ₽
            </div>
          </div>
          <div>
            <div style={{ color: '#7f8c8d', fontSize: '14px' }}>Использовано</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: budgetUsage > 90 ? '#e74c3c' : '#27ae60' }}>
              {stats.total_costs.toLocaleString('ru')} ₽
            </div>
          </div>
          <div>
            <div style={{ color: '#7f8c8d', fontSize: '14px' }}>Остаток</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
              {(stats.budget.total_budget - stats.total_costs).toLocaleString('ru')} ₽
            </div>
          </div>
          <div>
            <div style={{ color: '#7f8c8d', fontSize: '14px' }}>Процент использования</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: budgetUsage > 90 ? '#e74c3c' : budgetUsage > 70 ? '#f39c12' : '#27ae60' }}>
              {budgetUsage.toFixed(1)}%
            </div>
          </div>
        </div>
        <div style={{ backgroundColor: '#ecf0f1', borderRadius: '10px', height: '30px', overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${Math.min(budgetUsage, 100)}%`,
              backgroundColor: budgetUsage > 90 ? '#e74c3c' : budgetUsage > 70 ? '#f39c12' : '#27ae60',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* Works vs Materials Split */}
      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>⚙️ Разделение: Работы / Материалы</h3>
        <WorksMaterialsSplit stats={stats} details={details} />
      </div>

      {/* Costs Breakdown */}
      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>📊 Структура затрат</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <CostBreakdownItem
            label="Материалы"
            value={stats.material_requests.total}
            total={stats.total_costs}
            color="#3498db"
          />
          <CostBreakdownItem
            label="Техника"
            value={stats.equipment_orders.total}
            total={stats.total_costs}
            color="#f39c12"
          />
          <CostBreakdownItem
            label="РТБ"
            value={stats.timesheets.labor_costs_total}
            total={stats.total_costs}
            color="#27ae60"
          />
          <CostBreakdownItem
            label="УПД"
            value={stats.upd_documents.total}
            total={stats.total_costs}
            color="#9b59b6"
          />
        </div>
      </div>

      {/* Object Info */}
      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>ℹ️ Информация об объекте</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tbody>
            {details.contract_number && (
              <tr>
                <td style={tableCellStyle}>Номер договора:</td>
                <td style={{ ...tableCellStyle, fontWeight: 'bold' }}>{details.contract_number}</td>
              </tr>
            )}
            {details.start_date && (
              <tr>
                <td style={tableCellStyle}>Дата начала:</td>
                <td style={{ ...tableCellStyle, fontWeight: 'bold' }}>
                  {new Date(details.start_date).toLocaleDateString('ru')}
                </td>
              </tr>
            )}
            {details.end_date && (
              <tr>
                <td style={tableCellStyle}>Дата окончания:</td>
                <td style={{ ...tableCellStyle, fontWeight: 'bold' }}>
                  {new Date(details.end_date).toLocaleDateString('ru')}
                </td>
              </tr>
            )}
            {details.description && (
              <tr>
                <td style={tableCellStyle}>Описание:</td>
                <td style={{ ...tableCellStyle, fontWeight: 'bold' }}>{details.description}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Мини-таблица УПД */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ margin: 0 }}>📄 Последние УПД</h3>
          {updDocuments.length > 5 && (
            <button
              onClick={onSwitchToUPD}
              style={{
                padding: '6px 12px',
                backgroundColor: 'transparent',
                border: '1px solid #9b59b6',
                borderRadius: '6px',
                color: '#9b59b6',
                cursor: 'pointer',
                fontSize: '13px',
              }}
            >
              Смотреть все →
            </button>
          )}
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8f9fa' }}>
              <th style={{ ...miniTableHeaderStyle, textAlign: 'left' }}>Поставщик</th>
              <th style={{ ...miniTableHeaderStyle, textAlign: 'left' }}>Номер</th>
              <th style={{ ...miniTableHeaderStyle, textAlign: 'center' }}>Дата</th>
              <th style={{ ...miniTableHeaderStyle, textAlign: 'right' }}>Сумма</th>
            </tr>
          </thead>
          <tbody>
            {updDocuments.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ padding: '30px', textAlign: 'center', color: '#7f8c8d', borderBottom: '1px solid #ecf0f1' }}>
                  УПД документов пока нет
                </td>
              </tr>
            ) : (
              updDocuments.slice(0, 5).map((doc) => (
                <tr
                  key={doc.id}
                  onClick={() => loadUPDDetails(doc.id)}
                  style={{
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f8f9fa')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <td style={{ ...miniTableCellStyle, fontWeight: '500' }}>{doc.supplier_name}</td>
                  <td style={{ ...miniTableCellStyle, color: '#9b59b6' }}>{doc.document_number}</td>
                  <td style={{ ...miniTableCellStyle, textAlign: 'center', color: '#7f8c8d' }}>
                    {new Date(doc.document_date).toLocaleDateString('ru')}
                  </td>
                  <td style={{ ...miniTableCellStyle, textAlign: 'right', fontWeight: 'bold', color: '#27ae60' }}>
                    {doc.total_amount.toLocaleString('ru')} ₽
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        {loadingUPD && (
          <div style={{ textAlign: 'center', padding: '10px', color: '#7f8c8d' }}>
            Загрузка...
          </div>
        )}
      </div>

      {/* Модальное окно с деталями УПД */}
      {isModalOpen && selectedUPD && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setIsModalOpen(false)}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              maxWidth: '800px',
              width: '90%',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Заголовок модального окна */}
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid #ecf0f1',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <div>
                <h2 style={{ margin: '0 0 4px 0', fontSize: '18px' }}>
                  📄 УПД №{selectedUPD.document_number}
                </h2>
                <div style={{ color: '#7f8c8d', fontSize: '14px' }}>
                  {new Date(selectedUPD.document_date).toLocaleDateString('ru')} • {selectedUPD.supplier_name}
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                style={{
                  padding: '8px 12px',
                  backgroundColor: 'transparent',
                  border: 'none',
                  fontSize: '20px',
                  cursor: 'pointer',
                  color: '#7f8c8d',
                }}
              >
                ✕
              </button>
            </div>

            {/* Таблица состава УПД */}
            <div style={{ padding: '24px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ ...modalTableHeaderStyle, textAlign: 'left' }}>Наименование</th>
                    <th style={{ ...modalTableHeaderStyle, textAlign: 'center', width: '80px' }}>Кол-во</th>
                    <th style={{ ...modalTableHeaderStyle, textAlign: 'center', width: '60px' }}>Ед.</th>
                    <th style={{ ...modalTableHeaderStyle, textAlign: 'right', width: '100px' }}>Цена</th>
                    <th style={{ ...modalTableHeaderStyle, textAlign: 'right', width: '120px' }}>Сумма</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedUPD.items.map((item, index) => (
                    <tr key={index} style={{ borderBottom: '1px solid #ecf0f1' }}>
                      <td style={{ ...modalTableCellStyle, fontWeight: '500' }}>{item.product_name}</td>
                      <td style={{ ...modalTableCellStyle, textAlign: 'center' }}>{item.quantity}</td>
                      <td style={{ ...modalTableCellStyle, textAlign: 'center', color: '#7f8c8d' }}>{item.unit}</td>
                      <td style={{ ...modalTableCellStyle, textAlign: 'right' }}>{item.price.toLocaleString('ru')} ₽</td>
                      <td style={{ ...modalTableCellStyle, textAlign: 'right', fontWeight: '500' }}>
                        {item.amount.toLocaleString('ru')} ₽
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Итоги */}
              <div style={{
                marginTop: '20px',
                padding: '16px',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>Итого без НДС:</span>
                  <span style={{ fontWeight: '500' }}>{selectedUPD.total_amount.toLocaleString('ru')} ₽</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>НДС:</span>
                  <span style={{ fontWeight: '500' }}>{selectedUPD.total_vat.toLocaleString('ru')} ₽</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', fontWeight: 'bold', color: '#27ae60' }}>
                  <span>Итого с НДС:</span>
                  <span>{selectedUPD.total_with_vat.toLocaleString('ru')} ₽</span>
                </div>
              </div>
            </div>

            {/* Футер модального окна */}
            <div style={{
              padding: '16px 24px',
              borderTop: '1px solid #ecf0f1',
              display: 'flex',
              justifyContent: 'flex-end',
            }}>
              <button
                onClick={() => setIsModalOpen(false)}
                style={{
                  padding: '10px 24px',
                  backgroundColor: '#3498db',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}




// Works/Materials Split Component
function WorksMaterialsSplit({
  stats,
  details
}: {
  stats: ObjectStats;
  details: ObjectDetails['object'];
}) {
  // Работы = Техника + РТБ + (Иные затраты - будет добавлено позже)
  const works = stats.equipment_orders.total + stats.timesheets.labor_costs_total;

  // Материалы = УПД (фактические затраты на материалы)
  const materials = stats.upd_documents.total;

  // Бюджеты
  const worksBudget = (details.labor_amount || 0);
  const materialsBudget = (details.material_amount || 0);

  // Процент использования
  const worksUsage = worksBudget > 0 ? (works / worksBudget) * 100 : 0;
  const materialsUsage = materialsBudget > 0 ? (materials / materialsBudget) * 100 : 0;

  // Расчет по формуле: Работы = (техника + зарплаты) - договор
  const worksWithContract = works - (details.contract_amount || 0);

  return (
    <div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '30px',
        marginBottom: '20px'
      }}>
        {/* Работы */}
        <div style={{
          padding: '20px',
          backgroundColor: '#f8f9fa',
          borderRadius: '12px',
          border: '2px solid #e9ecef'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
            <span style={{ fontSize: '28px' }}>⚙️</span>
            <h4 style={{ margin: 0, color: '#2c3e50' }}>Работы</h4>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <div style={{ color: '#7f8c8d', fontSize: '13px', marginBottom: '5px' }}>Фактические затраты</div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#3498db' }}>
              {works.toLocaleString('ru')} ₽
            </div>
            <div style={{ fontSize: '12px', color: '#95a5a6', marginTop: '5px' }}>
              Техника: {stats.equipment_orders.total.toLocaleString('ru')} ₽<br />
              Зарплаты: {stats.timesheets.labor_costs_total.toLocaleString('ru')} ₽
            </div>
          </div>

          {worksBudget > 0 && (
            <>
              <div style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '5px' }}>
                  <span style={{ color: '#7f8c8d' }}>Бюджет:</span>
                  <span style={{ fontWeight: '600' }}>{worksBudget.toLocaleString('ru')} ₽</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '10px' }}>
                  <span style={{ color: '#7f8c8d' }}>Остаток:</span>
                  <span style={{
                    fontWeight: '600',
                    color: (worksBudget - works) >= 0 ? '#27ae60' : '#e74c3c'
                  }}>
                    {(worksBudget - works).toLocaleString('ru')} ₽
                  </span>
                </div>
              </div>

              <div style={{ backgroundColor: '#ecf0f1', borderRadius: '8px', height: '20px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${Math.min(worksUsage, 100)}%`,
                  backgroundColor: worksUsage > 90 ? '#e74c3c' : worksUsage > 70 ? '#f39c12' : '#27ae60',
                  transition: 'width 0.3s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  color: 'white'
                }}>
                  {worksUsage > 15 && `${worksUsage.toFixed(1)}%`}
                </div>
              </div>
            </>
          )}

          {details.contract_amount && details.contract_amount > 0 && (
            <div style={{
              marginTop: '15px',
              padding: '10px',
              backgroundColor: worksWithContract < 0 ? '#d4edda' : '#f8d7da',
              borderRadius: '8px',
              fontSize: '12px'
            }}>
              <strong>Расчёт:</strong> ({works.toLocaleString('ru')}) - {(details.contract_amount || 0).toLocaleString('ru')} = {' '}
              <span style={{
                fontWeight: 'bold',
                color: worksWithContract < 0 ? '#155724' : '#721c24'
              }}>
                {worksWithContract.toLocaleString('ru')} ₽
              </span>
            </div>
          )}
        </div>

        {/* Материалы */}
        <div style={{
          padding: '20px',
          backgroundColor: '#f8f9fa',
          borderRadius: '12px',
          border: '2px solid #e9ecef'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
            <span style={{ fontSize: '28px' }}>📦</span>
            <h4 style={{ margin: 0, color: '#2c3e50' }}>Материалы</h4>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <div style={{ color: '#7f8c8d', fontSize: '13px', marginBottom: '5px' }}>Фактические затраты (УПД)</div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#9b59b6' }}>
              {materials.toLocaleString('ru')} ₽
            </div>
            <div style={{ fontSize: '12px', color: '#95a5a6', marginTop: '5px' }}>
              Документов: {stats.upd_documents.total}
            </div>
          </div>

          {materialsBudget > 0 && (
            <>
              <div style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '5px' }}>
                  <span style={{ color: '#7f8c8d' }}>Бюджет:</span>
                  <span style={{ fontWeight: '600' }}>{materialsBudget.toLocaleString('ru')} ₽</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '10px' }}>
                  <span style={{ color: '#7f8c8d' }}>Остаток:</span>
                  <span style={{
                    fontWeight: '600',
                    color: (materialsBudget - materials) >= 0 ? '#27ae60' : '#e74c3c'
                  }}>
                    {(materialsBudget - materials).toLocaleString('ru')} ₽
                  </span>
                </div>
              </div>

              <div style={{ backgroundColor: '#ecf0f1', borderRadius: '8px', height: '20px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${Math.min(materialsUsage, 100)}%`,
                  backgroundColor: materialsUsage > 90 ? '#e74c3c' : materialsUsage > 70 ? '#f39c12' : '#27ae60',
                  transition: 'width 0.3s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  color: 'white'
                }}>
                  {materialsUsage > 15 && `${materialsUsage.toFixed(1)}%`}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Visual Pie-like Bars */}
      <div style={{
        display: 'flex',
        height: '60px',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        {works > 0 && (
          <div style={{
            flex: works,
            backgroundColor: '#3498db',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '14px',
            transition: 'flex 0.3s ease'
          }}>
            ⚙️ {((works / (works + materials)) * 100).toFixed(0)}%
          </div>
        )}
        {materials > 0 && (
          <div style={{
            flex: materials,
            backgroundColor: '#9b59b6',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '14px',
            transition: 'flex 0.3s ease'
          }}>
            📦 {((materials / (works + materials)) * 100).toFixed(0)}%
          </div>
        )}
      </div>
    </div>
  );
}

function CostBreakdownItem({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const percentage = total > 0 ? (value / total) * 100 : 0;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontWeight: '500' }}>{label}</span>
        <span style={{ fontWeight: 'bold' }}>
          {value.toLocaleString('ru')} ₽ ({percentage.toFixed(1)}%)
        </span>
      </div>
      <div style={{ backgroundColor: '#ecf0f1', borderRadius: '8px', height: '24px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${percentage}%`, backgroundColor: color, transition: 'width 0.3s ease' }} />
      </div>
    </div>
  );
}

// Materials Tab
function MaterialsTab({ requests }: { requests: ObjectDetails['material_requests'] }) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div style={cardStyle}>
      <h3 style={{ marginTop: 0 }}>📦 Заявки на материалы</h3>
      {requests.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>Заявок нет</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {requests.map((req) => (
            <div key={req.id} style={{
              border: '1px solid #ecf0f1',
              borderRadius: '8px',
              overflow: 'hidden',
              borderLeft: `4px solid ${getStatusColor(req.status)}`
            }}>
              <div
                onClick={() => toggleExpand(req.id)}
                style={{
                  padding: '15px',
                  cursor: 'pointer',
                  backgroundColor: expandedId === req.id ? '#f8f9fa' : 'white',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                  <span style={{ fontWeight: 'bold', color: '#2c3e50' }}>
                    #{req.id} {req.number && `(${req.number})`}
                  </span>
                  <span style={getStatusBadgeStyle(req.status)}>{getStatusLabel(req.status)}</span>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '8px',
                    fontSize: '11px',
                    backgroundColor: getUrgencyColor(req.urgency) + '20',
                    color: getUrgencyColor(req.urgency)
                  }}>
                    {getUrgencyLabel(req.urgency)}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                  <span style={{ color: '#7f8c8d', fontSize: '13px' }}>
                    {new Date(req.created_at).toLocaleDateString('ru')}
                  </span>
                  <span style={{ fontSize: '18px', color: '#7f8c8d' }}>
                    {expandedId === req.id ? '▲' : '▼'}
                  </span>
                </div>
              </div>
              {expandedId === req.id && (
                <div style={{ padding: '15px', borderTop: '1px solid #ecf0f1', backgroundColor: '#fafafa' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '15px' }}>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Поставщик</div>
                      <div style={{ fontWeight: '500' }}>{req.supplier || '—'}</div>
                    </div>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Ожидаемая поставка</div>
                      <div style={{ fontWeight: '500' }}>
                        {req.expected_delivery_date ? new Date(req.expected_delivery_date).toLocaleDateString('ru') : '—'}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Дата создания</div>
                      <div style={{ fontWeight: '500' }}>{new Date(req.created_at).toLocaleString('ru')}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <a
                      href={`/material-requests?id=${req.id}`}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#3498db',
                        color: 'white',
                        borderRadius: '6px',
                        textDecoration: 'none',
                        fontSize: '13px'
                      }}
                    >
                      Открыть заявку
                    </a>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Equipment Tab
function EquipmentTab({ orders }: { orders: ObjectDetails['equipment_orders'] }) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  // Словарь типов техники (перевод на русский)
  const equipmentTypeLabels: Record<string, string> = {
    'excavator': 'Экскаватор',
    'crane': 'Кран',
    'loader': 'Погрузчик',
    'bulldozer': 'Бульдозер',
    'concrete_mixer': 'Бетономешалка',
    'truck': 'Грузовик',
    'forklift': 'Вилочный погрузчик',
    'generator': 'Генератор',
    'compressor': 'Компрессор',
    'scaffolding': 'Леса строительные',
    'welding': 'Сварочное оборудование',
    'other': 'Прочее',
  };

  const getEquipmentTypeLabel = (type: string) => {
    return equipmentTypeLabels[type] || type;
  };

  return (
    <div style={cardStyle}>
      <h3 style={{ marginTop: 0 }}>🚜 Заявки на технику</h3>
      {orders.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>Заявок нет</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {orders.map((order) => (
            <div key={order.id} style={{
              border: '1px solid #ecf0f1',
              borderRadius: '8px',
              overflow: 'hidden',
              borderLeft: `4px solid ${getStatusColor(order.status)}`
            }}>
              <div
                onClick={() => toggleExpand(order.id)}
                style={{
                  padding: '15px',
                  cursor: 'pointer',
                  backgroundColor: expandedId === order.id ? '#f8f9fa' : 'white',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                  <span style={{ fontWeight: 'bold', color: '#2c3e50' }}>
                    #{order.id} {order.number && `(${order.number})`}
                  </span>
                  <span style={{ fontWeight: '500', color: '#f39c12' }}>
                    {getEquipmentTypeLabel(order.equipment_type)}
                  </span>
                  <span style={getStatusBadgeStyle(order.status)}>{getStatusLabel(order.status)}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                  <span style={{ color: '#7f8c8d', fontSize: '13px' }}>
                    {new Date(order.created_at).toLocaleDateString('ru')}
                  </span>
                  <span style={{ fontSize: '18px', color: '#7f8c8d' }}>
                    {expandedId === order.id ? '▲' : '▼'}
                  </span>
                </div>
              </div>
              {expandedId === order.id && (
                <div style={{ padding: '15px', borderTop: '1px solid #ecf0f1', backgroundColor: '#fafafa' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '15px' }}>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Тип техники</div>
                      <div style={{ fontWeight: '500' }}>{getEquipmentTypeLabel(order.equipment_type)}</div>
                    </div>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Поставщик</div>
                      <div style={{ fontWeight: '500' }}>{order.supplier || '—'}</div>
                    </div>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Период аренды</div>
                      <div style={{ fontWeight: '500' }}>
                        {order.start_date && order.end_date
                          ? `${new Date(order.start_date).toLocaleDateString('ru')} - ${new Date(order.end_date).toLocaleDateString('ru')}`
                          : '—'}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Дата создания</div>
                      <div style={{ fontWeight: '500' }}>{new Date(order.created_at).toLocaleString('ru')}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <a
                      href={`/equipment-orders?id=${order.id}`}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#f39c12',
                        color: 'white',
                        borderRadius: '6px',
                        textDecoration: 'none',
                        fontSize: '13px'
                      }}
                    >
                      Открыть заявку
                    </a>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// UPD Tab
function UPDTab({ documents }: { documents: ObjectDetails['upd_documents'] }) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div style={cardStyle}>
      <h3 style={{ marginTop: 0 }}>📄 УПД документы</h3>
      {documents.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>Документов нет</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {documents.map((doc) => (
            <div key={doc.id} style={{
              border: '1px solid #ecf0f1',
              borderRadius: '8px',
              overflow: 'hidden',
              borderLeft: '4px solid #9b59b6'
            }}>
              <div
                onClick={() => toggleExpand(doc.id)}
                style={{
                  padding: '15px',
                  cursor: 'pointer',
                  backgroundColor: expandedId === doc.id ? '#f8f9fa' : 'white',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                  <span style={{ fontWeight: 'bold', color: '#2c3e50' }}>
                    #{doc.id}
                  </span>
                  <span style={{ fontWeight: '500', color: '#9b59b6' }}>
                    {doc.document_number}
                  </span>
                  <span style={{ color: '#7f8c8d', fontSize: '13px' }}>
                    {doc.supplier_name}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                  <span style={{ fontWeight: 'bold', color: '#27ae60' }}>
                    {doc.total_amount.toLocaleString('ru')} ₽
                  </span>
                  <span style={{ fontSize: '18px', color: '#7f8c8d' }}>
                    {expandedId === doc.id ? '▲' : '▼'}
                  </span>
                </div>
              </div>
              {expandedId === doc.id && (
                <div style={{ padding: '15px', borderTop: '1px solid #ecf0f1', backgroundColor: '#fafafa' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '15px' }}>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Номер документа</div>
                      <div style={{ fontWeight: '500' }}>{doc.document_number}</div>
                    </div>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Дата документа</div>
                      <div style={{ fontWeight: '500' }}>{new Date(doc.document_date).toLocaleDateString('ru')}</div>
                    </div>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Поставщик</div>
                      <div style={{ fontWeight: '500' }}>{doc.supplier_name}</div>
                    </div>
                    <div>
                      <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>Сумма</div>
                      <div style={{ fontWeight: 'bold', color: '#27ae60' }}>{doc.total_amount.toLocaleString('ru')} ₽</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <a
                      href={`/upd?id=${doc.id}`}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#9b59b6',
                        color: 'white',
                        borderRadius: '6px',
                        textDecoration: 'none',
                        fontSize: '13px'
                      }}
                    >
                      Открыть документ
                    </a>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Helper functions
function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    NEW: 'Новая',
    APPROVED: 'Утверждена',
    PENDING_APPROVAL: 'На согласовании',
    IN_PROGRESS: 'В работе',
    IN_PROCESSING: 'В обработке',
    ORDERED: 'Заказано',
    PARTIALLY_DELIVERED: 'Частично поставлено',
    DELIVERED: 'Поставлено',
    COMPLETED: 'Выполнена',
    CANCELLED: 'Отменена',
    CANCEL_REQUESTED: 'Запрос отмены',
    ACTIVE: 'Активный',
    CLOSED: 'Закрыт',
  };
  return labels[status] || status;
}

function getUrgencyLabel(urgency: string): string {
  const labels: Record<string, string> = {
    low: 'Низкая',
    LOW: 'Низкая',
    normal: 'Обычная',
    NORMAL: 'Обычная',
    high: 'Высокая',
    HIGH: 'Высокая',
    urgent: 'Срочная',
    URGENT: 'Срочная',
    critical: 'Критичная',
    CRITICAL: 'Критичная',
  };
  return labels[urgency] || urgency;
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    NEW: '#3498db',
    APPROVED: '#2ecc71',
    PENDING_APPROVAL: '#f39c12',
    IN_PROGRESS: '#f39c12',
    IN_PROCESSING: '#9b59b6',
    ORDERED: '#1abc9c',
    PARTIALLY_DELIVERED: '#16a085',
    DELIVERED: '#27ae60',
    COMPLETED: '#27ae60',
    CANCELLED: '#95a5a6',
    CANCEL_REQUESTED: '#e67e22',
    ACTIVE: '#27ae60',
    CLOSED: '#7f8c8d',
  };
  return colors[status] || '#95a5a6';
}

function getUrgencyColor(urgency: string): string {
  const colors: Record<string, string> = {
    low: '#95a5a6',
    LOW: '#95a5a6',
    normal: '#3498db',
    NORMAL: '#3498db',
    high: '#f39c12',
    HIGH: '#f39c12',
    urgent: '#e74c3c',
    URGENT: '#e74c3c',
    critical: '#c0392b',
    CRITICAL: '#c0392b',
  };
  return colors[urgency] || '#95a5a6';
}

function getStatusBadgeStyle(status: string): React.CSSProperties {
  const colors: Record<string, { bg: string; text: string }> = {
    NEW: { bg: '#e3f2fd', text: '#1976d2' },
    APPROVED: { bg: '#e8f5e9', text: '#388e3c' },
    PENDING_APPROVAL: { bg: '#fff3e0', text: '#f57c00' },
    IN_PROGRESS: { bg: '#fff3e0', text: '#f57c00' },
    IN_PROCESSING: { bg: '#fff3e0', text: '#f57c00' },
    ORDERED: { bg: '#e0f2f1', text: '#00796b' },
    PARTIALLY_DELIVERED: { bg: '#e0f2f1', text: '#00897b' },
    DELIVERED: { bg: '#e8f5e9', text: '#388e3c' },
    COMPLETED: { bg: '#e8f5e9', text: '#388e3c' },
    CANCELLED: { bg: '#eceff1', text: '#546e7a' },
    CANCEL_REQUESTED: { bg: '#fff3e0', text: '#e65100' },
    ACTIVE: { bg: '#e8f5e9', text: '#388e3c' },
    CLOSED: { bg: '#eceff1', text: '#546e7a' },
  };
  const color = colors[status] || { bg: '#ecf0f1', text: '#7f8c8d' };

  return {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '500',
    backgroundColor: color.bg,
    color: color.text,
    display: 'inline-block',
  };
}

// Styles
const tabsContainerStyle: React.CSSProperties = {
  display: 'flex',
  gap: '8px',
  borderBottom: '2px solid #ecf0f1',
  marginBottom: '24px',
};

const tabStyle: React.CSSProperties = {
  padding: '12px 24px',
  backgroundColor: 'transparent',
  border: 'none',
  borderBottom: '2px solid transparent',
  cursor: 'pointer',
  fontSize: '14px',
  fontWeight: '500',
  color: '#7f8c8d',
  marginBottom: '-2px',
};

const activeTabStyle: React.CSSProperties = {
  ...tabStyle,
  color: '#3498db',
  borderBottom: '2px solid #3498db',
};

const contentStyle: React.CSSProperties = {
  minHeight: '400px',
};

const cardStyle: React.CSSProperties = {
  backgroundColor: 'white',
  padding: '24px',
  borderRadius: '8px',
  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  marginBottom: '20px',
};

const tableCellStyle: React.CSSProperties = {
  padding: '12px',
};

// Стили для мини-таблицы УПД
const miniTableHeaderStyle: React.CSSProperties = {
  padding: '10px 12px',
  fontSize: '13px',
  fontWeight: '600',
  color: '#7f8c8d',
  borderBottom: '2px solid #ecf0f1',
};

const miniTableCellStyle: React.CSSProperties = {
  padding: '12px',
  fontSize: '14px',
  borderBottom: '1px solid #ecf0f1',
};

// Стили для модального окна УПД
const modalTableHeaderStyle: React.CSSProperties = {
  padding: '12px 16px',
  fontSize: '13px',
  fontWeight: '600',
  color: '#7f8c8d',
  borderBottom: '2px solid #ecf0f1',
};

const modalTableCellStyle: React.CSSProperties = {
  padding: '12px 16px',
  fontSize: '14px',
};
