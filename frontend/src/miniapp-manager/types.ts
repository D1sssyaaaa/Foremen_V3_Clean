export interface ObjectPortfolioItem {
    object_id: number;
    object_name: string;
    contract_amount?: number;
    total_costs: number;
    labor_costs: number;
    material_costs: number;
    equipment_costs: number;
    other_costs: number;
    // Computed on frontend or backend
    budget_utilization_percent?: number;
    status?: 'ok' | 'warning' | 'danger';
}

export interface PortfolioSummary {
    period_start: string;
    period_end: string;
    total_cost: number;
    total_profit?: number; // Estimated
    objects_summary: ObjectPortfolioItem[];
}
