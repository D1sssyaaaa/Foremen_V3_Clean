import { apiClient } from '../../api/client';

export interface ObjectListItem {
    id: number;
    name: string;
    code: string;
    status: string;
    customer_name?: string;
}

export const objectsApi = {
    /**
     * Получение списка объектов, назначенных текущему бригадиру
     */
    async getMyObjects(): Promise<ObjectListItem[]> {
        const data = await apiClient.get<ObjectListItem[]>('/objects/my');
        return data;
    }
};
