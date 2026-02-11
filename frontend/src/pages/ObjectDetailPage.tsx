import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Edit2,
  DollarSign,
  Users,
  Activity,
  MessageSquare,
  Send,
  Paperclip,
  Save,
  ExternalLink,
  User,
  Building2,
  Clock,
  X,
  Plus
} from 'lucide-react';
import { objectFields, FieldDefinition } from '../utils/objectFields';

// --- Interfaces ---
// ... (Keep existing interfaces: ObjectStats, CostDetail, etc.)
interface ObjectStats {
  object_id: number;
  object_name: string;
  object_code: string;
  object_status: string;
  material_requests: {
    count: number;
    total: number;
    by_status: Record<string, number>;
  };
  equipment_orders: {
    count: number;
    total: number;
  };
  upd_documents: {
    count: number;
    total: number;
  };
  timesheets: {
    count: number;
    labor_costs_total: number;
  };
  total_costs: number;
  budget: {
    material_budget: number;
    labor_budget: number;
    total_budget: number;
  };
}

interface CostDetail {
  id: number | string;
  date: string | null;
  amount: number;
  description: string;
  document_number?: string;
  type?: string;
  hours?: number;
}

interface CostSummary {
  materials_total: number;
  equipment_deliveries_total: number;
  labor_total: number;
  other_total: number;
  work_total: number;
  grand_total: number;
}

interface ObjectCosts {
  object_id: number;
  object_name: string;
  summary: CostSummary;
  materials: CostDetail[];
  equipment_deliveries: CostDetail[];
  labor: CostDetail[];
  other: CostDetail[];
}

interface EditableObject {
  id: number;
  name: string;
  customer_name: string;
  contract_number: string;
  description: string;
  contract_amount: number;
  material_amount: number;
  labor_amount: number;
  status: string;
}

interface EstimateItem {
  id: number;
  category: string;
  name: string;
  unit: string;
  quantity: number;
  price: number;
  total_amount: number;
  delivered_quantity?: number;
  remaining_quantity?: number;
}

interface TimeSheetItemSimple {
  id: number;
  member_name: string;
  date: string;
  hours: number;
  rate: number | null;
  amount: number | null;
}

interface TimeSheetSummary {
  id: number;
  period_start: string;
  period_end: string;
  brigade_name: string;
  status: string;
  total_hours: number;
  total_amount: number;
  items: TimeSheetItemSimple[];
}

// --- Chat Component (Journal Style) ---
interface ChatMessage {
  id: string;
  sender: string;
  role?: string;
  text: string;
  timestamp: Date;
  isMe: boolean;
}

const ObjectChat = ({ objectId }: { objectId: number }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');

  useEffect(() => {
    const stored = localStorage.getItem(`chat_${objectId}`);
    if (stored) {
      setMessages(JSON.parse(stored).map((m: any) => ({ ...m, timestamp: new Date(m.timestamp) })));
    } else {
      setMessages([
        { id: '1', sender: 'Система', role: 'System', text: 'Объект создан. Начало ведения журнала.', timestamp: new Date(), isMe: false }
      ]);
    }
  }, [objectId]);

  const handleSend = () => {
    if (!inputText.trim()) return;
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: 'Я',
      role: 'Менеджер',
      text: inputText,
      timestamp: new Date(),
      isMe: true
    };
    const updated = [newMessage, ...messages]; // Newest first for Journal feed
    setMessages(updated);
    localStorage.setItem(`chat_${objectId}`, JSON.stringify(updated));
    setInputText('');

    setTimeout(() => {
      const reply: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'Бот',
        role: 'Ассистент',
        text: 'Запись добавлена в журнал.',
        timestamp: new Date(),
        isMe: false
      };
      const withReply = [reply, ...updated];
      setMessages(withReply);
      localStorage.setItem(`chat_${objectId}`, JSON.stringify(withReply));
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl border border-[var(--separator)] overflow-hidden shadow-sm">
      {/* Input Area - Top */}
      <div className="p-4 border-b border-[var(--separator)] bg-[var(--bg-ios)]">
        <div className="flex gap-2">
          <button className="p-2 text-[var(--text-secondary)] hover:text-[var(--blue-ios)] transition-colors rounded-lg hover:bg-white">
            <Paperclip size={20} />
          </button>
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Добавить комментарий или дело..."
              className="w-full bg-white border border-[var(--separator)] rounded-xl pl-4 pr-10 py-2.5 outline-none text-sm focus:ring-2 focus:ring-[var(--blue-ios)] transition-all placeholder:text-gray-400"
            />
            <button
              onClick={handleSend}
              className={`absolute right-1 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-all ${inputText.trim() ? 'text-[var(--blue-ios)] hover:bg-blue-50' : 'text-gray-300'}`}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-0 bg-gray-50/50">
        <div className="divide-y divide-[var(--separator-opaque)]">
          {messages.map(msg => (
            <div key={msg.id} className="p-4 hover:bg-white transition-colors group">
              <div className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ${msg.isMe ? 'bg-[var(--blue-ios)]' : 'bg-gray-400'}`}>
                  {msg.sender[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-baseline mb-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-[var(--text-primary)]">{msg.sender}</span>
                      {msg.role && <span className="text-[10px] uppercase tracking-wide text-[var(--text-secondary)] font-medium border border-gray-200 px-1.5 rounded">{msg.role}</span>}
                    </div>
                    <span className="text-xs text-[var(--text-secondary)] whitespace-nowrap">
                      {msg.timestamp.toLocaleString('ru', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{msg.text}</div>

                  {/* Actions */}
                  <div className="flex gap-4 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="text-xs text-[var(--blue-ios)] font-medium hover:underline">Ответить</button>
                    <button className="text-xs text-[var(--text-secondary)] hover:text-red-500">Удалить</button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        {messages.length === 0 && (
          <div className="p-8 text-center text-[var(--text-secondary)]">
            <MessageSquare size={32} className="mx-auto mb-2 opacity-20" />
            <p>История пуста</p>
          </div>
        )}
      </div>
    </div>
  );
};

// --- Info Panel Component ---
// ... (Keep existing Info Panel mostly the same, just styling tweaks if needed)
const ObjectInfoPanel = ({ objectId }: { objectId: number }) => {
  const [fields, setFields] = useState<FieldDefinition[]>([]);
  const [values, setValues] = useState<Record<string, any>>({});
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    setFields(objectFields.getFields());
    const stored = localStorage.getItem(`info_${objectId}`);
    if (stored) {
      setValues(JSON.parse(stored));
    }
  }, [objectId]);

  const handleSave = () => {
    localStorage.setItem(`info_${objectId}`, JSON.stringify(values));
    setIsEditing(false);
  };

  const handleChange = (id: string, val: any) => {
    setValues(prev => ({ ...prev, [id]: val }));
  };

  const renderValue = (field: FieldDefinition) => {
    const val = values[field.id];
    if (!val) return <span className="text-[var(--text-secondary)] italic text-xs">Не заполнено</span>;

    if (field.type === 'link') {
      return (
        <a href={val} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-[var(--blue-ios)] hover:underline break-all">
          <ExternalLink size={12} /> <span className="truncate">{field.label === 'Фото с объекта' ? 'Альбом' : 'Файл'}</span>
        </a>
      );
    }
    return <span className="text-[var(--text-primary)] font-medium text-sm">{val}</span>;
  };

  return (
    <div className="bg-white rounded-2xl border border-[var(--separator)] overflow-hidden shadow-sm flex flex-col mb-4">
      <div className="p-3 bg-gray-50 border-b border-[var(--separator)] flex justify-between items-center">
        <h3 className="font-bold text-sm text-[var(--text-primary)]">Дополнительно</h3>
        <button
          onClick={() => isEditing ? handleSave() : setIsEditing(true)}
          className={`p-1.5 rounded-md transition-all ${isEditing ? 'bg-[var(--blue-ios)] text-white shadow-sm' : 'hover:bg-white hover:shadow-sm text-[var(--text-secondary)]'}`}
        >
          {isEditing ? <Save size={14} /> : <Edit2 size={14} />}
        </button>
      </div>

      <div className="p-4 space-y-4">
        {fields.map(field => (
          <div key={field.id} className="group">
            <div className="text-[10px] uppercase tracking-wider text-[var(--text-secondary)] mb-1 font-semibold">{field.label}</div>

            {isEditing ? (
              field.type === 'select' ? (
                <select
                  value={values[field.id] || ''}
                  onChange={e => handleChange(field.id, e.target.value)}
                  className="w-full p-2 rounded-lg border border-[var(--separator)] bg-[var(--bg-ios)] text-xs outline-none focus:ring-1 focus:ring-[var(--blue-ios)]"
                >
                  <option value="">Не выбрано</option>
                  {field.options?.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                </select>
              ) : (
                <div className="relative">
                  <input
                    type={field.type === 'number' ? 'number' : 'text'}
                    value={values[field.id] || ''}
                    onChange={e => handleChange(field.id, e.target.value)}
                    placeholder={field.placeholder || ''}
                    className="w-full p-2 rounded-lg border border-[var(--separator)] bg-[var(--bg-ios)] text-xs outline-none focus:ring-1 focus:ring-[var(--blue-ios)]"
                  />
                </div>
              )
            ) : (
              <div className="min-h-[16px] text-sm">
                {renderValue(field)}
              </div>
            )}
          </div>
        ))}

        {fields.length === 0 && (
          <div className="text-center text-[var(--text-secondary)] text-xs py-2">
            Нет полей
          </div>
        )}
      </div>
    </div>
  );
};

// --- Participants Panel ---
const ParticipantsPanel = ({ object }: { object: EditableObject | null }) => {
  return (
    <div className="bg-white rounded-2xl border border-[var(--separator)] overflow-hidden shadow-sm flex flex-col">
      <div className="p-3 bg-gray-50 border-b border-[var(--separator)] flex justify-between items-center">
        <h3 className="font-bold text-sm text-[var(--text-primary)]">Участники</h3>
        <button className="text-[var(--text-secondary)] hover:text-[var(--blue-ios)]"><Plus size={16} /></button>
      </div>
      <div className="divide-y divide-[var(--separator-opaque)]">
        <div className="p-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center"><Building2 size={16} /></div>
          <div>
            <div className="text-xs font-bold text-[var(--text-secondary)]">Заказчик</div>
            <div className="text-sm font-medium text-[var(--text-primary)]">{object?.customer_name || 'Не указан'}</div>
          </div>
        </div>
        <div className="p-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-100 text-[var(--blue-ios)] flex items-center justify-center"><User size={16} /></div>
          <div>
            <div className="text-xs font-bold text-[var(--text-secondary)]">Менеджер</div>
            <div className="text-sm font-medium text-[var(--text-primary)]">Текущий Пользователь</div>
          </div>
        </div>
      </div>
    </div>
  )
};

export function ObjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const objectId = id ? parseInt(id, 10) : 0;

  // Data States
  const [stats, setStats] = useState<ObjectStats | null>(null);
  const [costs, setCosts] = useState<ObjectCosts | null>(null);
  const [objectDetails, setObjectDetails] = useState<EditableObject | null>(null);
  const [loading, setLoading] = useState(true);

  // Tabs: 'work' (Journal/Chat), 'finances' (Summary+Estimate), 'docs' (Files/Est)
  // User wanted standard layout. Let's keep meaningful tabs but rename.
  const [activeTab, setActiveTab] = useState<'journal' | 'finances' | 'labor'>('journal');

  // Sub-states
  const [estimateItems, setEstimateItems] = useState<EstimateItem[]>([]);
  const [loadingEstimate, setLoadingEstimate] = useState(false);
  const [timesheetSummaries, setTimesheetSummaries] = useState<TimeSheetSummary[]>([]);
  const [loadingTimesheets, setLoadingTimesheets] = useState(false);
  const [selectedTimesheet, setSelectedTimesheet] = useState<TimeSheetSummary | null>(null);

  useEffect(() => {
    if (objectId) {
      loadAllData();
    }
  }, [objectId]);

  useEffect(() => {
    // Lazy load tab data
    if (activeTab === 'finances' && estimateItems.length === 0) {
      loadEstimate();
    }
    if (activeTab === 'labor' && timesheetSummaries.length === 0) {
      loadTimesheets();
    }
  }, [activeTab]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [statsData, costsData, detailsData] = await Promise.all([
        apiClient.get<ObjectStats>(`/objects/${objectId}/stats`),
        apiClient.get<ObjectCosts>(`/objects/${objectId}/costs`),
        apiClient.get<EditableObject>(`/objects/${objectId}`)
      ]);
      setStats(statsData);
      setCosts(costsData);
      setObjectDetails(detailsData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadEstimate = async () => {
    setLoadingEstimate(true);
    try {
      const data = await apiClient.get<EstimateItem[]>(`/objects/${objectId}/estimate`);
      setEstimateItems(data);
    } catch { } finally { setLoadingEstimate(false); }
  };

  const loadTimesheets = async () => {
    setLoadingTimesheets(true);
    try {
      const data = await apiClient.get<TimeSheetSummary[]>(`/objects/${objectId}/timesheets`);
      setTimesheetSummaries(data);
    } catch { } finally { setLoadingTimesheets(false); }
  };


  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'bg-green-100 text-green-700';
      case 'PREPARATION_TO_CLOSE': return 'bg-amber-100 text-amber-700';
      case 'CLOSED': return 'bg-gray-100 text-gray-600';
      default: return 'bg-gray-100 text-gray-500';
    }
  };

  if (loading || !stats) return <div className="flex h-screen items-center justify-center"><div className="animate-spin text-[var(--blue-ios)]"><Activity size={40} /></div></div>;

  const estimateTotal = estimateItems.reduce((sum, item) => sum + item.total_amount, 0);
  const groupedEstimate = estimateItems.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, EstimateItem[]>);

  return (
    <div className="animate-fade-in pb-10 max-w-[1600px] mx-auto min-h-screen flex flex-col">
      {/* 1. Slim CRM Header */}
      <div className="bg-white border-b border-[var(--separator)] px-6 py-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 sticky top-0 z-10 backdrop-blur-md bg-white/90">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/objects')} className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
            <ArrowLeft size={22} />
          </button>

          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-[var(--text-primary)]">{stats.object_name}</h1>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${getStatusColor(stats.object_status)}`}>
                {stats.object_status === 'ACTIVE' ? 'В работе' : stats.object_status}
              </span>
              <span className="text-xs text-[var(--text-secondary)] bg-gray-100 px-2 py-0.5 rounded font-mono">
                {stats.object_code}
              </span>
            </div>
            <div className="text-sm text-[var(--text-secondary)] flex items-center gap-4 mt-1">
              <span className="flex items-center gap-1"><Building2 size={12} /> {objectDetails?.customer_name || 'Заказчик не указан'}</span>
              <span className="flex items-center gap-1"><Clock size={12} /> Обновлено сегодня</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs (Top Right or Center) */}
        <div className="flex bg-[var(--bg-ios)] p-1 rounded-lg">
          {[
            { id: 'journal', label: 'Журнал', icon: MessageSquare },
            { id: 'finances', label: 'Финансы', icon: DollarSign },
            { id: 'labor', label: 'Работы', icon: Users },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`
                        flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold transition-all
                        ${activeTab === tab.id
                  ? 'bg-white text-[var(--text-primary)] shadow-sm'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}
                    `}
            >
              <tab.icon size={16} /> {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Main Layout - Grid */}
      <div className="flex-1 p-6">
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 h-full">

          {/* LEFT COLUMN: Main Content (3/4 width) */}
          <div className="xl:col-span-3 min-h-[500px]">
            {activeTab === 'journal' && (
              <ObjectChat objectId={objectId} />
            )}

            {activeTab === 'finances' && (
              <div className="space-y-6">
                {/* KPI Cards (Moved here) */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-white p-4 rounded-xl border border-[var(--separator)] shadow-sm">
                    <div className="text-[var(--text-secondary)] text-xs font-bold uppercase">Бюджет</div>
                    <div className="text-xl font-bold mt-1 text-[var(--text-primary)]">{stats.budget.total_budget.toLocaleString('ru')} ₽</div>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-[var(--separator)] shadow-sm">
                    <div className="text-[var(--text-secondary)] text-xs font-bold uppercase">Расход</div>
                    <div className="text-xl font-bold mt-1 text-[var(--text-primary)]">{stats.total_costs.toLocaleString('ru')} ₽</div>
                  </div>
                  <div className={`p-4 rounded-xl border shadow-sm ${(stats.budget.total_budget - stats.total_costs) >= 0 ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                    <div className="text-[var(--text-secondary)] text-xs font-bold uppercase">Остаток</div>
                    <div className={`text-xl font-bold mt-1 ${(stats.budget.total_budget - stats.total_costs) >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                      {(stats.budget.total_budget - stats.total_costs).toLocaleString('ru')} ₽
                    </div>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-[var(--separator)] shadow-sm">
                    <div className="text-[var(--text-secondary)] text-xs font-bold uppercase">Рентабельность</div>
                    <div className="text-xl font-bold mt-1 text-purple-600">
                      {stats.budget.total_budget > 0 ? Math.round(((stats.budget.total_budget - stats.total_costs) / stats.budget.total_budget) * 100) : 0}%
                    </div>
                  </div>
                </div>

                {/* Cost Structure */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white rounded-2xl border border-[var(--separator)] p-6">
                    <h3 className="font-bold mb-4">Структура расходов</h3>
                    {/* Simple Visual Bars */}
                    {costs && (
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between text-sm mb-1"><span>Материалы</span> <span className="font-medium">{costs.summary.materials_total.toLocaleString('ru')} ₽</span></div>
                          <div className="h-2 bg-gray-100 rounded-full overflow-hidden"><div className="h-full bg-blue-500" style={{ width: `${Math.min((costs.summary.materials_total / stats.budget.material_budget) * 100, 100)}%` }}></div></div>
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1"><span>Работы (ФОТ)</span> <span className="font-medium">{costs.summary.work_total.toLocaleString('ru')} ₽</span></div>
                          <div className="h-2 bg-gray-100 rounded-full overflow-hidden"><div className="h-full bg-orange-500" style={{ width: `${Math.min((costs.summary.work_total / stats.budget.labor_budget) * 100, 100)}%` }}></div></div>
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1"><span>Техника</span> <span className="font-medium">{costs.summary.equipment_deliveries_total.toLocaleString('ru')} ₽</span></div>
                          <div className="h-2 bg-gray-100 rounded-full overflow-hidden"><div className="h-full bg-purple-500" style={{ width: '50%' }}></div></div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Estimate Mini View */}
                  <div className="bg-white rounded-2xl border border-[var(--separator)] p-6">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="font-bold">Смета</h3>
                      <span className="text-xs bg-gray-100 px-2 py-1 rounded">{estimateTotal.toLocaleString('ru')} ₽</span>
                    </div>
                    <div className="max-h-[300px] overflow-y-auto pr-2">
                      {estimateItems.length === 0 ? <button onClick={loadEstimate} className="text-blue-500 text-sm">Загрузить смету</button> : (
                        <div className="space-y-2">
                          {Object.keys(groupedEstimate).map(cat => (
                            <div key={cat} className="text-sm border-b pb-2">
                              <div className="font-medium text-gray-700">{cat}</div>
                              <div className="text-[var(--text-secondary)] text-xs">{groupedEstimate[cat].length} позиций</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'labor' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {timesheetSummaries.map(ts => (
                  <div key={ts.id} onClick={() => setSelectedTimesheet(ts)} className="bg-white p-4 rounded-xl border border-[var(--separator)] cursor-pointer hover:border-[var(--blue-ios)] transition-all shadow-sm">
                    <div className="font-bold mb-1">{ts.brigade_name}</div>
                    <div className="text-xs text-[var(--text-secondary)] mb-3">
                      {new Date(ts.period_start).toLocaleDateString('ru')} - {new Date(ts.period_end).toLocaleDateString('ru')}
                    </div>
                    <div className="flex justify-between items-end">
                      <div className="text-sm">{ts.total_hours} ч.</div>
                      <div className="font-bold text-[var(--blue-ios)]">{ts.total_amount.toLocaleString('ru')} ₽</div>
                    </div>
                  </div>
                ))}
                {timesheetSummaries.length === 0 && !loadingTimesheets && <div className="col-span-3 text-center text-gray-400 py-10">Нет данных о работах</div>}
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: Sidebar (1/4 width) */}
          <div className="xl:col-span-1 space-y-6">
            {/* 3. Additional Information Panel */}
            <ObjectInfoPanel objectId={objectId} />

            {/* 4. Participants Panel */}
            <ParticipantsPanel object={objectDetails} />
          </div>

        </div>
      </div>

      {/* Timesheet Details Modal */}
      {selectedTimesheet && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedTimesheet(null)}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-[var(--bg-card)] rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            {/* ... (Same modal content as before) ... */}
            <div className="p-5 border-b flex justify-between">
              <h3 className="font-bold">Детали табеля</h3>
              <button onClick={() => setSelectedTimesheet(null)}><X size={20} /></button>
            </div>
            <div className="p-4 overflow-y-auto">
              {selectedTimesheet.items.map(i => (
                <div key={i.id} className="flex justify-between py-2 border-b last:border-0 border-gray-100">
                  <span>{i.member_name}</span>
                  <span className="font-medium">{i.hours} ч.</span>
                  <span className="text-gray-500">{i.amount?.toLocaleString('ru')} ₽</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
