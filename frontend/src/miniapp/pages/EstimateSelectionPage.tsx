import React, { useState, useEffect } from 'react';
import { IosSection } from '../components/ui-ios';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Check, ChevronRight, FileText, Loader2 } from 'lucide-react';
import { useTimeSheetStore } from '../store/useTimeSheetStore';

interface CostObject {
    id: number;
    name: string;
    description: string;
    status: string;
    material_amount: number;
    contract_amount: number;
}

export const EstimateSelectionPage: React.FC = () => {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(true);
    const [objects, setObjects] = useState<CostObject[]>([]);
    const [error, setError] = useState("");

    // Fetch real objects
    useEffect(() => {
        const fetchObjects = async () => {
            try {
                // Assuming /objects returns list of objects accessible to user (Foreman filtering is on backend)
                const { apiClient } = await import('../../api/client');
                const { data } = await apiClient.get<CostObject[]>('/objects');
                setObjects(data);
            } catch (err) {
                console.error("Failed to load objects", err);
                setError("Не удалось загрузить список объектов");
            } finally {
                setIsLoading(false);
            }
        };
        fetchObjects();
    }, []);

    // Helper to get color/progress (mocked for now as we don't have exact progress calculated yet)
    const getProgressMock = (obj: CostObject) => {
        // Simple heuristic: if active, show some progress
        return obj.status === 'ACTIVE' ? 15 : 0;
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-[var(--bg-ios)]">
                <Loader2 className="w-6 h-6 animate-spin text-[var(--text-secondary)]" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[var(--bg-ios)] font-sans text-[var(--text-primary)]">
            {/* iOS Navigation Bar */}
            <div className="sticky top-0 z-50 bg-[var(--bg-ios)]/90 backdrop-blur-xl border-b border-[var(--separator-opaque)] px-4 pt-3 pb-3">
                <div className="flex items-center justify-between mb-2">
                    <button
                        onClick={() => navigate(-1)}
                        className="flex items-center text-[var(--blue-ios)] active:opacity-60 transition-opacity"
                    >
                        <ArrowLeft size={22} className="mr-1" />
                        <span className="text-[17px]">Назад</span>
                    </button>

                    <h1 className="text-[17px] font-semibold text-[var(--text-primary)] absolute left-1/2 -translate-x-1/2">
                        Выбор объекта
                    </h1>

                    <div className="w-[60px]" /> {/* Spacer */}
                </div>
            </div>

            <div className="p-4">
                <div className="mb-6 text-center">
                    <h2 className="text-2xl font-bold mb-1">Ваши объекты</h2>
                    <p className="text-[var(--text-secondary)] text-[15px]">
                        Выберите объект для создания заявки
                    </p>
                </div>

                {error && (
                    <div className="p-4 mb-4 bg-red-500/10 text-red-500 rounded-lg text-center text-sm">
                        {error}
                    </div>
                )}

                <IosSection>
                    {objects.length === 0 && !error ? (
                        <div className="p-8 text-center text-[var(--text-secondary)]">
                            Нет доступных объектов
                        </div>
                    ) : (
                        objects.map((obj, idx) => (
                            <div key={obj.id} className={idx !== objects.length - 1 ? "border-b border-[var(--separator)]" : ""}>
                                <button
                                    onClick={() => navigate(`/miniapp/estimate/${obj.id}/materials`)}
                                    className="w-full text-left px-4 py-4 bg-[var(--bg-card)] active:bg-[var(--bg-pressed)] transition-colors flex items-center justify-between group"
                                >
                                    <div className="flex items-start gap-3">
                                        <div className={`mt-1 w-8 h-8 rounded-full bg-[var(--blue-ios)]/10 flex items-center justify-center text-[var(--blue-ios)]`}>
                                            <FileText size={18} />
                                        </div>
                                        <div>
                                            <div className="text-[17px] font-semibold text-[var(--text-primary)] mb-0.5">
                                                {obj.name}
                                            </div>
                                            <div className="text-[13px] text-[var(--text-secondary)]">
                                                {obj.status}
                                            </div>
                                        </div>
                                    </div>

                                    <ChevronRight size={20} className="text-[var(--text-third)] opacity-50 group-active:opacity-100" />
                                </button>
                            </div>
                        ))
                    )}
                </IosSection>
            </div>

            {/* Bottom Safe Area */}
            <div className="h-safe-bottom" />
        </div>
    );
};
