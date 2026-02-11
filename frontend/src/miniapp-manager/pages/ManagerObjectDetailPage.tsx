import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTheme, ThemeProvider } from '../context/ThemeContext';
import { ChevronLeft, FileText, Download, Moon, Sun, X, ArrowRight } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, Tooltip, LabelList } from 'recharts';

// MOCK DATA GENERATOR
const getObjectData = (id: number) => ({
    id,
    name: id === 1 ? "ЖК Зеленый Парк" : "Офис Центр Сити",
    budget: 15000000,
    spent: 12500000,
    balance: 2500000,
    progress: 83,
    // Pie Chart Data (4 Categories)
    structure: [
        { name: 'Материалы', value: 6700000, color: '#34C759' }, // Green
        { name: 'Техника / Дост.', value: 1800000, color: '#FF9500' }, // Orange
        { name: 'Работы', value: 3500000, color: '#007AFF' },    // Blue
        { name: 'Иные', value: 500000, color: '#AF52DE' },       // Purple
    ],
    // Bar Chart Data (Last 6 months)
    dynamics: [
        { month: 'Сен', plan: 2000000, fact: 1800000 },
        { month: 'Окт', plan: 2500000, fact: 2400000 },
        { month: 'Ноя', plan: 2500000, fact: 2900000 }, // Over
        { month: 'Дек', plan: 1500000, fact: 1500000 },
        { month: 'Янв', plan: 1000000, fact: 800000 },
        { month: 'Фев', plan: 2000000, fact: 3100000 }, // Current
    ],
    transactions: [
        { id: 101, type: 'material', description: "Закупка арматуры А500С", amount: -450000, date: "10.02.2024", contragent: "ООО 'Металл-Групп'" },
        { id: 102, type: 'work', brigade: "Монолитчики (Иванов А.)", period: "01.02 - 15.02", amount: -200000, description: "Оплата по табелю" },
        { id: 103, type: 'mechanism', description: "Аренда автокрана 25т", amount: -150000, date: "08.02.2024", contragent: "ИП Иванов В.В." },
    ]
});

const ManagerObjectDetailContent: React.FC = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { colors, isDark, toggleTheme } = useTheme();

    // Fallback to ID 1 if not parsed
    const data = getObjectData(Number(id) || 1);

    const [selectedTx, setSelectedTx] = React.useState<any>(null);

    return (
        <div className="min-h-screen pb-20 p-4 transition-colors duration-300 relative" style={{ backgroundColor: colors.bg_primary, color: colors.text_primary }}>
            {/* Header */}
            <div className="flex items-center justify-between mb-6 pt-2">
                <button
                    onClick={() => navigate(-1)}
                    className="p-2 rounded-full backdrop-blur-md transition-colors"
                    style={{ backgroundColor: colors.card_bg, color: colors.text_primary }}
                >
                    <ChevronLeft size={24} />
                </button>
                <h1 className="text-lg font-bold truncate max-w-[200px]" style={{ color: colors.text_primary }}>
                    {data.name}
                </h1>
                <div className="flex gap-2">
                    <button
                        className="p-2 rounded-full backdrop-blur-md transition-colors"
                        style={{ backgroundColor: colors.card_bg, color: colors.text_primary }}
                        onClick={toggleTheme}
                    >
                        {isDark ? <Sun size={24} /> : <Moon size={24} />}
                    </button>
                    <button
                        className="p-2 rounded-full backdrop-blur-md transition-colors"
                        style={{ backgroundColor: colors.card_bg, color: colors.chart_primary }}
                        onClick={() => alert("Скачивание PDF отчета...")}
                    >
                        <Download size={24} />
                    </button>
                </div>
            </div>

            {/* Main Stats with Visual Budget - ALWAYS DARK CARD for High Contrast */}
            <div className="mb-6 rounded-[20px] p-4 shadow-lg text-white transition-all" style={{ backgroundColor: '#2C2C2E' }}>
                <div className="flex justify-between items-end mb-4">
                    <div>
                        <div className="text-sm mb-1 opacity-70 text-white">Освоено бюджета</div>
                        <div className="text-3xl font-bold tracking-tight text-white">
                            {data.progress}%
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-xs mb-1 opacity-70 text-white">Остаток</div>
                        <div className="text-lg font-semibold text-[#30D158]">
                            {data.balance.toLocaleString()} ₽
                        </div>
                    </div>
                </div>
                {/* Progress Bar */}
                <div className="w-full h-3 rounded-full overflow-hidden bg-white/10">
                    <div
                        className="h-full rounded-full transition-all duration-1000"
                        style={{ width: `${data.progress}%`, backgroundColor: data.progress > 90 ? '#FF453A' : '#30D158' }}
                    />
                </div>
            </div>

            {/* Estimate & Control Link */}
            <button
                onClick={() => navigate(`/miniapp/manager/object/${id}/estimate`)}
                className="w-full mb-6 p-4 rounded-[20px] shadow-lg flex items-center justify-between transition-all active:scale-95"
                style={{ backgroundColor: '#2C2C2E', color: 'white' }}
            >
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-full" style={{ backgroundColor: 'rgba(48, 209, 88, 0.2)', color: '#30D158' }}>
                        <FileText size={20} />
                    </div>
                    <div>
                        <div className="font-semibold text-base">Смета и Лимиты</div>
                        <div className="text-xs text-white/50">Контроль расхода материалов</div>
                    </div>
                </div>
                <ArrowRight size={20} className="text-white/30" />
            </button>


            {/* Cost Structure (Pie Chart) - Adaptive Text */}
            <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3" style={{ color: colors.text_primary }}>Структура расходов</h3>
                <div className="flex items-center space-x-4">
                    {/* Chart */}
                    <div className="relative w-40 h-40 flex-shrink-0">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={data.structure}
                                    innerRadius={60}
                                    outerRadius={75}
                                    paddingAngle={4}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {data.structure.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                            </PieChart>
                        </ResponsiveContainer>
                        {/* Center Text */}
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span className="text-[10px] opacity-70" style={{ color: colors.text_secondary }}>Всего</span>
                            <span className="font-bold text-sm" style={{ color: colors.text_primary }}>
                                {(data.budget / 1000000).toFixed(1)}M
                            </span>
                        </div>
                    </div>
                    {/* Legend */}
                    <div className="flex-1 space-y-3">
                        {data.structure.map((item, idx) => (
                            <div key={idx} className="flex justify-between items-center text-sm">
                                <div className="flex items-center">
                                    <div className="w-2.5 h-2.5 rounded-full mr-2.5" style={{ backgroundColor: item.color }} />
                                    <span className="font-medium text-xs" style={{ color: colors.text_secondary }}>{item.name}</span>
                                </div>
                                <span className="font-bold text-xs" style={{ color: colors.text_primary }}>
                                    {(item.value / 1000000).toFixed(1)}M
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Dynamics (Bar Chart) - Adaptive Text & Gradient */}
            <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3" style={{ color: colors.text_primary }}>Динамика (Факт)</h3>
                <div className="h-52 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data.dynamics} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorFact" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={colors.chart_primary} stopOpacity={0.8} />
                                    <stop offset="95%" stopColor={colors.chart_primary} stopOpacity={0.3} />
                                </linearGradient>
                            </defs>
                            <XAxis
                                dataKey="month"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: colors.text_secondary, fontSize: 11, fontWeight: 500 }}
                                dy={10}
                            />

                            <Bar
                                dataKey="fact"
                                radius={[6, 6, 6, 6]}
                                fill="url(#colorFact)"
                                barSize={32}
                            >
                                <LabelList
                                    dataKey="fact"
                                    position="top"
                                    formatter={(val: any) => (val / 1000000).toFixed(1) + 'M'}
                                    style={{ fill: colors.text_secondary, fontSize: 10, fontWeight: 600 }}
                                    offset={5}
                                />
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Recent Transactions - System Aligned */}
            <div className="mb-8">
                <h3 className="text-lg font-semibold mb-3" style={{ color: colors.text_primary }}>Последние операции</h3>
                <div className="space-y-3">
                    {data.transactions.map((tx: any) => {
                        // Icon & Color Mapping based on System Types
                        let Icon = FileText;
                        let iconBg = 'bg-white/10';
                        let iconColor = 'text-white/70';

                        // Content Variables
                        let mainText = '';
                        let subText = '';

                        switch (tx.type) {
                            case 'material':
                                Icon = FileText;
                                iconBg = 'bg-green-500/20';
                                iconColor = 'text-green-400';
                                mainText = tx.supplier;
                                subText = `${tx.number} от ${tx.date}`;
                                break;
                            case 'work':
                                Icon = FileText;
                                iconBg = 'bg-blue-500/20';
                                iconColor = 'text-blue-400';
                                mainText = `Табель (РТБ): ${tx.brigade}`;
                                subText = `Период: ${tx.period}`;
                                break;
                            case 'mechanism':
                                Icon = FileText;
                                iconBg = 'bg-orange-500/20';
                                iconColor = 'text-orange-400';
                                mainText = tx.name;
                                subText = `${tx.supplier} • ${tx.date}`;
                                break;
                            case 'other':
                                Icon = FileText;
                                iconBg = 'bg-purple-500/20';
                                iconColor = 'text-purple-400';
                                mainText = tx.name;
                                subText = tx.date;
                                break;
                            default:
                                mainText = 'Неизвестная операция';
                        }

                        return (
                            <button
                                key={tx.id}
                                onClick={() => setSelectedTx(tx)}
                                className="w-full flex items-center p-3 rounded-2xl text-white shadow-sm transition-transform active:scale-95 text-left"
                                style={{ backgroundColor: '#2C2C2E' }}
                            >
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-3 flex-shrink-0 ${iconBg}`}>
                                    <Icon size={18} className={iconColor} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="font-medium truncate text-sm text-white">{mainText}</div>
                                    <div className="text-xs text-white/50">{subText}</div>
                                </div>
                                <div className="font-semibold text-sm text-white whitespace-nowrap ml-2">
                                    {tx.amount.toLocaleString()} ₽
                                </div>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Transaction Details Modal */}
            {selectedTx && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setSelectedTx(null)}>
                    <div
                        className="w-full max-w-sm rounded-[24px] p-6 text-left relative shadow-2xl animate-in fade-in zoom-in-95 duration-200"
                        style={{ backgroundColor: '#1C1C1E', color: 'white' }}
                        onClick={e => e.stopPropagation()}
                    >
                        {/* Close Button */}
                        <button
                            onClick={() => setSelectedTx(null)}
                            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                        >
                            <X size={20} className="text-white/70" />
                        </button>

                        {/* Title Section */}
                        <div className="mb-6">
                            <div className="text-xs font-medium text-white/50 mb-1 uppercase tracking-wide">
                                {selectedTx.type === 'material' ? 'Закупка материалов' :
                                    selectedTx.type === 'work' ? 'Оплата работ' :
                                        selectedTx.type === 'mechanism' ? 'Аренда техники' : 'Прочие расходы'}
                            </div>
                            <h3 className="text-2xl font-bold mb-1">
                                {Math.abs(selectedTx.amount).toLocaleString()} ₽
                            </h3>
                            <div className="text-sm text-white/50">{selectedTx.date}</div>
                        </div>

                        {/* Details List */}
                        <div className="space-y-4">
                            {selectedTx.type === 'material' && (
                                <>
                                    <div className="p-4 rounded-xl bg-white/5">
                                        <div className="text-xs text-white/40 mb-1">Поставщик</div>
                                        <div className="font-medium text-sm">{selectedTx.supplier}</div>
                                    </div>
                                    <div className="p-4 rounded-xl bg-white/5">
                                        <div className="text-xs text-white/40 mb-1">Документ</div>
                                        <div className="font-medium text-sm">{selectedTx.number}</div>
                                    </div>
                                    <div className="p-4 rounded-xl bg-white/5">
                                        <div className="text-xs text-white/40 mb-2">Список материалов</div>
                                        <div className="text-sm leading-relaxed text-white/80">
                                            {selectedTx.materials}
                                        </div>
                                    </div>
                                </>
                            )}

                            {selectedTx.type === 'work' && (
                                <>
                                    <div className="p-4 rounded-xl bg-white/5">
                                        <div className="text-xs text-white/40 mb-1">Бригада</div>
                                        <div className="font-medium text-sm">{selectedTx.brigade}</div>
                                    </div>
                                    <div className="p-4 rounded-xl bg-white/5">
                                        <div className="text-xs text-white/40 mb-1">Отчетный период</div>
                                        <div className="font-medium text-sm">{selectedTx.period}</div>
                                    </div>
                                    <div className="p-4 rounded-xl bg-white/5">
                                        <div className="text-xs text-white/40 mb-1">Описание</div>
                                        <div className="font-medium text-sm">{selectedTx.description}</div>
                                    </div>
                                </>
                            )}

                            {(selectedTx.type === 'mechanism' || selectedTx.type === 'other') && (
                                <>
                                    <div className="p-4 rounded-xl bg-white/5">
                                        <div className="text-xs text-white/40 mb-1">Наименование</div>
                                        <div className="font-medium text-sm">{selectedTx.name}</div>
                                    </div>
                                    {selectedTx.supplier && (
                                        <div className="p-4 rounded-xl bg-white/5">
                                            <div className="text-xs text-white/40 mb-1">Исполнитель</div>
                                            <div className="font-medium text-sm">{selectedTx.supplier}</div>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Export directly since ThemeProvider is now in App.tsx
export const ManagerObjectDetailPage = ManagerObjectDetailContent;
