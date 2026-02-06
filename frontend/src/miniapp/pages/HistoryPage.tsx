import { ChevronLeft, Check, Clock, XCircle, AlertCircle } from 'lucide-react';
import { IosSection } from '../components/ui-ios';
import { motion } from 'framer-motion';

// Mock Data for Visualization
const MOCK_HISTORY = [
    { id: 101, date: '2024-02-03', object: 'Зеленый Парк', status: 'PENDING', hours: 40, workers: 5 },
    { id: 102, date: '2024-02-02', object: 'Офис', status: 'APPROVED', hours: 32, workers: 4 },
    { id: 103, date: '2024-02-01', object: 'Солнечный', status: 'REJECTED', hours: 40, workers: 5, rejectionReason: 'Неверное количество часов у Иванова' },
    { id: 104, date: '2024-01-31', object: 'Зеленый Парк', status: 'APPROVED', hours: 48, workers: 6 },
    { id: 105, date: '2024-01-30', object: 'Зеленый Парк', status: 'APPROVED', hours: 48, workers: 6 },
];

const StatusBadge = ({ status }: { status: string }) => {
    switch (status) {
        case 'APPROVED':
            return (
                <div className="flex items-center gap-1 text-[#34C759] bg-[#34C759]/10 px-2 py-0.5 rounded text-[13px] font-medium">
                    <Check size={14} strokeWidth={3} />
                    <span>Принято</span>
                </div>
            );
        case 'REJECTED':
            return (
                <div className="flex items-center gap-1 text-[#FF3B30] bg-[#FF3B30]/10 px-2 py-0.5 rounded text-[13px] font-medium">
                    <XCircle size={14} strokeWidth={2.5} />
                    <span>Отказ</span>
                </div>
            );
        case 'PENDING':
        default:
            return (
                <div className="flex items-center gap-1 text-[#FF9500] bg-[#FF9500]/10 px-2 py-0.5 rounded text-[13px] font-medium">
                    <Clock size={14} strokeWidth={2.5} />
                    <span>Проверка</span>
                </div>
            );
    }
};

export const HistoryPage = ({ onBack }: { onBack: () => void }) => {
    return (
        <div className="min-h-screen bg-[var(--bg-ios)] text-[var(--text-primary)]">
            {/* Header */}
            <div className="bg-[var(--bg-ios)]/90 backdrop-blur-md border-b border-[var(--separator-opaque)] sticky top-0 z-50">
                <div className="h-[44px] flex items-center px-2 relative justify-center">
                    <button
                        onClick={onBack}
                        className="absolute left-2 flex items-center text-[var(--blue-ios)] hover:opacity-70 transition-opacity"
                    >
                        <ChevronLeft size={26} strokeWidth={2} className="-ml-1" />
                        <span className="text-[17px] font-normal leading-none pb-0.5">Табель</span>
                    </button>
                    <h1 className="text-[17px] font-semibold">История</h1>
                </div>
            </div>

            <div className="pt-6 pb-12">
                <IosSection title="ПОСЛЕДНИЕ ОТЧЕТЫ">
                    {MOCK_HISTORY.map((item, idx) => (
                        <div key={item.id} className={idx !== MOCK_HISTORY.length - 1 ? "border-b border-[var(--separator)]" : ""}>
                            <div className="bg-[var(--bg-card)] p-4 active:bg-[var(--bg-pressed)] transition-colors cursor-pointer">
                                <div className="flex justify-between items-start mb-2">
                                    <div className="font-semibold text-[17px]">
                                        {new Date(item.date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
                                        <span className="text-[var(--text-secondary)] font-normal ml-2 text-[15px]">
                                            {item.object}
                                        </span>
                                    </div>
                                    <StatusBadge status={item.status} />
                                </div>

                                <div className="flex justify-between items-end">
                                    <div className="text-[13px] text-[var(--text-secondary)]">
                                        {item.workers} чел. • {item.hours} ч.
                                    </div>
                                    {item.status === 'REJECTED' && (
                                        <div className="text-[13px] text-[#FF3B30] font-medium flex items-center gap-1 mt-1">
                                            <AlertCircle size={14} />
                                            См. причину
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </IosSection>

                <div className="px-6 mt-4 text-center">
                    <p className="text-[13px] text-[var(--text-secondary)]">
                        История хранится за последние 30 дней.
                    </p>
                </div>
            </div>
        </div>
    );
};
