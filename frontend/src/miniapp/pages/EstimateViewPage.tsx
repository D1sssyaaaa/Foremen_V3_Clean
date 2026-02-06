import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Search, Loader2, Package } from 'lucide-react';
import { estimateApi, EstimateItem } from '../api/estimates';
import { IosSection, IosButton } from '../components/ui-ios';
import { MiniAppHeader } from '../components/MiniAppHeader';

export const EstimateViewPage: React.FC = () => {
    const navigate = useNavigate();
    const { objectId } = useParams<{ objectId: string }>();
    const [isLoading, setIsLoading] = useState(true);
    const [items, setItems] = useState<EstimateItem[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (objectId) {
            loadEstimate();
        }
    }, [objectId]);

    const loadEstimate = async () => {
        if (!objectId) return;

        try {
            setIsLoading(true);
            const data = await estimateApi.getEstimateItems(objectId);
            setItems(data);
        } catch (err) {
            console.error('Failed to load estimate', err);
            setError('Не удалось загрузить смету');
        } finally {
            setIsLoading(false);
        }
    };

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

    const handleCreateRequest = () => {
        navigate(`/miniapp/material-request/${objectId}`);
    };

    return (
        <div className="min-h-screen bg-[var(--bg-ios)] pb-24 font-sans text-[var(--text-primary)]">
            {/* Header */}
            <MiniAppHeader title="Смета объекта" />

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

            {/* Content */}
            <div className="p-4 space-y-6">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-20 text-[var(--text-secondary)]">
                        <Loader2 className="w-8 h-8 animate-spin mb-3" />
                        <p>Загрузка сметы...</p>
                    </div>
                ) : error ? (
                    <div className="text-center py-10 text-red-500">
                        {error}
                    </div>
                ) : items.length === 0 ? (
                    <div className="text-center py-20 text-[var(--text-secondary)]">
                        <Package className="w-12 h-12 mx-auto mb-3 opacity-30" />
                        <p>Смета не загружена</p>
                    </div>
                ) : (
                    filteredCategories.map(cat => (
                        <div key={cat}>
                            <h3 className="text-[var(--text-secondary)] text-sm font-medium uppercase tracking-wider mb-2 ml-4">
                                {cat || 'Без категории'}
                            </h3>
                            <IosSection className="overflow-hidden">
                                {groupedItems[cat]
                                    .filter(item => item.name.toLowerCase().includes(searchQuery.toLowerCase()))
                                    .map((item, idx, arr) => {
                                        const remaining = (item.remaining_quantity || 0);
                                        const isLow = remaining < item.quantity * 0.2; // Меньше 20%

                                        return (
                                            <div
                                                key={item.id}
                                                className={`p-4 bg-[var(--bg-card)] ${idx !== arr.length - 1 ? 'border-b border-[var(--separator)]' : ''
                                                    } ${remaining < 0 ? 'bg-red-50 dark:bg-red-100 dark:text-black' : ''}`}
                                            >
                                                <div className="mb-2">
                                                    <div className="text-[17px] font-medium leading-snug">
                                                        {item.name}
                                                    </div>
                                                </div>

                                                <div className="grid grid-cols-2 gap-2 text-[13px]">
                                                    <div>
                                                        <span className={`${remaining < 0 ? 'text-[var(--text-secondary)] dark:text-black/70' : 'text-[var(--text-secondary)]'}`}>По смете:</span>
                                                        <div className="font-medium">
                                                            {Number(item.quantity).toLocaleString('ru-RU', { maximumFractionDigits: 3 })} {item.unit}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <span className={`${remaining < 0 ? 'text-[var(--text-secondary)] dark:text-black/70' : 'text-[var(--text-secondary)]'}`}>Отгружено:</span>
                                                        <div className="font-medium">
                                                            {Number(item.delivered_quantity || 0).toLocaleString('ru-RU', { maximumFractionDigits: 3 })} {item.unit}
                                                        </div>
                                                    </div>
                                                    <div className="col-span-2">
                                                        <span className={`${remaining < 0 ? 'text-[var(--text-secondary)] dark:text-black/70' : 'text-[var(--text-secondary)]'}`}>Остаток:</span>
                                                        <div
                                                            className={`font-semibold ${remaining < 0
                                                                ? 'text-red-600 dark:text-red-900'
                                                                : isLow
                                                                    ? 'text-orange-600'
                                                                    : 'text-green-600'
                                                                }`}
                                                        >
                                                            {Number(remaining).toLocaleString('ru-RU', { maximumFractionDigits: 3 })} {item.unit}
                                                            {remaining < 0 && ' (перерасход!)'}
                                                        </div>
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

            {/* Bottom Button */}
            {
                !isLoading && !error && items.length > 0 && (
                    <div className="fixed bottom-0 left-0 right-0 p-4 bg-[var(--bg-card)] border-t border-[var(--separator-opaque)] pb-safe-bottom z-50">
                        <IosButton
                            variant="primary"
                            size="lg"
                            className="w-full"
                            onClick={handleCreateRequest}
                        >
                            Создать заявку на материал
                        </IosButton>
                    </div>
                )
            }
        </div >
    );
};
