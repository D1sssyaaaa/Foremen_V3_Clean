import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Loader2 } from 'lucide-react';
import { objectsApi, ObjectListItem } from '../api/objectsApi';
import { IosSection } from '../components/ui-ios';
import { MiniAppHeader } from '../components/MiniAppHeader';

export const ObjectSelectPage: React.FC = () => {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(true);
    const [objects, setObjects] = useState<ObjectListItem[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadObjects();
    }, []);

    const loadObjects = async () => {
        try {
            setIsLoading(true);
            const data = await objectsApi.getMyObjects();
            setObjects(data);
        } catch (err) {
            console.error('Failed to load objects', err);
            setError('Не удалось загрузить объекты');
        } finally {
            setIsLoading(false);
        }
    };

    const handleObjectClick = (objectId: number) => {
        navigate(`/miniapp/estimate/${objectId}`);
    };

    return (
        <div className="min-h-screen bg-[var(--bg-ios)] pb-safe-bottom font-sans text-[var(--text-primary)]">
            {/* Header */}
            <MiniAppHeader title="Мои объекты" />

            {/* Content */}
            <div className="p-4 space-y-4">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-20 text-[var(--text-secondary)]">
                        <Loader2 className="w-8 h-8 animate-spin mb-3" />
                        <p>Загрузка объектов...</p>
                    </div>
                ) : error ? (
                    <div className="text-center py-10 text-red-500">
                        {error}
                    </div>
                ) : objects.length === 0 ? (
                    <div className="text-center py-20 text-[var(--text-secondary)]">
                        <Building2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
                        <p>Нет назначенных объектов</p>
                    </div>
                ) : (
                    <IosSection>
                        {objects.map((obj, idx) => (
                            <div
                                key={obj.id}
                                onClick={() => handleObjectClick(obj.id)}
                                className={`p-4 bg-[var(--bg-card)] cursor-pointer active:bg-[var(--bg-elevated)] transition-colors ${idx !== objects.length - 1 ? 'border-b border-[var(--separator)]' : ''
                                    }`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="text-[17px] font-medium leading-snug mb-1">
                                            {obj.name}
                                        </div>
                                        <div className="text-[13px] text-[var(--text-secondary)] space-y-0.5">
                                            <div>Код: {obj.code}</div>
                                            {obj.customer_name && (
                                                <div>Заказчик: {obj.customer_name}</div>
                                            )}
                                            <div className="flex items-center mt-1">
                                                <span
                                                    className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium ${obj.status === 'ACTIVE'
                                                        ? 'bg-green-100 text-green-700'
                                                        : 'bg-gray-100 text-gray-700'
                                                        }`}
                                                >
                                                    {obj.status === 'ACTIVE' ? 'Активен' : obj.status}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-[var(--text-third)] ml-2">
                                        <svg width="8" height="13" viewBox="0 0 8 13" fill="currentColor">
                                            <path d="M1.5 1L6.5 6.5L1.5 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                                        </svg>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </IosSection>
                )}
            </div>
        </div>
    );
};
