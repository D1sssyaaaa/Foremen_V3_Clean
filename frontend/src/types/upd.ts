export interface UPDItem {
    id: number;
    product_name: string;
    quantity: number;
    unit: string;
    price: number;
    amount: number;
    vat_rate: number;
    vat_amount: number;
    total_with_vat: number;
    okei_code?: string;
}

export interface ParsingIssue {
    severity: string;
    element: string;
    message: string;
    generator?: string;
    value?: string;
}

export interface UPDListItem {
    id: number;
    document_number: string;
    document_date: string; // ISO date string
    supplier_name: string;
    total_with_vat: number;
    items_count: number;
    status: 'NEW' | 'DISTRIBUTED' | 'ARCHIVED' | 'DUPLICATE' | 'ERROR';
    created_at: string;
}

// Alias for compatibility with existing code
export type UPDDocument = UPDListItem & {
    xml_file_path?: string;
    generator?: string;
    parsing_issues_count?: number;
};
export type UPDDetailResponse = UPDDetail;

export interface UPDDetail extends UPDListItem {
    supplier_inn?: string;
    buyer_name?: string;
    buyer_inn?: string;
    total_amount: number;
    total_vat: number;
    xml_file_path: string;
    generator?: string;
    format_version?: string;
    items: UPDItem[];
    parsing_issues: ParsingIssue[];
    updated_at: string;
}

export interface DistributionSuggestionItem {
    material_cost_item_id: number;
    product_name: string;
    suggested_estimate_item_id: number | null;
    suggested_cost_object_id?: number | null;
    suggested_cost_object_name?: string | null;
    confidence: number;
    source: string | null;
    matched_name: string | null;
}

export interface DistributionSuggestions {
    upd_id: number;
    suggestions: DistributionSuggestionItem[];
}

export interface DistributionItemCreate {
    material_cost_item_id: number;
    material_request_id?: number | null;
    cost_object_id?: number | null;
    distributed_quantity: number;
    distributed_amount: number;
}

export interface DistributeUPDRequest {
    distributions: DistributionItemCreate[];
}

export interface DistributeUPDResponse {
    upd_id: number;
    new_status: string;
    total_distributed_amount: number;
    distributions_count: number;
    cost_entries_created: number;
}
