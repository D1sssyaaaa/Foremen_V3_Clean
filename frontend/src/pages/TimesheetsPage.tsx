import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Calendar,
    Clock,
    User,
    CheckCircle2,
    XCircle,
    AlertCircle,
    ChevronRight,
    Filter,
    Search,
    Check,
    X
} from 'lucide-react';

interface TimeSheetListItem {
    id: number;
    brigade_name: string;
    foreman_name: string;
    objects_info: string;
    period_start: string;
    period_end: string;
    status: string;
    total_hours: number;
    created_at: string;
}

interface TimeSheetItemResponse {
    id: number;
    member_id: number;
    member_name: string;
    date: string;
    cost_object_id: number | null;
    cost_object_name: string | null;
    hours: number;
}

interface TimeSheetResponse {
    id: number;
    brigade_id: number;
    brigade_name: string;
    period_start: string;
    period_end: string;
    status: string;
    hour_rate: number | null;
    total_hours: number;
    total_amount: number | null;
    items: TimeSheetItemResponse[];
    created_at: string;
    updated_at: string;
}

export function TimesheetsPage() {
    const { user } = useAuth();
    const [timesheets, setTimesheets] = useState<TimeSheetListItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('ALL');
    const [selectedTimesheet, setSelectedTimesheet] = useState<TimeSheetResponse | null>(null);
    const [loadingDetails, setLoadingDetails] = useState(false);
    const [rejectReason, setRejectReason] = useState('');
    const [showRejectInput, setShowRejectInput] = useState(false);

    const canApprove = user?.roles.some(r => ['HR_MANAGER', 'MANAGER', 'ADMIN'].includes(r));

    useEffect(() => {
        loadTimesheets();
    }, [statusFilter]);

    const loadTimesheets = async () => {
        setLoading(true);
        try {
            const params: any = {};
            if (statusFilter !== 'ALL') {
                params.status = statusFilter;
            }
            const data = await apiClient.get<TimeSheetListItem[]>('/time-sheets/', { params });
            setTimesheets(data);
        } catch (error) {
            console.error('Failed to load timesheets:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadTimesheetDetails = async (id: number) => {
        setLoadingDetails(true);
        try {
            const data = await apiClient.get<TimeSheetResponse>(`/time-sheets/${id}`);
            setSelectedTimesheet(data);
            setShowRejectInput(false);
            setRejectReason('');
        } catch (error) {
            console.error('Failed to load details:', error);
        } finally {
            setLoadingDetails(false);
        }
    };

    const handleApprove = async () => {
        if (!selectedTimesheet) return;
        if (!confirm('Утвердить табель? Это действие создаст записи о затратах.')) return;

        try {
            await apiClient.post(`/time-sheets/${selectedTimesheet.id}/approve`, { items: [] }); // Start with empty overrides
            // Reload details to show updated status
            await loadTimesheetDetails(selectedTimesheet.id);
            loadTimesheets(); // Reload list
            alert('Табель утвержден');
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Ошибка утверждения');
        }
    };

    const handleReject = async () => {
        if (!selectedTimesheet) return;
        if (!showRejectInput) {
            setShowRejectInput(true);
            return;
        }
        if (!rejectReason.trim()) {
            alert('Укажите причину отклонения');
            return;
        }

        try {
            await apiClient.post(`/time-sheets/${selectedTimesheet.id}/reject`, { comment: rejectReason });
            await loadTimesheetDetails(selectedTimesheet.id);
            loadTimesheets();
            alert('Табель отклонен');
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Ошибка отклонения');
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'DRAFT': return 'bg-gray-100 text-gray-600';
            case 'SUBMITTED':
            case 'UNDER_REVIEW': return 'bg-blue-100 text-blue-700';
            case 'APPROVED': return 'bg-green-100 text-green-700';
            case 'REJECTED':
            case 'CORRECTED': return 'bg-red-100 text-red-700';
            case 'CANCELLED': return 'bg-gray-200 text-gray-500';
            default: return 'bg-gray-100 text-gray-600';
        }
    };

    const getStatusText = (status: string) => {
        const map: Record<string, string> = {
            'DRAFT': 'Черновик',
            'SUBMITTED': 'Отправлен',
            'UNDER_REVIEW': 'На проверке',
            'APPROVED': 'Утвержден',
            'REJECTED': 'Отклонен',
            'CORRECTED': 'Исправлен',
            'CANCELLED': 'Отменен'
        };
        return map[status] || status;
    };

    const statusOptions = [
        { value: 'ALL', label: 'Все' },
        { value: 'UNDER_REVIEW', label: 'На проверке' },
        { value: 'DRAFT', label: 'Черновики' },
        { value: 'APPROVED', label: 'Утвержденные' },
        { value: 'REJECTED', label: 'Отклоненные' },
    ];

    return (
        <div className="space-y-6 animate-fade-in pb-20">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Табели</h1>
                    <p className="text-[var(--text-secondary)]">Учет рабочего времени бригад</p>
                </div>
            </div>

            {/* Filters */}
            <div className="flex overflow-x-auto pb-2 gap-2 hide-scrollbar">
                {statusOptions.map(option => (
                    <button
                        key={option.value}
                        onClick={() => setStatusFilter(option.value)}
                        className={`
              px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors
              ${statusFilter === option.value
                                ? 'bg-[var(--blue-ios)] text-white shadow-md'
                                : 'bg-[var(--bg-card)] text-[var(--text-secondary)] hover:bg-[var(--bg-ios)] border border-[var(--separator)]'}
            `}
                    >
                        {option.label}
                    </button>
                ))}
            </div>

            {/* List */}
            <div className="grid grid-cols-1 gap-4">
                {loading ? (
                    <div className="flex justify-center p-10"><div className="animate-spin text-[var(--blue-ios)]"><Clock size={32} /></div></div>
                ) : timesheets.length === 0 ? (
                    <div className="text-center p-10 bg-[var(--bg-card)] rounded-2xl border border-[var(--separator)]">
                        <p className="text-[var(--text-secondary)]">Табели не найдены</p>
                    </div>
                ) : (
                    <AnimatePresence>
                        {timesheets.map(ts => (
                            <motion.div
                                key={ts.id}
                                layout
                                initial={{ opacity: 0, scale: 0.98 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.98 }}
                                onClick={() => loadTimesheetDetails(ts.id)}
                                className="bg-[var(--bg-card)] p-4 rounded-xl border border-[var(--separator)] shadow-sm hover:shadow-md transition-all cursor-pointer active:scale-[0.99] group relative overflow-hidden"
                            >
                                <div className="flex justify-between items-start mb-3">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-blue-50 text-[var(--blue-ios)] flex items-center justify-center font-bold">
                                            {ts.brigade_name.substring(0, 2).toUpperCase()}
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-[var(--text-primary)]">{ts.brigade_name}</h3>
                                            <div className="text-xs text-[var(--text-secondary)] flex items-center gap-1">
                                                <User size={10} /> Бригадир: {ts.foreman_name}
                                            </div>
                                        </div>
                                    </div>
                                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${getStatusColor(ts.status)}`}>
                                        {getStatusText(ts.status)}
                                    </span>
                                </div>

                                <div className="flex items-center gap-4 text-sm text-[var(--text-secondary)] mb-3 pl-13">
                                    <div className="flex items-center gap-1.5">
                                        <Calendar size={14} />
                                        {new Date(ts.period_start).toLocaleDateString()} - {new Date(ts.period_end).toLocaleDateString()}
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        <Clock size={14} />
                                        {ts.total_hours} ч.
                                    </div>
                                </div>

                                {ts.objects_info && (
                                    <div className="text-xs bg-[var(--bg-ios)] p-2 rounded-lg text-[var(--text-secondary)] line-clamp-1">
                                        📍 {ts.objects_info}
                                    </div>
                                )}

                                <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--separator)] opacity-0 group-hover:opacity-100 transition-opacity" />
                            </motion.div>
                        ))}
                    </AnimatePresence>
                )}
            </div>

            {/* Details Modal */}
            {selectedTimesheet && (
                <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedTimesheet(null)}>
                    <motion.div
                        initial={{ opacity: 0, y: 100 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-[var(--bg-card)] w-full max-w-2xl max-h-[85vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden"
                        onClick={e => e.stopPropagation()}
                    >
                        {/* Modal Header */}
                        <div className="p-4 border-b border-[var(--separator)] bg-[var(--bg-ios)] flex justify-between items-center sticky top-0 z-10">
                            <div>
                                <h2 className="text-lg font-bold">Табель #{selectedTimesheet.id}</h2>
                                <p className="text-xs text-[var(--text-secondary)]">Создан {new Date(selectedTimesheet.created_at).toLocaleString()}</p>
                            </div>
                            <button onClick={() => setSelectedTimesheet(null)} className="p-2 bg-white rounded-full hover:bg-gray-100"><X size={20} /></button>
                        </div>

                        {/* Modal Content */}
                        <div className="p-4 overflow-y-auto flex-1 space-y-6">
                            <div className="flex justify-between items-center p-3 bg-blue-50 rounded-xl border border-blue-100">
                                <div>
                                    <div className="text-xs text-blue-600 font-bold uppercase tracking-wider">Статус</div>
                                    <div className="font-bold text-blue-900">{getStatusText(selectedTimesheet.status)}</div>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs text-blue-600 font-bold uppercase tracking-wider">Всего часов</div>
                                    <div className="font-bold text-blue-900 text-xl">{selectedTimesheet.total_hours}</div>
                                </div>
                            </div>

                            <div>
                                <h3 className="font-bold mb-3 flex items-center gap-2"><User size={18} className="text-[var(--blue-ios)]" /> Сотрудники и работы</h3>
                                <div className="space-y-3">
                                    {selectedTimesheet.items.map(item => (
                                        <div key={item.id} className="bg-[var(--bg-ios)] p-3 rounded-xl flex justify-between items-center">
                                            <div>
                                                <div className="font-medium">{item.member_name}</div>
                                                <div className="text-xs text-[var(--text-secondary)]">
                                                    {new Date(item.date).toLocaleDateString()} • {item.cost_object_name || 'Без объекта'}
                                                </div>
                                            </div>
                                            <div className="font-mono font-bold bg-white px-3 py-1 rounded-lg border border-[var(--separator)]">
                                                {item.hours} ч.
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Actions Footer */}
                        {canApprove && selectedTimesheet.status === 'UNDER_REVIEW' && (
                            <div className="p-4 border-t border-[var(--separator)] bg-white safe-area-bottom">
                                {showRejectInput ? (
                                    <div className="space-y-3">
                                        <textarea
                                            value={rejectReason}
                                            onChange={e => setRejectReason(e.target.value)}
                                            placeholder="Укажите причину отклонения..."
                                            className="w-full p-3 rounded-xl border border-red-200 bg-red-50 text-sm outline-none focus:ring-2 focus:ring-red-500"
                                            rows={2}
                                        />
                                        <div className="flex gap-2">
                                            <button onClick={handleReject} className="flex-1 bg-red-600 text-white font-bold py-2 rounded-xl">Подтвердить отклонение</button>
                                            <button onClick={() => setShowRejectInput(false)} className="px-4 py-2 bg-gray-100 rounded-xl font-medium">Отмена</button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex gap-3">
                                        <button
                                            onClick={handleReject}
                                            className="flex-1 py-3 bg-red-100 text-red-700 font-bold rounded-xl hover:bg-red-200 transition-colors"
                                        >
                                            Отклонить
                                        </button>
                                        <button
                                            onClick={handleApprove}
                                            className="flex-2 w-full py-3 bg-green-600 text-white font-bold rounded-xl shadow-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                                        >
                                            <Check size={20} /> Утвердить
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </motion.div>
                </div>
            )}
        </div>
    );
}
