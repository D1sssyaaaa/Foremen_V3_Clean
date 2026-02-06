import { apiClient } from '../../api/client';

export type MaterialRequestStatus = 'NEW' | 'APPROVED' | 'IN_PROCESSING' | 'ORDERED' | 'PARTIALLY_DELIVERED' | 'SHIPPED' | 'COMPLETED' | 'REJECTED';
export type UrgencyLevel = 'normal' | 'urgent' | 'critical';
export type MaterialType = 'regular' | 'inert';

export interface MaterialRequestItemCreate {
    material_name: string;
    quantity: number;
    unit: string;
    description?: string;
}

export interface MaterialRequestCreate {
    cost_object_id: number;
    material_type: MaterialType;
    urgency: UrgencyLevel;
    expected_delivery_date?: string; // YYYY-MM-DD
    items: MaterialRequestItemCreate[];
    comment?: string;
}

export interface MaterialRequestResponse {
    id: number;
    status: MaterialRequestStatus;
    // ... add other fields if needed for response handling
}

export const materialsApi = {
    // Create new material request
    createRequest: async (data: MaterialRequestCreate): Promise<MaterialRequestResponse> => {
        return await apiClient.post<MaterialRequestResponse>('/material-requests/', data);
    }
};
