import React from 'react';
import { GlassCard } from './GlassCard';
import { useTheme } from '../context/ThemeContext';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface KPICardProps {
    title: string;
    value: number;
    isCurrency?: boolean;
    trend?: number; // Percentage
    isGood?: boolean;
}

export const KPICard: React.FC<KPICardProps> = ({
    title,
    value,
    isCurrency = true,
    trend,
    isGood = true
}) => {
    const { colors, isDark } = useTheme();

    const formatValue = (val: number) => {
        if (isCurrency) {
            return new Intl.NumberFormat('ru-RU', {
                style: 'currency',
                currency: 'RUB',
                maximumFractionDigits: 0
            }).format(val);
        }
        return val.toString();
    };

    return (
        <GlassCard className="w-full">
            <div className="flex justify-between items-start mb-2">
                <span style={{ color: colors.text_secondary }} className="text-sm font-medium">
                    {title}
                </span>
                {trend !== undefined && (
                    <div className={`flex items-center text-xs font-bold px-2 py-1 rounded-full ${isGood ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'
                        }`}>
                        {isGood ? <TrendingUp size={12} className="mr-1" /> : <TrendingDown size={12} className="mr-1" />}
                        {Math.abs(trend)}%
                    </div>
                )}
            </div>

            <div className="text-2xl font-bold tracking-tight" style={{ color: isGood ? colors.success : colors.text_primary }}>
                {formatValue(value)}
            </div>

            {/* Decorative Chart Line (Abstract) */}
            <div className="h-8 mt-4 w-full flex items-end opacity-50 space-x-1">
                {[40, 60, 45, 70, 85, 65, 90].map((h, i) => (
                    <div
                        key={i}
                        className="flex-1 rounded-t-sm transition-all duration-500"
                        style={{
                            height: `${h}%`,
                            backgroundColor: isGood ? colors.success : colors.chart_secondary
                        }}
                    />
                ))}
            </div>
        </GlassCard>
    );
};
