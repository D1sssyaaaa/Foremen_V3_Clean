
import { Minus, Plus, Ban } from 'lucide-react';
import { IosListRow } from './ui-ios';

export const WorkerRow = ({ entry, onUpdateHours, onToggleStatus, isForeman }: any) => {
    const isWorking = entry.isWorking !== false;

    return (
        <IosListRow className={!isWorking ? "bg-[var(--bg-ios)]/50" : ""}>
            {/* Left Content */}
            <div className="flex-1 min-w-0 pr-4">
                <div className="flex items-center gap-2">
                    <span className={`text-[17px] font-normal tracking-tight ${!isWorking ? 'text-[var(--text-secondary)] line-through' : 'text-[var(--text-primary)]'}`}>
                        {entry.fullName}
                    </span>
                    {isForeman && (
                        <span className="text-[11px] font-medium text-[var(--text-secondary)] bg-[var(--bg-pressed)] px-1.5 py-[2px] rounded">Вы</span>
                    )}
                </div>

                {isWorking && (
                    <div className="text-[13px] text-[var(--text-secondary)] mt-0.5">
                        {entry.isOvertime ? (
                            <span className="text-[#FF9500]">Переработка</span>
                        ) : (
                            "Смена 8ч"
                        )}
                    </div>
                )}
            </div>

            {/* Right Controls */}
            {isWorking ? (
                <div className="flex items-center gap-3">
                    {/* iOS Stepper Design */}
                    <div className="flex items-center bg-[var(--bg-pressed)] rounded-[8px] p-[2px]">
                        <button
                            onClick={() => onUpdateHours(entry.workerId, -1)}
                            className="w-[32px] h-[28px] flex items-center justify-center text-[var(--text-primary)] active:opacity-50 border-r border-[var(--separator)]"
                            disabled={entry.hours <= 0}
                        >
                            <Minus size={18} strokeWidth={2.5} />
                        </button>

                        <span className="w-[32px] text-center font-semibold text-[15px] tabular-nums leading-none text-[var(--text-primary)]">
                            {entry.hours}
                        </span>

                        <button
                            onClick={() => onUpdateHours(entry.workerId, 1)}
                            className="w-[32px] h-[28px] flex items-center justify-center text-[var(--text-primary)] active:opacity-50 border-l border-[var(--separator)]"
                        >
                            <Plus size={18} strokeWidth={2.5} />
                        </button>
                    </div>

                    {/* Ban Button - Minimal */}
                    <button
                        onClick={() => onToggleStatus(entry.workerId)}
                        className="w-8 h-8 flex items-center justify-center text-[var(--text-secondary)] active:text-[#FF3B30] transition-colors"
                    >
                        <Ban size={20} />
                    </button>
                </div>
            ) : (
                <button
                    onClick={() => onToggleStatus(entry.workerId)}
                    className="text-[var(--blue-ios)] text-[15px] font-medium active:opacity-50"
                >
                    Вернуть
                </button>
            )}
        </IosListRow>
    );
};
