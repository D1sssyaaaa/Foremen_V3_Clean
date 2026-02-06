import { apiClient } from '../../api/client';

export interface EstimateItem {
    id: number;
    category: string;
    name: string;
    unit: string;
    quantity: number;
    price?: number;  // Опционально - скрыто для бригадиров
    total_amount?: number;  // Опционально - скрыто для бригадиров
    ordered_quantity?: number;
    delivered_quantity?: number;  // Новое поле
    remaining_quantity?: number;  // Новое поле
}

export const estimateApi = {
    // Get estimate items for an object
    getEstimateItems: async (objectId: number | string): Promise<EstimateItem[]> => {
        try {
            const data = await apiClient.get<EstimateItem[]>(`/objects/${objectId}/estimate`);
            return data;
        } catch (error) {
            console.warn('Using MOCK data for estimate');
            return [
                { id: 1, category: 'Общестроительные работы', name: 'Бетон М300', unit: 'м3', quantity: 150, delivered_quantity: 50, remaining_quantity: 100 },
                { id: 2, category: 'Общестроительные работы', name: 'Арматура A500C d12', unit: 'т', quantity: 5.5, delivered_quantity: 2.0, remaining_quantity: 3.5 },
                { id: 3, category: 'Отделка', name: 'Штукатурка гипсовая', unit: 'меш.', quantity: 200, delivered_quantity: 210, remaining_quantity: -10 },
                { id: 4, category: 'Электрика', name: 'Кабель ВВГнг 3х2.5', unit: 'м', quantity: 1000, delivered_quantity: 0, remaining_quantity: 1000 },
            ];
        }
    }
};
