import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { ObjectCostSummary } from '../types';

export function ManagerDashboardPage() {
    const [data, setData] = useState<ObjectCostSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState<number | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            // Get period from start of year to today by default
            const endDate = new Date().toISOString().split('T')[0];
            const startDate = new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0];

            const response = await apiClient.get<{ objects_summary: ObjectCostSummary[] }>(
                `/analytics/summary?period_start=${startDate}&period_end=${endDate}`
            );
            setData(response.objects_summary);
        } catch (err) {
            console.error('Ошибка загрузки данных:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatMoney = (amount: number | null) => {
        if (amount === null || amount === undefined) return '-';
        return amount.toLocaleString('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            maximumFractionDigits: 0
        });
    };

    const formatPercent = (val: number) => {
        return val.toFixed(1) + '%';
    };

    const calculateProfit = (plan: number | null, fact: number) => {
        if (plan === null) return null;
        return plan - fact;
    };

    const calculateProfitPercent = (plan: number | null, fact: number) => {
        if (!plan) return 0;
        const profit = plan - fact;
        return (profit / plan) * 100;
    };

    if (loading) {
        return <div style={{ padding: '20px', textAlign: 'center' }}>Загрузка данных...</div>;
    }

    return (
        <div style={{ padding: '16px', maxWidth: '800px', margin: '0 auto' }}>
            <h1 style={{
                fontSize: '24px',
                marginBottom: '20px',
                color: '#1a1a1a',
                fontWeight: 'bold'
            }}>
                Сводная таблица объектов
            </h1>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {data.map(item => {
                    const isExpanded = expandedId === item.object_id;

                    // Calculations
                    const planLabor = item.planned_labor_cost || 0;
                    const factLabor = item.total_labor_cost;
                    const profitLabor = calculateProfit(planLabor, factLabor) || 0;
                    const profitLaborPct = calculateProfitPercent(planLabor, factLabor);

                    const planMaterial = item.planned_material_cost || 0;
                    const factMaterial = item.total_material_cost;
                    const profitMaterial = calculateProfit(planMaterial, factMaterial) || 0;
                    const profitMaterialPct = calculateProfitPercent(planMaterial, factMaterial);

                    return (
                        <div
                            key={item.object_id}
                            style={{
                                backgroundColor: 'white',
                                borderRadius: '16px',
                                padding: '16px',
                                boxShadow: '0 4px 20px rgba(0,0,0,0.05)',
                                cursor: 'pointer',
                                transition: 'transform 0.2s',
                            }}
                            onClick={() => setExpandedId(isExpanded ? null : item.object_id)}
                        >
                            {/* Card Header */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                <div>
                                    <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#2c3e50' }}>
                                        {item.object_name}
                                    </h3>
                                    <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '4px' }}>
                                        Договор: {formatMoney(item.contract_amount)}
                                    </div>
                                </div>
                                <div style={{
                                    backgroundColor: '#e8f5e9',
                                    color: '#2ecc71',
                                    padding: '4px 8px',
                                    borderRadius: '8px',
                                    fontSize: '12px',
                                    fontWeight: '600'
                                }}>
                                    В работе
                                </div>
                            </div>

                            {/* Main KPI Row */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: isExpanded ? '16px' : '0' }}>
                                <div style={{ backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '12px' }}>
                                    <div style={{ fontSize: '11px', color: '#7f8c8d', marginBottom: '4px' }}>Фактические затраты</div>
                                    <div style={{ fontSize: '16px', fontWeight: '600', color: '#e74c3c' }}>
                                        {formatMoney(item.total_cost)}
                                    </div>
                                </div>
                                <div style={{ backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '12px' }}>
                                    <div style={{ fontSize: '11px', color: '#7f8c8d', marginBottom: '4px' }}>Остаток бюджета</div>
                                    <div style={{ fontSize: '16px', fontWeight: '600', color: (item.remaining_budget || 0) >= 0 ? '#2ecc71' : '#e74c3c' }}>
                                        {formatMoney(item.remaining_budget)}
                                    </div>
                                </div>
                            </div>

                            {/* Expanded Details */}
                            {isExpanded && (
                                <div style={{ borderTop: '1px solid #eee', paddingTop: '16px' }}>

                                    {/* Labor Section */}
                                    <div style={{ marginBottom: '16px' }}>
                                        <div style={{ fontSize: '14px', fontWeight: '600', color: '#34495e', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            👷 Работа (ФОТ)
                                            <span style={{
                                                fontSize: '11px',
                                                padding: '2px 6px',
                                                borderRadius: '4px',
                                                backgroundColor: profitLaborPct >= 0 ? '#e8f5e9' : '#ffebee',
                                                color: profitLaborPct >= 0 ? '#2ecc71' : '#e74c3c'
                                            }}>
                                                {formatPercent(profitLaborPct)}
                                            </span>
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', fontSize: '12px' }}>
                                            <div>
                                                <div style={{ color: '#95a5a6' }}>План</div>
                                                <div style={{ fontWeight: '500' }}>{formatMoney(planLabor)}</div>
                                            </div>
                                            <div>
                                                <div style={{ color: '#95a5a6' }}>Факт</div>
                                                <div style={{ fontWeight: '500' }}>{formatMoney(factLabor)}</div>
                                            </div>
                                            <div>
                                                <div style={{ color: '#95a5a6' }}>Разница</div>
                                                <div style={{ fontWeight: '600', color: profitLabor >= 0 ? '#2ecc71' : '#e74c3c' }}>
                                                    {formatMoney(profitLabor)}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Material Section */}
                                    <div style={{ marginBottom: '16px' }}>
                                        <div style={{ fontSize: '14px', fontWeight: '600', color: '#34495e', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            🧱 Материалы
                                            <span style={{
                                                fontSize: '11px',
                                                padding: '2px 6px',
                                                borderRadius: '4px',
                                                backgroundColor: profitMaterialPct >= 0 ? '#e8f5e9' : '#ffebee',
                                                color: profitMaterialPct >= 0 ? '#2ecc71' : '#e74c3c'
                                            }}>
                                                {formatPercent(profitMaterialPct)}
                                            </span>
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', fontSize: '12px' }}>
                                            <div>
                                                <div style={{ color: '#95a5a6' }}>План</div>
                                                <div style={{ fontWeight: '500' }}>{formatMoney(planMaterial)}</div>
                                            </div>
                                            <div>
                                                <div style={{ color: '#95a5a6' }}>Факт</div>
                                                <div style={{ fontWeight: '500' }}>{formatMoney(factMaterial)}</div>
                                            </div>
                                            <div>
                                                <div style={{ color: '#95a5a6' }}>Разница</div>
                                                <div style={{ fontWeight: '600', color: profitMaterial >= 0 ? '#2ecc71' : '#e74c3c' }}>
                                                    {formatMoney(profitMaterial)}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Equipment Section (Fact Only) */}
                                    <div>
                                        <div style={{ fontSize: '14px', fontWeight: '600', color: '#34495e', marginBottom: '8px' }}>
                                            🚜 Техника
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', fontSize: '12px' }}>
                                            <div>
                                                <div style={{ color: '#95a5a6' }}>План</div>
                                                <div style={{ fontWeight: '500' }}>-</div>
                                            </div>
                                            <div>
                                                <div style={{ color: '#95a5a6' }}>Факт</div>
                                                <div style={{ fontWeight: '500' }}>{formatMoney(item.total_equipment_cost)}</div>
                                            </div>
                                            <div>
                                                {/* Empty third column */}
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
