
import { useEffect, useState } from 'react';
import { useTimeSheetStore } from '../store/useTimeSheetStore';
import { IosSection } from '../components/ui-ios';
import { DateSlider } from '../components/DateSlider';
import { WorkerRow } from '../components/WorkerRow';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, Plus, Check, Loader2, ChevronRight, ChevronLeft } from 'lucide-react';
import WebApp from '@twa-dev/sdk';
import { HistoryPage } from './HistoryPage';
import { SettingsPage } from './SettingsPage';
import { timesheetApi } from '../api/timesheetApi';
import { format } from 'date-fns';

export const TimeSheetFlow = () => {
    const store = useTimeSheetStore();
    const [view, setView] = useState<'flow' | 'settings' | 'history'>('flow');
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const [isObjectSheetOpen, setIsObjectSheetOpen] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);

    // Store full details for the list
    const [submissionItems, setSubmissionItems] = useState<{ key: string, dateStr: string, objectId: number, count: number, totalHours: number, dateLabel: string, objectName: string }[]>([]);

    // State for in-modal editing
    const [editingDraft, setEditingDraft] = useState<{ dateStr: string, objectId: number, title: string } | null>(null);

    const activeObjectId = store.selectedObjectId || 1;

    const objects = [
        { id: 1, name: "Зеленый Парк" },
        { id: 2, name: "Солнечный" },
        { id: 3, name: "Офис" }
    ];

    const activeObject = objects.find(o => o.id === activeObjectId) || objects[0];

    useEffect(() => {
        WebApp.ready();
        WebApp.expand();

        // Theme Handling
        const colorScheme = WebApp.colorScheme;
        if (colorScheme === 'dark') {
            document.documentElement.classList.add('dark');
            WebApp.setHeaderColor('#000000');
            WebApp.setBackgroundColor('#000000');
        } else {
            document.documentElement.classList.remove('dark');
            WebApp.setHeaderColor('#F2F2F7');
            WebApp.setBackgroundColor('#F2F2F7');
        }

        const user = WebApp.initDataUnsafe?.user;
        if (user) {
            const foremanId = user.id;
            const foremanName = `${user.first_name} ${user.last_name || ''}`.trim();
            store.setForemanId(foremanId);
            // Ensure foreman exists in brigade
            store.addToBrigade({ id: foremanId, fullName: foremanName });
            // Add to current sheet if empty
            if (store.entries.length === 0) {
                store.addWorker({ id: foremanId, fullName: foremanName });
            }
        }

        setTimeout(() => {
            setIsLoading(false);
            if (!store.selectedObjectId) store.setObjectId(1);
        }, 800);
    }, []);

    const generateSubmissionItems = () => {
        store.saveCurrentToDraft();
        const drafts = store.drafts;
        const items: typeof submissionItems = [];

        for (const [key, entries] of Object.entries(drafts)) {
            const [dateStr, objectIdStr] = key.split(':');
            const objectId = parseInt(objectIdStr);
            const workingEntries = entries.filter(e => e.isWorking !== false);

            if (workingEntries.length > 0) {
                const dateObj = new Date(dateStr);
                const objName = objects.find(o => o.id === objectId)?.name || "Неизвестный";
                const totalHours = workingEntries.reduce((sum, e) => sum + e.hours, 0);

                items.push({
                    key,
                    dateStr,
                    objectId,
                    count: workingEntries.length,
                    totalHours,
                    dateLabel: format(dateObj, 'dd.MM.yyyy'),
                    objectName: objName
                });
            }
        }

        // Sort by date
        items.sort((a, b) => new Date(a.dateStr).getTime() - new Date(b.dateStr).getTime());
        return items;
    };

    const prepareSubmission = () => {
        const items = generateSubmissionItems();

        if (items.length === 0) {
            WebApp.showPopup({ title: 'Пусто', message: 'Нет данных для отправки' });
            return;
        }

        setSubmissionItems(items);
        setEditingDraft(null);
        setShowConfirm(true);
    };

    const handleDeleteItem = (e: React.MouseEvent, key: string, dateStr: string, objectId: number) => {
        e.stopPropagation();
        store.removeDraft(new Date(dateStr), objectId);

        const items = generateSubmissionItems();
        setSubmissionItems(items);
        if (items.length === 0) setShowConfirm(false);
    };

    const handleEditItem = (dateStr: string, objectId: number, title: string) => {
        store.setDate(new Date(dateStr));
        store.setObjectId(objectId);
        setEditingDraft({ dateStr, objectId, title });
    };

    const handleBackFromEdit = () => {
        store.saveCurrentToDraft();
        const items = generateSubmissionItems();
        setSubmissionItems(items);
        setEditingDraft(null);
    };

    const confirmSubmit = async () => {
        setIsSubmitting(true);
        setShowConfirm(false);
        try {
            const drafts = store.drafts;
            const promises = [];
            for (const [key, entries] of Object.entries(drafts)) {
                const [dateStr, objectIdStr] = key.split(':');
                const objectId = parseInt(objectIdStr);
                const payloadEntries = entries
                    .filter(e => e.isWorking !== false)
                    .map(e => ({ worker_id: e.workerId, hours: e.hours }));

                if (payloadEntries.length === 0) continue;
                const formattedDate = format(new Date(dateStr), 'yyyy-MM-dd');
                promises.push(timesheetApi.submit(formattedDate, objectId, payloadEntries));
            }
            if (promises.length > 0) await Promise.all(promises);
            WebApp.showPopup({ title: 'Отправлено', message: `Успешно отправлено`, buttons: [{ type: 'ok' }] });
            store.reset();
        } catch (e) {
            WebApp.showPopup({ title: 'Ошибка', message: 'Не удалось отправить' });
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleNextDay = () => {
        const nextDay = new Date(store.currentDate);
        nextDay.setDate(nextDay.getDate() + 1);
        store.setDate(nextDay);
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-[var(--bg-ios)]">
                <Loader2 className="w-6 h-6 animate-spin text-[var(--text-secondary)]" />
            </div>
        );
    }

    if (view === 'settings') {
        return <SettingsPage onBack={() => setView('flow')} />;
    }

    if (view === 'history') {
        return <HistoryPage onBack={() => setView('flow')} />;
    }

    const workingWorkers = store.entries.filter(e => e.isWorking !== false);
    const notWorkingWorkers = store.entries.filter(e => e.isWorking === false);

    return (
        <div className="min-h-screen bg-[var(--bg-ios)] pb-32 font-sans text-[var(--text-primary)]">
            {/* iOS Navigation Bar */}
            <div className="sticky top-0 z-50 bg-[var(--bg-ios)]/90 backdrop-blur-xl border-b border-[var(--separator-opaque)] px-4 pt-3 pb-3">
                <div className="flex justify-between items-center mb-2">
                    {/* Header: Left (History), Center (Title), Right (Settings) */}
                    <button
                        onClick={() => setView('history')}
                        className="w-8 h-8 rounded-full bg-[var(--bg-pressed)] flex items-center justify-center text-[var(--text-secondary)] active:text-[var(--blue-ios)] active:opacity-60 transition-all"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10" />
                            <polyline points="12 6 12 12 16 14" />
                        </svg>
                    </button>

                    <h1 className="text-[20px] font-bold leading-none tracking-tight text-[var(--text-primary)]">Табель</h1>

                    <button
                        onClick={() => setView('settings')}
                        className="w-8 h-8 rounded-full bg-[var(--bg-pressed)] flex items-center justify-center text-[var(--blue-ios)] active:opacity-60 transition-opacity"
                    >
                        <Settings size={20} />
                    </button>
                </div>

                {/* Object Selector */}
                <button
                    onClick={() => setIsObjectSheetOpen(true)}
                    className="w-full bg-[var(--bg-card)] rounded-[10px] p-2 flex items-center justify-between px-3 active:bg-[var(--bg-pressed)] transition-colors shadow-sm"
                >
                    <span className="text-[17px] font-medium text-[var(--text-primary)] truncate pr-2">{activeObject.name}</span>
                    <div className="text-[var(--blue-ios)] flex items-center text-[13px] font-medium">
                        Сменить
                        <ChevronRight size={16} className="ml-1 opacity-60" />
                    </div>
                </button>
            </div>

            {/* Object Action Sheet */}
            <AnimatePresence>
                {isObjectSheetOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/40 z-[60]"
                            onClick={() => setIsObjectSheetOpen(false)}
                        />
                        <motion.div
                            initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "100%" }}
                            transition={{ type: "spring", damping: 25, stiffness: 300 }}
                            className="fixed bottom-0 left-0 right-0 bg-[var(--bg-ios)] rounded-t-[20px] z-[61] overflow-hidden pb-8 max-h-[80vh]"
                        >
                            <div className="flex justify-center pt-3 pb-2">
                                <div className="w-12 h-1.5 bg-[var(--separator-opaque)] rounded-full opacity-50" />
                            </div>
                            <div className="px-4 pb-2 text-[20px] font-semibold text-center mb-4 text-[var(--text-primary)]">Выберите объект</div>
                            <IosSection className="mx-4 mb-4">
                                {objects.map((obj, idx) => (
                                    <div key={obj.id} className={idx !== objects.length - 1 ? "border-b border-[var(--separator)]" : ""}>
                                        <button
                                            onClick={() => {
                                                store.setObjectId(obj.id);
                                                setIsObjectSheetOpen(false);
                                            }}
                                            className="w-full text-left px-4 py-3.5 bg-[var(--bg-card)] text-[17px] flex justify-between items-center active:bg-[var(--bg-pressed)] transition-colors"
                                        >
                                            <span className={obj.id === activeObjectId ? "font-semibold text-[var(--blue-ios)]" : "text-[var(--text-primary)]"}>
                                                {obj.name}
                                            </span>
                                            {obj.id === activeObjectId && <Check size={20} className="text-[var(--blue-ios)]" />}
                                        </button>
                                    </div>
                                ))}
                            </IosSection>
                            <div className="px-4">
                                <button
                                    onClick={() => setIsObjectSheetOpen(false)}
                                    className="w-full py-3.5 bg-[var(--bg-card)] rounded-[14px] text-[var(--blue-ios)] font-semibold text-[17px] active:opacity-50"
                                >
                                    Отмена
                                </button>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* Main Content (Date Picker, Workers) */}
            <div className="mt-4 mb-2">
                <DateSlider selectedDate={store.currentDate} onSelect={store.setDate} />
            </div>

            <IosSection title={`Сотрудники (${workingWorkers.length})`}>
                {workingWorkers.length === 0 && (
                    <div className="p-4 text-center text-[var(--text-secondary)] text-[15px]">Нет сотрудников</div>
                )}
                {workingWorkers.map((entry, idx) => (
                    <div key={entry.workerId} className={idx !== workingWorkers.length - 1 ? "border-b border-[var(--separator)]" : ""}>
                        <WorkerRow
                            entry={entry}
                            onUpdateHours={store.updateHours}
                            onToggleStatus={store.toggleWorkerStatus}
                            onRemove={store.removeWorker}
                            isForeman={entry.workerId === store.foremanId}
                        />
                    </div>
                ))}
            </IosSection>

            {notWorkingWorkers.length > 0 && (
                <IosSection title="Не работают сегодня">
                    {notWorkingWorkers.map((entry, idx) => (
                        <div key={entry.workerId} className={idx !== notWorkingWorkers.length - 1 ? "border-b border-[var(--separator)]" : ""}>
                            <WorkerRow
                                entry={entry}
                                onUpdateHours={store.updateHours}
                                onToggleStatus={store.toggleWorkerStatus}
                                onRemove={store.removeWorker}
                                isForeman={entry.workerId === store.foremanId}
                            />
                        </div>
                    ))}
                </IosSection>
            )}

            {/* Bottom Bar */}
            <div className="fixed bottom-0 left-0 right-0 bg-[var(--bg-ios)]/90 backdrop-blur-xl border-t border-[var(--separator-opaque)] z-50 pb-safe">
                <div className="flex items-center justify-between px-4 py-3 gap-3">
                    <button
                        onClick={() => {
                            const prev = new Date(store.currentDate);
                            prev.setDate(prev.getDate() - 1);
                            store.setDate(prev);
                        }}
                        className="w-[50px] h-[50px] rounded-[14px] bg-[var(--bg-pressed)] flex items-center justify-center text-[var(--text-primary)] active:opacity-60"
                    >
                        <ChevronLeft size={28} className="-ml-1" />
                    </button>

                    <button
                        onClick={prepareSubmission}
                        disabled={isSubmitting}
                        className="flex-1 h-[50px] rounded-[14px] bg-[var(--blue-ios)] text-white font-semibold text-[17px] active:opacity-80 transition-opacity flex items-center justify-center gap-2 shadow-sm"
                    >
                        {isSubmitting ? <Loader2 className="animate-spin" /> : "Отправить"}
                    </button>

                    <button
                        onClick={handleNextDay}
                        className="w-[50px] h-[50px] rounded-[14px] bg-[var(--bg-pressed)] flex items-center justify-center text-[var(--text-primary)] active:opacity-60"
                    >
                        <ChevronRight size={28} className="-mr-0.5" />
                    </button>
                </div>
                <div className="h-6" />
            </div>

            {/* Confirmation Modal */}
            <AnimatePresence>
                {showConfirm && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/40 z-[60]"
                            onClick={() => setShowConfirm(false)}
                        />
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0, y: 20 }}
                            animate={{ scale: 1, opacity: 1, y: 0 }}
                            exit={{ scale: 0.95, opacity: 0, y: 20 }}
                            className="fixed flex flex-col items-center justify-center inset-0 pointer-events-none z-[62]"
                        >
                            <div className="bg-[var(--bg-ios)] w-[95%] max-w-md h-[85vh] rounded-[20px] overflow-hidden shadow-2xl pointer-events-auto flex flex-col text-[var(--text-primary)]">
                                {!editingDraft ? (
                                    // MODE: LIST (Review)
                                    <div className="flex flex-col h-full">
                                        <div className="p-4 text-center border-b border-[var(--separator-opaque)] bg-[var(--bg-card)]/80 backdrop-blur-sm sticky top-0 z-10">
                                            <h3 className="text-[17px] font-semibold">Проверка перед отправкой</h3>
                                        </div>

                                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                                            {submissionItems.map(item => (
                                                <div
                                                    key={item.key}
                                                    onClick={() => handleEditItem(item.dateStr, item.objectId, `${item.dateLabel} - ${item.objectName}`)}
                                                    className="flex items-center justify-between bg-[var(--bg-card)] p-4 rounded-[14px] shadow-sm active:scale-[0.98] transition-transform cursor-pointer border border-[var(--separator)]/20"
                                                >
                                                    <div className="flex-1 min-w-0 pr-2">
                                                        <div className="flex flex-col gap-0.5">
                                                            <div className="flex items-center gap-2">
                                                                <span className="font-semibold text-[17px] text-[var(--text-primary)]">{item.dateLabel}</span>
                                                                {/* Object Tag */}
                                                                <span className="px-2 py-0.5 rounded-md bg-[var(--blue-ios)]/10 text-[var(--blue-ios)] text-[11px] font-semibold uppercase tracking-wide truncate max-w-[120px]">
                                                                    {item.objectName}
                                                                </span>
                                                            </div>
                                                            <div className="text-[14px] text-[var(--text-secondary)] mt-1">
                                                                {item.count} чел. • Всего {item.totalHours} ч.
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-3 shrink-0">
                                                        <button
                                                            onClick={(e) => handleDeleteItem(e, item.key, item.dateStr, item.objectId)}
                                                            className="w-9 h-9 flex items-center justify-center text-[#FF3B30] bg-[#FF3B30]/10 rounded-full active:bg-[#FF3B30]/20 transition-colors"
                                                        >
                                                            <Plus className="rotate-45" size={18} strokeWidth={2.5} />
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>

                                        <div className="p-4 bg-[var(--bg-card)]/80 backdrop-blur-sm border-t border-[var(--separator-opaque)] flex flex-col gap-3">
                                            <button
                                                onClick={confirmSubmit}
                                                className="w-full h-[52px] bg-[var(--blue-ios)] text-white text-[17px] font-semibold rounded-[14px] active:opacity-90 shadow-sm"
                                            >
                                                Отправить все
                                            </button>
                                            <button
                                                onClick={() => setShowConfirm(false)}
                                                className="w-full h-[52px] bg-[var(--bg-card)] text-[var(--blue-ios)] text-[17px] font-semibold rounded-[14px] active:bg-[var(--bg-pressed)]"
                                            >
                                                Закрыть
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    // MODE: EDITOR (Editing a specific day)
                                    <div className="flex flex-col h-full bg-[var(--bg-ios)]">
                                        <div className="px-4 py-3 bg-[var(--bg-card)]/80 backdrop-blur-sm border-b border-[var(--separator-opaque)] flex items-center justify-between sticky top-0 z-10">
                                            <button
                                                onClick={handleBackFromEdit}
                                                className="text-[var(--blue-ios)] text-[17px] flex items-center -ml-2"
                                            >
                                                <ChevronLeft size={24} />
                                                Назад
                                            </button>
                                            <h3 className="text-[17px] font-semibold truncate max-w-[60%]">{editingDraft.title}</h3>
                                            <div className="w-[60px]" /> {/* Spacer for centering */}
                                        </div>

                                        <div className="flex-1 overflow-y-auto">
                                            <div className="p-4 pb-20">
                                                {/* Re-using workers list for current store context (which is set to the draft) */}
                                                <IosSection title={`Сотрудники (${workingWorkers.length})`}>
                                                    {workingWorkers.map((entry, idx) => (
                                                        <div key={entry.workerId} className={idx !== workingWorkers.length - 1 ? "border-b border-[var(--separator)]" : ""}>
                                                            <WorkerRow
                                                                entry={entry}
                                                                onUpdateHours={store.updateHours}
                                                                onToggleStatus={store.toggleWorkerStatus}
                                                                onRemove={store.removeWorker}
                                                                isForeman={entry.workerId === store.foremanId}
                                                            />
                                                        </div>
                                                    ))}
                                                </IosSection>

                                                {notWorkingWorkers.length > 0 && (
                                                    <IosSection title="Не работают">
                                                        {notWorkingWorkers.map((entry, idx) => (
                                                            <div key={entry.workerId} className={idx !== notWorkingWorkers.length - 1 ? "border-b border-[var(--separator)]" : ""}>
                                                                <WorkerRow
                                                                    entry={entry}
                                                                    onUpdateHours={store.updateHours}
                                                                    onToggleStatus={store.toggleWorkerStatus}
                                                                    onRemove={store.removeWorker}
                                                                    isForeman={entry.workerId === store.foremanId}
                                                                />
                                                            </div>
                                                        ))}
                                                    </IosSection>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};
