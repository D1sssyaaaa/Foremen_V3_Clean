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
        try {
            const data = await apiClient.get<ObjectListItem[]>('/objects/my');
            return data;
        } catch (error) {
            console.warn('Using MOCK data for objects');
            return [
                { id: 1, name: 'ЖК "Перспектива"', code: 'OBJ-001', status: 'ACTIVE', customer_name: 'ОАО "Застройщик"' },
                { id: 2, name: 'Бизнес-центр "Сити"', code: 'OBJ-002', status: 'ACTIVE', customer_name: 'ООО "Инвест Групп"' },
                { id: 3, name: 'Частный дом (Горки)', code: 'OBJ-003', status: 'CLOSED', customer_name: 'Иванов И.И.' },
            ];
        }
    }
};
