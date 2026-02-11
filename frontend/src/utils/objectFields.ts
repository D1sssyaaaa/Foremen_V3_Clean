export interface FieldDefinition {
    id: string;
    label: string;
    type: 'text' | 'number' | 'select' | 'date' | 'link' | 'user';
    options?: string[]; // For select
    required?: boolean;
    placeholder?: string;
}

const DEFAULT_FIELDS: FieldDefinition[] = [
    { id: 'payment_form', label: 'Форма оплаты', type: 'select', options: ['Наличные', 'Безнал (с НДС)', 'Безнал (без НДС)'] },
    { id: 'material_markup', label: 'Наценка на материал', type: 'select', options: ['Розница', 'Опт', 'Крупный опт'] },
    { id: 'primary_cp', label: 'Первичное КП', type: 'link', placeholder: 'Ссылка на файл' },
    { id: 'contract', label: 'Договор', type: 'link', placeholder: 'Ссылка на файл' },
    { id: 'closing_docs', label: 'Закрывающие документы', type: 'link', placeholder: 'Ссылка на папку' },
    { id: 'k_estimate', label: 'К-смета', type: 'text' },
    { id: 'project', label: 'Проект', type: 'link', placeholder: 'Ссылка на проект' },
    { id: 'address', label: 'Адрес объекта', type: 'text' },
    { id: 'object_type', label: 'Тип объекта', type: 'text' },
    { id: 'photo', label: 'Фото с объекта', type: 'link', placeholder: 'Ссылка на фотоальбом' },
    { id: 'foreman', label: 'Бригадир', type: 'user' },
    { id: 'material_calc', label: 'Расчет и учет материала', type: 'text' },
];

const STORAGE_KEY = 'object_fields_config';

export const objectFields = {
    getFields: (): FieldDefinition[] => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored) : DEFAULT_FIELDS;
        } catch {
            return DEFAULT_FIELDS;
        }
    },

    saveFields: (fields: FieldDefinition[]) => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(fields));
    },

    resetDefaults: () => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_FIELDS));
        return DEFAULT_FIELDS;
    }
};
