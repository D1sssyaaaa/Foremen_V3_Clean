import { apiClient } from './client';
import type { Notification, NotificationBadge } from '../types/notification';

export const notificationsApi = {
  // Получить все уведомления текущего пользователя
  async getAll(params?: { is_read?: boolean; limit?: number; offset?: number }): Promise<Notification[]> {
    const queryParams = new URLSearchParams();
    // Backend использует unread_only вместо is_read
    if (params?.is_read === false) {
      queryParams.append('unread_only', 'true');
    }
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    
    const queryString = queryParams.toString();
    return apiClient.get<Notification[]>(`/notifications${queryString ? '?' + queryString : ''}`);
  },

  // Получить количество непрочитанных и последние уведомления
  async getBadge(): Promise<NotificationBadge> {
    return apiClient.get<NotificationBadge>('/notifications/badge');
  },

  // Отметить уведомление как прочитанное
  async markAsRead(id: number): Promise<void> {
    await apiClient.post(`/notifications/${id}/read`);
  },

  // Отметить все уведомления как прочитанные
  async markAllAsRead(): Promise<void> {
    await apiClient.post('/notifications/read-all');
  },

  // Удалить уведомление
  async delete(id: number): Promise<void> {
    await apiClient.delete(`/notifications/${id}`);
  },
};
