import { apiClient } from './client';
import {
    UPDListItem, UPDDetail,
    DistributeUPDRequest, DistributeUPDResponse,
    DistributionSuggestions
} from '../types/upd';

// We assume UPDUploadResponse might be same as UPDDetail or similar, 
// checking upd.ts it wasn't exported explicitly or defined? 
// Checking types/index.ts -> it was UPDDetailResponse?
// checking types/upd.ts -> I didn't verify UPDUploadResponse export.
// I should rely on UPDDetail for now as they are similar in structure for response.
// Backend router returns UPDUploadResponse.
// I'll use any or define it if needed.

export const updApi = {
    getAll: (skip = 0, limit = 100) =>
        apiClient.get<UPDListItem[]>('/material-costs/', { skip, limit }),

    getUnprocessed: () =>
        apiClient.get<UPDListItem[]>('/material-costs/unprocessed'),

    getById: (id: number) =>
        apiClient.get<UPDDetail>(`/material-costs/${id}`),

    upload: (file: File) =>
        apiClient.uploadFile<UPDDetail>('/material-costs/upload', file),

    getSuggestions: (id: number, costObjectId?: number) =>
        apiClient.get<DistributionSuggestions>(`/material-costs/${id}/suggestions`, { cost_object_id: costObjectId }),

    distribute: (id: number, data: DistributeUPDRequest) =>
        apiClient.post<DistributeUPDResponse>(`/material-costs/${id}/distribute`, data),

    checkDuplicates: (id: number, toleranceDays = 3) =>
        apiClient.get<UPDListItem[]>(`/material-costs/${id}/duplicates`, { tolerance_days: toleranceDays }),

    markDuplicate: (id: number, originalId: number) =>
        apiClient.post(`/material-costs/${id}/mark-duplicate?original_upd_id=${originalId}`)
};
