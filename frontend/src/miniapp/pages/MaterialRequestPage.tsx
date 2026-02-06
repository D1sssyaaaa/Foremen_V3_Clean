import { useState, useMemo, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { estimateApi, EstimateItem } from '../api/estimates';
import { materialsApi, MaterialRequestCreate, MaterialRequestItemCreate, UrgencyLevel, MaterialType } from '../api/materials';
import { GlassCard, GlassButton } from '../components/ui-glass';
import { Search, Plus, Trash2, AlertTriangle, X, Check, Clock, AlertOctagon } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { clsx } from 'clsx';
import { MiniAppHeader } from '../components/MiniAppHeader';

interface CustomItem {
    id: string;
    name: string;
    unit: string;
    quantity: number;
}

export const MaterialRequestPage = () => {
    const { objectId } = useParams<{ objectId: string }>();
    const navigate = useNavigate();

    // UI State
    const [selection, setSelection] = useState<Record<number, number>>({});
    const [searchQuery, setSearchQuery] = useState('');
    const [urgency, setUrgency] = useState<UrgencyLevel>('normal');
    const [comment, setComment] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Custom Items State
    const [customItems, setCustomItems] = useState<CustomItem[]>([]);
    const [isCustomModalOpen, setIsCustomModalOpen] = useState(false);
    const [newCustomItem, setNewCustomItem] = useState({ name: '', unit: 'шт', quantity: 1 });

    // Data Fetching State
    const [estimateItems, setEstimateItems] = useState<EstimateItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            if (!objectId) return;
            setIsLoading(true);
            try {
                const data = await estimateApi.getEstimateItems(Number(objectId));
                setEstimateItems(data);
            } catch (error) {
                console.error("Failed to load estimate", error);
            } finally {
                setIsLoading(false);
            }
        };
        loadData();
    }, [objectId]);

    // Group items by category
    const groupedItems = useMemo(() => {
        const groups: Record<string, EstimateItem[]> = {};
        estimateItems.forEach(item => {
            const cat = item.category || 'Без категории';
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(item);
        });
        return groups;
    }, [estimateItems]);

    const handleQuantityChange = (id: number, val: number) => {
        setSelection(prev => {
            const next = { ...prev };
            if (val <= 0) delete next[id];
            else next[id] = val;
            return next;
        });
    };

    const addCustomItem = () => {
        if (!newCustomItem.name) return;
        setCustomItems(prev => [...prev, {
            id: `custom-${Date.now()}`,
            name: newCustomItem.name,
            unit: newCustomItem.unit,
            quantity: newCustomItem.quantity
        }]);
        setNewCustomItem({ name: '', unit: 'шт', quantity: 1 });
        setIsCustomModalOpen(false);
    };

    const removeCustomItem = (id: string) => {
        setCustomItems(prev => prev.filter(i => i.id !== id));
    };

    const handleSubmit = async () => {
        if (!objectId) return;
        setIsSubmitting(true);

        try {
            const items: MaterialRequestItemCreate[] = [];

            // Add selected estimate items
            Object.entries(selection).forEach(([idStr, quantity]) => {
                const id = parseInt(idStr);
                const item = estimateItems.find(i => i.id === id);
                if (item) {
                    items.push({
                        material_name: item.name,
                        quantity: quantity,
                        unit: item.unit,
                        description: 'Из сметы'
                    });
                }
            });

            // Add custom items
            customItems.forEach(item => {
                items.push({
                    material_name: item.name,
                    quantity: item.quantity,
                    unit: item.unit,
                    description: 'Дополнительно'
                });
            });

            const requestData: MaterialRequestCreate = {
                cost_object_id: parseInt(objectId),
                material_type: 'regular',
                urgency: urgency,
                items: items,
                comment: comment
            };

            await materialsApi.createRequest(requestData);
            navigate('/miniapp/my-requests'); // Redirect to requests list
        } catch (error) {
            console.error("Failed to create request", error);
            alert("Ошибка при создании заявки");
        } finally {
            setIsSubmitting(false);
        }
    };

    const totalSelected = Object.keys(selection).length + customItems.length;

    if (isLoading) return <div className="flex h-screen items-center justify-center p-4 text-slate-500">Загрузка...</div>;

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-black pb-32 text-slate-900 dark:text-white transition-colors duration-300">
            <MiniAppHeader title="Оформление заявки" />

            <div className="p-4 space-y-6">
                {/* Search */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input
                        type="text"
                        placeholder="Поиск материала..."
                        className="w-full bg-slate-100 dark:bg-[#1C1C1E] h-10 rounded-xl pl-10 pr-4 text-[17px] outline-none placeholder:text-slate-400 dark:text-white dark:placeholder:text-slate-600 transition-colors"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                {/* Urgency Selection */}
                <div className="grid grid-cols-3 gap-2">
                    {[
                        { id: 'normal', label: 'Обычная', icon: Check, color: 'text-green-500' },
                        { id: 'urgent', label: 'Срочно', icon: Clock, color: 'text-orange-500' },
                        { id: 'critical', label: 'Авария', icon: AlertOctagon, color: 'text-red-500' }
                    ].map((opt) => (
                        <button
                            key={opt.id}
                            onClick={() => setUrgency(opt.id as UrgencyLevel)}
                            className={clsx(
                                "flex flex-col items-center justify-center p-3 rounded-xl border transition-all",
                                urgency === opt.id
                                    ? "bg-white dark:bg-[#1C1C1E] border-blue-500 shadow-sm"
                                    : "bg-slate-100 dark:bg-[#1C1C1E] border-transparent opacity-60"
                            )}
                        >
                            <opt.icon size={20} className={clsx("mb-1", opt.color)} />
                            <span className="text-[12px] font-medium">{opt.label}</span>
                        </button>
                    ))}
                </div>

                {/* Comment */}
                <div>
                    <label className="text-[13px] uppercase tracking-wide text-slate-500 font-semibold px-1 mb-2 block">Комментарий</label>
                    <textarea
                        className="w-full bg-white dark:bg-[#1C1C1E] rounded-xl p-3 text-[15px] outline-none border border-slate-200 dark:border-white/10 min-h-[80px]"
                        placeholder="Укажите детали доставки или комментарий..."
                        value={comment}
                        onChange={e => setComment(e.target.value)}
                    />
                </div>

                {/* Custom Items Section */}
                {customItems.length > 0 && (
                    <div className="space-y-2">
                        <h3 className="text-[13px] uppercase tracking-wide text-slate-500 font-semibold px-1">Дополнительно</h3>
                        {customItems.map(item => (
                            <GlassCard key={item.id} className="flex items-center justify-between">
                                <div>
                                    <div className="font-medium text-[16px]">{item.name}</div>
                                    <div className="text-[13px] text-slate-500">{item.quantity} {item.unit}</div>
                                </div>
                                <button
                                    onClick={() => removeCustomItem(item.id)}
                                    className="p-2 text-red-500 bg-red-50 dark:bg-red-500/10 rounded-lg active:opacity-70"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </GlassCard>
                        ))}
                    </div>
                )}

                {/* Estimate Items */}
                {Object.keys(groupedItems).map(cat => {
                    const visibleItems = groupedItems[cat].filter(i => i.name.toLowerCase().includes(searchQuery.toLowerCase()));
                    if (visibleItems.length === 0) return null;

                    return (
                        <div key={cat} className="space-y-2">
                            <h3 className="text-[13px] uppercase tracking-wide text-slate-500 font-semibold px-1">{cat}</h3>
                            <div className="bg-white dark:bg-[#1C1C1E] rounded-xl overflow-hidden shadow-sm border border-slate-200 dark:border-white/10">
                                {visibleItems.map((item, idx) => {
                                    const ordered = selection[item.id] || 0;
                                    const remaining = item.quantity - (item.ordered_quantity || 0);
                                    const isOverLimit = (item.ordered_quantity || 0) + ordered > item.quantity;

                                    return (
                                        <div key={item.id} className={clsx("p-3 flex items-center justify-between", idx !== visibleItems.length - 1 && "border-b border-slate-100 dark:border-white/5")}>
                                            <div className="flex-1 pr-3 min-w-0">
                                                <div className="text-[16px] font-medium leading-snug">{item.name}</div>
                                                <div className="text-[13px] text-slate-500 mt-0.5 flex flex-wrap gap-3">
                                                    <span className={clsx(remaining < 0 && "text-red-500 font-medium")}>
                                                        Ост: {Number(remaining).toLocaleString('ru-RU', { maximumFractionDigits: 3 })} {item.unit}
                                                    </span>
                                                    <span>Всего: {Number(item.quantity).toLocaleString('ru-RU', { maximumFractionDigits: 3 })}</span>
                                                </div>
                                                {isOverLimit && (
                                                    <div className="text-orange-500 text-[11px] font-medium flex items-center mt-1">
                                                        <AlertTriangle size={12} className="mr-1" />
                                                        Превышение лимита
                                                    </div>
                                                )}
                                            </div>

                                            <div className="bg-slate-100 dark:bg-[#2C2C2E] rounded-lg h-9 w-24 flex items-center overflow-hidden">
                                                <input
                                                    type="number"
                                                    inputMode="decimal"
                                                    className="w-full h-full text-center bg-transparent outline-none font-semibold text-[17px] p-0 dark:text-white"
                                                    placeholder="0"
                                                    value={ordered || ''}
                                                    onChange={(e) => handleQuantityChange(item.id, parseFloat(e.target.value))}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })}

                <GlassButton variant="secondary" className="w-full" onClick={() => setIsCustomModalOpen(true)}>
                    <Plus size={20} />
                    Добавить свой материал
                </GlassButton>
            </div>

            {/* Bottom Bar */}
            <AnimatePresence>
                {totalSelected > 0 && (
                    <motion.div
                        initial={{ y: 100 }} animate={{ y: 0 }} exit={{ y: 100 }}
                        className="fixed bottom-0 left-0 right-0 p-4 bg-white/90 dark:bg-black/90 backdrop-blur-xl border-t border-slate-200 dark:border-white/10 pb-safe z-50"
                    >
                        <GlassButton
                            onClick={handleSubmit}
                            disabled={isSubmitting}
                            className="w-full shadow-lg shadow-blue-500/20"
                        >
                            {isSubmitting ? 'Отправка...' : `Оформить заявку (${totalSelected})`}
                        </GlassButton>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Custom Item Modal */}
            <AnimatePresence>
                {isCustomModalOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/40 z-[60] backdrop-blur-sm"
                            onClick={() => setIsCustomModalOpen(false)}
                        />
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
                            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[90%] max-w-sm bg-white dark:bg-[#1C1C1E] rounded-2xl p-5 z-[61] shadow-2xl border border-white/10"
                        >
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-[18px] font-bold">Новый материал</h3>
                                <button onClick={() => setIsCustomModalOpen(false)} className="p-1 bg-slate-100 dark:bg-white/10 rounded-full">
                                    <X size={20} />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-[13px] font-medium text-slate-500 mb-1 block">Название</label>
                                    <input
                                        autoFocus
                                        className="w-full bg-slate-100 dark:bg-[#2C2C2E] h-11 rounded-xl px-3 outline-none focus:ring-2 ring-blue-500/50 transition-all text-[17px] dark:text-white"
                                        value={newCustomItem.name}
                                        onChange={e => setNewCustomItem(prev => ({ ...prev, name: e.target.value }))}
                                        placeholder="Например: Саморезы 50мм"
                                    />
                                </div>
                                <div className="flex gap-3">
                                    <div className="flex-1">
                                        <label className="text-[13px] font-medium text-slate-500 mb-1 block">Кол-во</label>
                                        <input
                                            type="number"
                                            inputMode="decimal"
                                            className="w-full bg-slate-100 dark:bg-[#2C2C2E] h-11 rounded-xl px-3 outline-none focus:ring-2 ring-blue-500/50 transition-all text-[17px] dark:text-white"
                                            value={newCustomItem.quantity}
                                            onChange={e => setNewCustomItem(prev => ({ ...prev, quantity: parseFloat(e.target.value) || 0 }))}
                                        />
                                    </div>
                                    <div className="w-24">
                                        <label className="text-[13px] font-medium text-slate-500 mb-1 block">Ед. изм.</label>
                                        <input
                                            className="w-full bg-slate-100 dark:bg-[#2C2C2E] h-11 rounded-xl px-3 outline-none focus:ring-2 ring-blue-500/50 transition-all text-[17px] dark:text-white"
                                            value={newCustomItem.unit}
                                            onChange={e => setNewCustomItem(prev => ({ ...prev, unit: e.target.value }))}
                                        />
                                    </div>
                                </div>
                                <GlassButton onClick={addCustomItem} disabled={!newCustomItem.name} className="w-full mt-2">
                                    Добавить
                                </GlassButton>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div >
    );
};
