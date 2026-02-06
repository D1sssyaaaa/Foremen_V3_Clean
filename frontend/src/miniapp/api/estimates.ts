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
        const data = await apiClient.get<EstimateItem[]>(`/objects/${objectId}/estimate`);
        return data;
    }
};
