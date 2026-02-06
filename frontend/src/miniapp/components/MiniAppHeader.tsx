import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Moon, Sun } from 'lucide-react';
import { useTheme } from '../../miniapp-manager/context/ThemeContext';

interface MiniAppHeaderProps {
    title: string;
    onBack?: () => void;
    showBack?: boolean;
}

export const MiniAppHeader: React.FC<MiniAppHeaderProps> = ({ title, onBack, showBack = true }) => {
    const navigate = useNavigate();
    const { isDark, toggleTheme } = useTheme();

    const handleBack = () => {
        if (onBack) {
            onBack();
        } else {
            navigate(-1);
        }
    };

    return (
        <div className="sticky top-0 z-50 bg-[var(--bg-ios)]/90 backdrop-blur-xl border-b border-[var(--separator-opaque)] px-4 py-3 transition-colors duration-300">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    {showBack && (
                        <button
                            onClick={handleBack}
                            className="p-2 -ml-2 rounded-full active:bg-black/5 dark:active:bg-white/10 text-[var(--blue-ios)] transition-colors"
                        >
                            <ArrowLeft size={24} />
                        </button>
                    )}
                    <h1 className="text-[17px] font-semibold text-[var(--text-primary)]">{title}</h1>
                </div>

                <button
                    onClick={toggleTheme}
                    className="p-2 rounded-full bg-black/5 dark:bg-white/10 text-[var(--text-secondary)] hover:text-[var(--text-primary)] active:scale-95 transition-all"
                    aria-label="Toggle theme"
                >
                    {isDark ? <Sun size={20} className="text-yellow-400" /> : <Moon size={20} />}
                </button>
            </div>
        </div>
    );
};
