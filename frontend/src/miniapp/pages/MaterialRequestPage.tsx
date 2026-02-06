import React, { useState, useEffect } from 'react';
import { IosSection, IosButton, IosCard } from '../components/ui-ios';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Plus, Search, CheckCircle2, AlertTriangle, Package } from 'lucide-react';
import { estimateApi, EstimateItem } from '../api/estimates';

interface SelectionState {
    [itemId: number]: number; // itemId -> quantity to order
}

export const MaterialRequestPage: React.FC = () => {
    const navigate = useNavigate();
    const { id } = useParams<{ id: string }>();
    const [isLoading, setIsLoading] = useState(true);
    const [items, setItems] = useState<EstimateItem[]>([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [selection, setSelection] = useState<SelectionState>({});

    useEffect(() => {
        const loadItems = async () => {
            if (!id) return;
            try {
                // TODO: Replace with real ID from params
                const data = await estimateApi.getEstimateItems(id);
                setItems(data);
            } catch (error) {
                console.error("Failed to load estimate items", error);
            } finally {
                setIsLoading(false);
            }
        };
        loadItems();
    }, [id]);

    // Group items by category
    const groupedItems = items.reduce((acc, item) => {
        if (!acc[item.category]) acc[item.category] = [];
        acc[item.category].push(item);
        return acc;
    }, {} as Record<string, EstimateItem[]>);

    const filteredCategories = Object.keys(groupedItems).filter(cat =>
        cat.toLowerCase().includes(searchQuery.toLowerCase()) ||
        groupedItems[cat].some(item => item.name.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const handleQuantityChange = (itemId: number, qty: number) => {
        if (qty <= 0) {
            const newSel = { ...selection };
            delete newSel[itemId];
            setSelection(newSel);
        } else {
            setSelection({ ...selection, [itemId]: qty });
        }
    };

    const getStatusColor = (item: EstimateItem, orderQty: number) => {
        const total = (item.ordered_quantity || 0) + orderQty;
        if (total > item.quantity) return "text-red-500";
        if (total === item.quantity) return "text-green-500";
        return "text-[var(--text-primary)]";
    };

    const totalSelected = Object.keys(selection).length;

    return (
        <div className="min-h-screen bg-[var(--bg-ios)] pb-24 font-sans text-[var(--text-primary)]">
            {/* Header */}
            <div className="sticky top-0 z-50 bg-[var(--bg-ios)]/90 backdrop-blur-xl border-b border-[var(--separator-opaque)] px-4 py-3">
                <div className="flex items-center justify-between mb-2">
                    <button onClick={() => navigate(-1)} className="text-[var(--blue-ios)] flex items-center">
                        <ArrowLeft size={22} className="mr-1" /> Back
                    </button>
                    <h1 className="text-[17px] font-semibold">Заявка на материал</h1>
                    <div className="w-[60px]" />
                </div>

                {/* Search */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-secondary)]" />
                    <input
                        type="text"
                        placeholder="Поиск материала..."
                        className="w-full bg-[var(--bg-elevated)] rounded-lg pl-9 pr-4 py-2 text-[15px] outline-none"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {/* List */}
            <div className="p-4 space-y-6">
                {isLoading ? (
                    <div className="text-center py-10 text-[var(--text-secondary)]">Загрузка сметы...</div>
                ) : (
                    filteredCategories.map(cat => (
                        <div key={cat}>
                            <h3 className="text-[var(--text-secondary)] text-sm font-medium uppercase tracking-wider mb-2 ml-4">
                                {cat || "Без категории"}
                            </h3>
                            <IosSection className="overflow-hidden">
                                {groupedItems[cat]
                                    .filter(item => item.name.toLowerCase().includes(searchQuery.toLowerCase()))
                                    .map((item, idx, arr) => {
                                        const currentOrder = selection[item.id] || 0;
                                        const remaining = item.quantity - (item.ordered_quantity || 0);
                                        const isOverLimit = (item.ordered_quantity || 0) + currentOrder > item.quantity;

                                        return (
                                            <div key={item.id} className={`p-4 bg-[var(--bg-card)] ${idx !== arr.length - 1 ? 'border-b border-[var(--separator)]' : ''}`}>
                                                <div className="flex justify-between items-start mb-2">
                                                    <div className="flex-1 pr-2">
                                                        <div className="text-[17px] font-medium leading-snug">{item.name}</div>
                                                        <div className="text-[13px] text-[var(--text-secondary)] mt-1">
                                                            Остаток по смете: <span className={remaining < 0 ? 'text-red-500' : ''}>{remaining} {item.unit}</span>
                                                        </div>
                                                    </div>
                                                    <div className="text-right">
                                                        {isOverLimit && (
                                                            <div className="flex items-center text-red-500 text-[11px] font-medium mb-1 justify-end">
                                                                <AlertTriangle size={12} className="mr-1" />
                                                                Превышение
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="flex items-center justify-between mt-3">
                                                    <div className="text-[13px] text-[var(--text-third)]">
                                                        Всего: {item.quantity} {item.unit}
                                                    </div>

                                                    {/* Stepper */}
                                                    <div className="flex items-center bg-[var(--bg-elevated)] rounded-lg p-1">
                                                        <button
                                                            className="w-8 h-8 flex items-center justify-center text-[var(--text-primary)] active:opacity-50"
                                                            onClick={() => handleQuantityChange(item.id, currentOrder - 1)}
                                                            disabled={currentOrder <= 0}
                                                        >
                                                            -
                                                        </button>
                                                        <input
                                                            type="number"
                                                            className="w-12 text-center bg-transparent outline-none font-semibold text-[17px]"
                                                            value={currentOrder || ''}
                                                            placeholder="0"
                                                            onChange={(e) => handleQuantityChange(item.id, parseFloat(e.target.value) || 0)}
                                                        />
                                                        <button
                                                            className="w-8 h-8 flex items-center justify-center text-[var(--blue-ios)] active:opacity-50"
                                                            onClick={() => handleQuantityChange(item.id, currentOrder + 1)}
                                                        >
                                                            +
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                            </IosSection>
                        </div>
                    ))
                )}
            </div>

            {/* Bottom Bar */}
            {totalSelected > 0 && (
                <div className="fixed bottom-0 left-0 right-0 p-4 bg-[var(--bg-card)] border-t border-[var(--separator-opaque)] pb-safe-bottom z-50">
                    <div className="flex justify-between items-center mb-3">
                        <span className="text-[15px] text-[var(--text-secondary)]">
                            Выбрано позиций: {totalSelected}
                        </span>
                    </div>
                    <IosButton
                        variant="primary"
                        size="lg"
                        className="w-full"
                        onClick={() => console.log("Submit", selection)}
                    >
                        Оформить заявку
                    </IosButton>
                </div>
            )}
        </div>
    );
};
