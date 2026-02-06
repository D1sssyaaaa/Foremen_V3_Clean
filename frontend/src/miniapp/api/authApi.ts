import { apiClient } from '../../api/client';

export interface TelegramAuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export const authApi = {
    /**
     * Авторизация через Telegram Mini App
     * @param initData - строка initData от Telegram WebApp
     */
    async loginWithTelegram(initData: string): Promise<TelegramAuthResponse> {
        const data = await apiClient.post<TelegramAuthResponse>('/auth/telegram', {
            init_data: initData
        });
        return data;
    }
};
