import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
// import { GlassCard } from '../components/GlassCard'; // Not using GlassCard anymore for main layout based on request
import { PortfolioItem } from '../components/PortfolioItem';
import { ObjectPortfolioItem } from '../types';
import { Calendar, Moon, Sun, ArrowUpRight } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

// MOCK DATA
const MOCK_DATA: ObjectPortfolioItem[] = [
    {
        object_id: 1,
        object_name: "ЖК Зеленый Парк",
        contract_amount: 15000000,
        total_costs: 12500000,
        labor_costs: 3500000,
        material_costs: 6700000,
        equipment_costs: 1800000,
        other_costs: 500000,
    },
    {
        object_id: 2,
        object_name: "Офис Центр Сити",
        contract_amount: 4000000,
        total_costs: 4100000, // Over budget
        labor_costs: 1200000,
        material_costs: 2000000,
        equipment_costs: 400000,
        other_costs: 500000,
    },
    {
        object_id: 3,
        object_name: "Складской Комплекс",
        contract_amount: 25000000,
        total_costs: 8500000,
        labor_costs: 2500000,
        material_costs: 4000000,
        equipment_costs: 1500000,
        other_costs: 500000,
    }
];

export const ManagerPortfolioPage: React.FC = () => {
    const { colors, isDark, toggleTheme } = useTheme();
    const [period, setPeriod] = useState("Февраль 2024");
    const navigate = useNavigate();

    // Calculate totals
    const totalBudget = MOCK_DATA.reduce((acc, i) => acc + (i.contract_amount || 0), 0);
    const totalSpent = MOCK_DATA.reduce((acc, i) => acc + i.total_costs, 0);
    const totalBalance = totalBudget - totalSpent;
    const itemsCount = MOCK_DATA.length;

    // Breakdown
    const totalMat = MOCK_DATA.reduce((acc, i) => acc + (i.material_costs || 0), 0);
    const totalLab = MOCK_DATA.reduce((acc, i) => acc + (i.labor_costs || 0), 0);
    const totalEq = MOCK_DATA.reduce((acc, i) => acc + (i.equipment_costs || 0), 0);
    const totalOther = MOCK_DATA.reduce((acc, i) => acc + (i.other_costs || 0), 0);

    // Chart Data
    const percent = Math.min((totalSpent / totalBudget) * 100, 100);
    const chartData = [{ name: 'Spent', value: percent, fill: totalBalance >= 0 ? colors.success : colors.danger }];

    const handleObjectClick = (id: number) => {
        navigate(`/miniapp/manager/object/${id}`);
    };

    return (
        <div className="p-4 max-w-md mx-auto min-h-screen pb-20">
            {/* Header */}
            <div className="flex justify-between items-center mb-6 pt-2">
                <div className="flex items-center gap-2">
                    <h1 className="text-2xl font-bold tracking-tight" style={{ color: colors.text_primary }}>
                        Портфель
                    </h1>
                    <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-black/5 dark:bg-white/10">
                        <Calendar size={12} style={{ color: colors.text_secondary }} />
                        <span className="text-xs font-medium" style={{ color: colors.text_primary }}>{period}</span>
                    </div>
                </div>

                <button
                    className="p-2 rounded-full backdrop-blur-md transition-colors"
                    style={{ backgroundColor: colors.card_bg, color: colors.text_primary }}
                    onClick={toggleTheme}
                >
                    {isDark ? <Sun size={24} /> : <Moon size={24} />}
                </button>
            </div>

            {/* Total Summary Card - Analytical Style */}
            <div className="mb-8 rounded-[28px] p-6 shadow-xl text-white overflow-hidden relative"
                style={{ backgroundColor: '#1C1C1E' }}>

                <h2 className="text-sm font-medium text-white/60 mb-5 uppercase tracking-wider">Структура расходов</h2>

                <div className="flex items-start justify-between relative z-10">
                    {/* Left: Financials */}
                    <div className="flex-1 mr-4">
                        {/* Main Stats Grid */}
                        <div className="grid grid-cols-2 gap-4 mb-5">
                            <div>
                                <div className="text-[10px] text-white/50 uppercase mb-1">Бюджет</div>
                                <div className="text-lg font-bold leading-none">{(totalBudget / 1000000).toFixed(1)}M</div>
                            </div>
                            <div>
                                <div className="text-[10px] text-white/50 uppercase mb-1">Освоено</div>
                                <div className="text-lg font-bold leading-none">{(totalSpent / 1000000).toFixed(1)}M</div>
                            </div>
                        </div>

                        {/* Balance */}
                        <div className="mb-5">
                            <div className="text-[10px] text-white/50 uppercase mb-1">Остаток</div>
                            <div className="text-2xl font-bold tracking-tight text-[#30D158]">
                                {(totalBalance / 1000000).toFixed(1)}M ₽
                            </div>
                        </div>

                        {/* Legend */}
                        <div className="space-y-1.5 border-t border-white/10 pt-3">
                            <div className="flex items-center justify-between text-xs">
                                <div className="flex items-center">
                                    <div className="w-1.5 h-1.5 rounded-full mr-2" style={{ backgroundColor: '#34C759' }} />
                                    <span className="text-white/70">Материалы</span>
                                </div>
                                <span className="font-medium text-white">{(totalMat / 1000000).toFixed(1)}M</span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                                <div className="flex items-center">
                                    <div className="w-1.5 h-1.5 rounded-full mr-2" style={{ backgroundColor: '#FF9500' }} />
                                    <span className="text-white/70">Техника / Дост.</span>
                                </div>
                                <span className="font-medium text-white">{(totalEq / 1000000).toFixed(1)}M</span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                                <div className="flex items-center">
                                    <div className="w-1.5 h-1.5 rounded-full mr-2" style={{ backgroundColor: '#007AFF' }} />
                                    <span className="text-white/70">Работы</span>
                                </div>
                                <span className="font-medium text-white">{(totalLab / 1000000).toFixed(1)}M</span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                                <div className="flex items-center">
                                    <div className="w-1.5 h-1.5 rounded-full mr-2" style={{ backgroundColor: '#AF52DE' }} />
                                    <span className="text-white/70">Иные</span>
                                </div>
                                <span className="font-medium text-white">{(totalOther / 1000000).toFixed(1)}M</span>
                            </div>
                        </div>
                    </div>

                    {/* Right: Pie Chart */}
                    <div className="w-32 h-32 relative flex-shrink-0 mt-2">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={[
                                        { name: 'Mat', value: totalMat, color: '#34C759' }, // Green
                                        { name: 'Eq', value: totalEq, color: '#FF9500' }, // Orange
                                        { name: 'Lab', value: totalLab, color: '#007AFF' }, // Blue
                                        { name: 'Oth', value: totalOther, color: '#AF52DE' }, // Purple
                                    ]}
                                    innerRadius={45}
                                    outerRadius={60}
                                    paddingAngle={4}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {[
                                        { color: '#34C759' },
                                        { color: '#FF9500' },
                                        { color: '#007AFF' },
                                        { color: '#AF52DE' }
                                    ].map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                            </PieChart>
                        </ResponsiveContainer>
                        {/* Center Text */}
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span className="text-[9px] text-white/40 uppercase">Расход</span>
                            <span className="text-sm font-bold text-white">
                                {(totalSpent / 1000000).toFixed(1)}M
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Objects List */}
            <div className="mb-4">
                <h2 className="text-lg font-semibold mb-4" style={{ color: colors.text_primary }}>
                    Объекты в работе
                </h2>
                <div className="space-y-4">
                    {MOCK_DATA.map(item => (
                        <PortfolioItem
                            key={item.object_id}
                            item={item}
                            onClick={handleObjectClick}
                        />
                    ))}
                </div>
            </div>

            <div className="h-10"></div>
        </div>
    );
};
