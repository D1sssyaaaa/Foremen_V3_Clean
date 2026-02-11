// Типы для авторизации
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export interface User {
  id: number;
  username: string;
  phone: string;
  email: string | null;
  full_name: string | null;
  birth_date?: string | null;
  profile_photo_url?: string | null;
  roles: string[];
  telegram_chat_id: string | null;
  is_active: boolean;
}

// Роли пользователей
export enum UserRole {
  ADMIN = 'ADMIN',
  MANAGER = 'MANAGER',
  ACCOUNTANT = 'ACCOUNTANT',
  HR_MANAGER = 'HR_MANAGER',
  MATERIALS_MANAGER = 'MATERIALS_MANAGER',
  PROCUREMENT_MANAGER = 'PROCUREMENT_MANAGER',
  EQUIPMENT_MANAGER = 'EQUIPMENT_MANAGER',
}

// Объекты учета
export interface CostObject {
  id: number;
  name: string;
  code: string;
  contract_number: string | null;
  contract_amount: number | null;
  material_amount?: number | null;
  labor_amount?: number | null;
  start_date: string | null;
  end_date: string | null;
  status?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  customer_name?: string | null;
  stats?: {
    plan: { materials: number; labor: number; total: number };
    fact: { materials: number; labor: number; total: number };
    balance: { materials: number; labor: number; total: number };
    margin_pct: { materials: number; labor: number };
  };
}

// УПД
// УПД
export * from './upd';

// Заявки на материалы
export interface MaterialRequest {
  id: number;
  cost_object_id: number;
  cost_object_name: string;
  foreman_id: number | null;
  foreman_name: string | null;
  number: string | null;
  status: string;
  material_type: 'regular' | 'inert';
  urgency: string | null;
  delivery_address: string | null;
  items_count: number;
  items?: {
    id: number;
    name: string;
    quantity: number;
    unit: string;
  }[];
  author_id?: number;
  created_at: string;
  updated_at: string;
}

// Табели РТБ
export interface TimeSheet {
  id: number;
  brigade_id: number;
  brigade_name: string;
  period_start: string;
  period_end: string;
  status: string;
  number: string | null;
  total_hours: number | null;
  total_amount: number | null;
  items_count: number;
  created_at: string;
  updated_at: string;
}

// Аналитика
export interface CostAnalytics {
  object_id: number;
  object_name: string;
  total_costs: number;
  material_costs: number;
  equipment_costs: number;
  labor_costs: number;
  period_start: string;
  period_end: string;
}

export interface ObjectCostSummary {
  object_id: number;
  object_name: string;
  total_labor_cost: number;
  total_equipment_cost: number;
  total_material_cost: number;
  total_cost: number;
  contract_amount: number | null;
  remaining_budget: number | null;
  budget_utilization_percent: number | null;
  planned_labor_cost: number | null;
  planned_material_cost: number | null;
}
