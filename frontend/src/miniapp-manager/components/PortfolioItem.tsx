import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { ChevronRight, Building2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { ObjectPortfolioItem } from '../types';

interface PortfolioItemProps {
    item: ObjectPortfolioItem;
    onClick: (id: number) => void;
}

export const PortfolioItem: React.FC<PortfolioItemProps> = ({ item, onClick }) => {
    const { colors, isDark } = useTheme();

    // Basic logic to determine status if not provided (assume 80% warning, 100% danger)
    // If contract_amount is missing, we can't calculate budget
    const budget = item.contract_amount || 0;
    const percent = budget > 0 ? (item.total_costs / budget) * 100 : 0;

    let statusColor = colors.success;
    let StatusIcon = CheckCircle2;
    let statusText = "В бюджете";

    if (percent > 100) {
        statusColor = colors.danger;
        StatusIcon = AlertCircle;
        statusText = "Перерасход";
    } else if (percent > 85) {
        statusColor = colors.warning;
        StatusIcon = AlertCircle;
        statusText = "Риск";
    }

    return (
        <button
            onClick={() => onClick(item.object_id)}
            className="w-full text-left rounded-[20px] p-5 shadow-sm transition-transform active:scale-95"
            style={{ backgroundColor: isDark ? '#1C1C1E' : '#FFFFFF' }}
        >
            {/* Header */}
            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-3">
                    <div
                        className="w-10 h-10 rounded-full flex items-center justify-center"
                        style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : '#F2F2F7' }}
                    >
                        <Building2 size={20} style={{ color: colors.text_primary }} />
                    </div>
                    <div>
                        <h3 className="font-semibold text-base leading-tight" style={{ color: colors.text_primary }}>
                            {item.object_name}
                        </h3>
                        <div className="flex items-center mt-1">
                            <div className={`w-1.5 h-1.5 rounded-full mr-1.5 ${percent > 100 ? 'bg-red-500' : percent > 85 ? 'bg-yellow-500' : 'bg-green-500'}`} />
                            <span className="text-xs text-secondary opacity-60" style={{ color: colors.text_secondary }}>
                                {percent > 0 ? `${Math.round(percent)}% освоено` : 'Нет данных'}
                            </span>
                        </div>
                    </div>
                </div>
                <ChevronRight size={20} style={{ color: colors.text_secondary, opacity: 0.5 }} />
            </div>

            {/* Progress Bar */}
            {budget > 0 && (
                <div className="w-full h-1.5 rounded-full mb-4 overflow-hidden bg-gray-100 dark:bg-white/5">
                    <div
                        className="h-full rounded-full"
                        style={{
                            width: `${Math.min(percent, 100)}%`,
                            backgroundColor: statusColor
                        }}
                    />
                </div>
            )}

            {/* Financials Grid */}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <div className="text-[10px] uppercase tracking-wider font-semibold mb-0.5 opacity-50" style={{ color: colors.text_secondary }}>Расход</div>
                    <div className="font-semibold text-sm" style={{ color: colors.text_primary }}>
                        {(item.total_costs / 1000000).toFixed(1)}M ₽
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-[10px] uppercase tracking-wider font-semibold mb-0.5 opacity-50" style={{ color: colors.text_secondary }}>Бюджет</div>
                    <div className="font-medium text-sm ml-auto" style={{ color: colors.text_secondary }}>
                        {budget > 0 ? `${(budget / 1000000).toFixed(1)}M ₽` : '—'}
                    </div>
                </div>
            </div>
        </button>
    );
};
