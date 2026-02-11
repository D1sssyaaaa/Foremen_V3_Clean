import axios, { AxiosError, AxiosInstance } from 'axios';
import type { LoginRequest, TokenResponse, User } from '../types';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    const baseURL = import.meta.env.VITE_API_URL
      ? `${import.meta.env.VITE_API_URL}/api/v1`
      : '/api/v1';

    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Загрузка токенов из localStorage
    this.loadTokens();

    // Interceptor для добавления токена к запросам
    this.client.interceptors.request.use((config) => {
      if (this.accessToken) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });

    // Interceptor для обработки 401 ошибок
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && originalRequest && !originalRequest.headers['X-Retry']) {
          // Попытка обновить токен
          try {
            await this.refreshAccessToken();
            originalRequest.headers['X-Retry'] = 'true';
            return this.client(originalRequest);
          } catch {
            this.logout();
            console.warn('Redirect to login disabled for testing');
            // window.location.href = '/login';
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private loadTokens() {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  private saveTokens(access: string, refresh: string) {
    this.accessToken = access;
    this.refreshToken = refresh;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }

  async login(credentials: LoginRequest): Promise<User> {
    const { data } = await this.client.post<TokenResponse>('/auth/login', credentials);
    this.saveTokens(data.access_token, data.refresh_token);
    return this.getCurrentUser();
  }

  async refreshAccessToken(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error('No refresh token');
    }

    const { data } = await this.client.post<TokenResponse>('/auth/refresh', {
      refresh_token: this.refreshToken,
    });

    this.saveTokens(data.access_token, data.refresh_token);
  }

  async getCurrentUser(): Promise<User> {
    const { data } = await this.client.get<User>('/auth/me');
    return data;
  }

  logout() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  // Методы для работы с API
  async get<T>(url: string, params?: any): Promise<T> {
    const { data } = await this.client.get<T>(url, { params });
    return data;
  }

  async post<T>(url: string, body?: any): Promise<T> {
    const { data } = await this.client.post<T>(url, body);
    return data;
  }

  async put<T>(url: string, body?: any): Promise<T> {
    const { data } = await this.client.put<T>(url, body);
    return data;
  }

  async patch<T>(url: string, body?: any): Promise<T> {
    const { data } = await this.client.patch<T>(url, body);
    return data;
  }

  async delete<T>(url: string): Promise<T> {
    const { data } = await this.client.delete<T>(url);
    return data;
  }

  async uploadFile<T>(url: string, file: File, additionalData?: any): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    if (additionalData) {
      Object.keys(additionalData).forEach(key => {
        const value = additionalData[key];
        if (value !== undefined && value !== null) {
          // Handle non-string values specifically if needed, but append generally converts to string
          formData.append(key, value instanceof Blob ? value : String(value));
        }
      });
    }

    const { data } = await this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return data;
  }
}

export const apiClient = new ApiClient();
