import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Package, Clock, CheckCircle, XCircle } from 'lucide-react';
import { IosSection } from '../components/ui-ios';
import { apiClient } from '../../api/client';

interface MaterialRequest {
    id: number;
    object_id: number;
    object_name: string;
    created_at: string;
    status: string;
    items_count: number;
}

export const MyRequestsPage: React.FC = () => {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(true);
    const [requests, setRequests] = useState<MaterialRequest[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadRequests();
    }, []);

    const loadRequests = async () => {
        try {
            setIsLoading(true);
            // TODO: Создать endpoint /material-requests/my
            const data = await apiClient.get<MaterialRequest[]>('/material-requests/my');
            setRequests(data);
        } catch (err) {
            console.error('Failed to load requests', err);
            setError('Не удалось загрузить заявки');
        } finally {
            setIsLoading(false);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'PENDING':
                return <Clock className="w-4 h-4 text-orange-500" />;
            case 'APPROVED':
                return <CheckCircle className="w-4 h-4 text-green-500" />;
            case 'REJECTED':
                return <XCircle className="w-4 h-4 text-red-500" />;
            default:
                return <Clock className="w-4 h-4 text-gray-500" />;
        }
    };

    const getStatusText = (status: string) => {
        switch (status) {
            case 'PENDING':
                return 'На рассмотрении';
            case 'APPROVED':
                return 'Одобрена';
            case 'REJECTED':
                return 'Отклонена';
            default:
                return status;
        }
    };

    // Group by object
    const groupedByObject = requests.reduce((acc, req) => {
        if (!acc[req.object_name]) acc[req.object_name] = [];
        acc[req.object_name].push(req);
        return acc;
    }, {} as Record<string, MaterialRequest[]>);

    return (
        <div className="min-h-screen bg-[var(--bg-ios)] pb-safe-bottom font-sans text-[var(--text-primary)]">
            {/* Header */}
            <div className="sticky top-0 z-50 bg-[var(--bg-ios)]/90 backdrop-blur-xl border-b border-[var(--separator-opaque)] px-4 py-3">
                <div className="flex items-center justify-between">
                    <button onClick={() => navigate(-1)} className="text-[var(--blue-ios)] flex items-center">
                        <ArrowLeft size={22} className="mr-1" /> Назад
                    </button>
                    <h1 className="text-[17px] font-semibold">Мои заявки</h1>
                    <div className="w-[60px]" />
                </div>
            </div>

            {/* Content */}
            <div className="p-4 space-y-6">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-20 text-[var(--text-secondary)]">
                        <Loader2 className="w-8 h-8 animate-spin mb-3" />
                        <p>Загрузка заявок...</p>
                    </div>
                ) : error ? (
                    <div className="text-center py-10 text-red-500">
                        {error}
                    </div>
                ) : requests.length === 0 ? (
                    <div className="text-center py-20 text-[var(--text-secondary)]">
                        <Package className="w-12 h-12 mx-auto mb-3 opacity-30" />
                        <p>Нет заявок</p>
                    </div>
                ) : (
                    Object.keys(groupedByObject).map(objectName => (
                        <div key={objectName}>
                            <h3 className="text-[var(--text-secondary)] text-sm font-medium uppercase tracking-wider mb-2 ml-4">
                                {objectName}
                            </h3>
                            <IosSection>
                                {groupedByObject[objectName].map((req, idx, arr) => (
                                    <div
                                        key={req.id}
                                        className={`p-4 bg-[var(--bg-card)] ${idx !== arr.length - 1 ? 'border-b border-[var(--separator)]' : ''
                                            }`}
                                    >
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="flex-1">
                                                <div className="text-[17px] font-medium leading-snug mb-1">
                                                    Заявка #{req.id}
                                                </div>
                                                <div className="text-[13px] text-[var(--text-secondary)]">
                                                    {new Date(req.created_at).toLocaleDateString('ru', {
                                                        day: 'numeric',
                                                        month: 'long',
                                                        year: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    })}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2 ml-2">
                                                {getStatusIcon(req.status)}
                                                <span className="text-[13px] font-medium">
                                                    {getStatusText(req.status)}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="text-[13px] text-[var(--text-secondary)]">
                                            Позиций: {req.items_count}
                                        </div>
                                    </div>
                                ))}
                            </IosSection>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
