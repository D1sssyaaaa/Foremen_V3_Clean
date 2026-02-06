import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    onClick?: () => void;
    noPadding?: boolean;
}

export const GlassCard: React.FC<GlassCardProps> = ({
    children,
    className = '',
    onClick,
    noPadding = false
}) => {
    const { colors } = useTheme();

    return (
        <motion.div
            whileTap={onClick ? { scale: 0.98 } : undefined}
            onClick={onClick}
            className={`relative overflow-hidden backdrop-blur-xl ${className}`}
            style={{
                backgroundColor: colors.card_bg,
                border: `1px solid ${colors.card_border}`,
                borderRadius: '20px',
                padding: noPadding ? '0' : '16px',
                boxShadow: '0 4px 24px -1px rgba(0, 0, 0, 0.1)',
            }}
        >
            {children}
        </motion.div>
    );
};
