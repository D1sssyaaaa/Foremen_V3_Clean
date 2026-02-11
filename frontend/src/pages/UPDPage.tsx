
import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { updApi } from '../api/updApi';
import type { UPDDocument, UPDDetailResponse, CostObject, DistributionSuggestionItem } from '../types';
import { motion } from 'framer-motion';
import {
  Download,
  Eye,
  ChevronDown,
  ChevronUp,
  Filter,
  MoreVertical,
  FileText,
  AlertTriangle,
  RefreshCw,
  Trash2,
  Calendar,
  Printer,
  Upload,
  Link,
  X,
  Copy,
  Share2,
  ExternalLink,
  AlertCircle, // Kept as it's used
  Split, // Kept as it's used
  Box, // Kept as it's used
  Loader2 // Kept as it's used
} from 'lucide-react';

export function UPDPage() {
  const [upds, setUpds] = useState<UPDDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  // Состояние для expandable rows
  const [expandedRowId, setExpandedRowId] = useState<number | null>(null);
  const [detailsCache, setDetailsCache] = useState<Record<number, UPDDetailResponse>>({});
  const [detailsLoading, setDetailsLoading] = useState<Record<number, boolean>>({});

  // Состояние для распределения
  const [objects, setObjects] = useState<CostObject[]>([]);
  const [distributeModalOpen, setDistributeModalOpen] = useState(false);
  const [selectedUpdForDistribution, setSelectedUpdForDistribution] = useState<number | null>(null);

  // Smart Distribution State
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<DistributionSuggestionItem[]>([]);
  const [distributionDraft, setDistributionDraft] = useState<Record<number, number | null>>({}); // itemId -> objectId

  useEffect(() => {
    loadUPDs();
    loadObjects();
  }, []);

  const loadObjects = async () => {
    try {
      const data = await apiClient.get<CostObject[]>('/objects/');
      setObjects(data);
    } catch (err) {
      console.error('Ошибка загрузки объектов:', err);
    }
  };

  const loadUPDs = async () => {
    try {
      const data = await updApi.getUnprocessed();
      setUpds(data);
    } catch (err: any) {
      setError('Ошибка загрузки УПД');
    } finally {
      setLoading(false);
    }
  };

  const toggleRow = async (id: number) => {
    if (expandedRowId === id) {
      setExpandedRowId(null);
      return;
    }

    setExpandedRowId(id);

    if (!detailsCache[id] && !detailsLoading[id]) {
      setDetailsLoading(prev => ({ ...prev, [id]: true }));
      try {
        const detail = await updApi.getById(id);
        // @ts-ignore
        setDetailsCache(prev => ({ ...prev, [id]: detail }));
      } catch (err) {
        console.error('Ошибка загрузки деталей:', err);
      } finally {
        setDetailsLoading(prev => ({ ...prev, [id]: false }));
      }
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError('');

    try {
      await updApi.upload(file);
      await loadUPDs();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки файла');
    } finally {
      setUploading(false);
    }
  };

  const openDistributeModal = async (id: number, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setSelectedUpdForDistribution(id);
    setDistributeModalOpen(true);
    setLoadingSuggestions(true);
    setSuggestions([]);
    setDistributionDraft({});

    try {
      const [detail, suggestionsData] = await Promise.all([
        detailsCache[id] ? Promise.resolve(detailsCache[id]) : updApi.getById(id),
        updApi.getSuggestions(id)
      ]);

      // @ts-ignore
      if (!detailsCache[id]) setDetailsCache(prev => ({ ...prev, [id]: detail }));

      setSuggestions(suggestionsData.suggestions);

      const initialDraft: Record<number, number | null> = {};

      suggestionsData.suggestions.forEach(s => {
        if (s.suggested_cost_object_id) {
          initialDraft[s.material_cost_item_id] = s.suggested_cost_object_id;
        } else {
          initialDraft[s.material_cost_item_id] = null;
        }
      });

      detail.items.forEach(item => {
        if (initialDraft[item.id] === undefined) {
          initialDraft[item.id] = null;
        }
      });

      setDistributionDraft(initialDraft);

    } catch (err) {
      console.error('Failed to load data for distribution:', err);
      alert('Ошибка загрузки данных для распределения');
      setDistributeModalOpen(false);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleDraftChange = (itemId: number, objectId: number | null) => {
    setDistributionDraft(prev => ({
      ...prev,
      [itemId]: objectId
    }));
  };

  const applyBulkObject = (objectId: number | null) => {
    if (!selectedUpdForDistribution) return;
    const details = detailsCache[selectedUpdForDistribution];
    if (!details) return;

    const newDraft: Record<number, number | null> = {};
    details.items.forEach(item => {
      newDraft[item.id] = objectId;
    });
    setDistributionDraft(newDraft);
  };

  const handleDistributeConfirm = async () => {
    if (!selectedUpdForDistribution) return;
    const details = detailsCache[selectedUpdForDistribution];
    if (!details) return;

    const unassigned = details.items.filter(item => !distributionDraft[item.id]);
    if (unassigned.length > 0) {
      if (!window.confirm(`Не рапределено позиций: ${unassigned.length}.Продолжить ? `)) {
        return;
      }
    }

    const distributions = details.items
      .filter(item => distributionDraft[item.id])
      .map(item => ({
        material_cost_item_id: item.id,
        cost_object_id: distributionDraft[item.id]!,
        distributed_quantity: item.quantity,
        distributed_amount: item.total_with_vat // Using Total with VAT as amount
      }));

    if (distributions.length === 0) {
      alert('Нет позиций для распределения');
      return;
    }

    try {
      await updApi.distribute(selectedUpdForDistribution, { distributions });
      setDistributeModalOpen(false);
      loadUPDs();
    } catch (err: any) {
      console.error('Ошибка распределения:', err);
      alert(err.response?.data?.detail || 'Ошибка при распределении');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NEW': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'DISTRIBUTED': return 'bg-green-100 text-green-700 border-green-200';
      case 'ARCHIVED': return 'bg-gray-100 text-gray-600 border-gray-200';
      case 'ERROR': return 'bg-red-100 text-red-700 border-red-200';
      case 'DUPLICATE': return 'bg-orange-100 text-orange-700 border-orange-200';
      default: return 'bg-gray-100 text-gray-500 border-gray-200';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'NEW': return 'Новый';
      case 'DISTRIBUTED': return 'Распределен';
      case 'ARCHIVED': return 'Архив';
      case 'ERROR': return 'Ошибка';
      case 'DUPLICATE': return 'Дубликат';
      default: return status;
    }
  };

  const getSuggestionForItem = (itemId: number) => {
    return suggestions.find(s => s.material_cost_item_id === itemId);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <Loader2 className="animate-spin text-[var(--blue-ios)]" size={40} />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in pb-20">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">УПД Документы</h1>
          <p className="text-[var(--text-secondary)]">Обработка и распределение поступлений</p>
        </div>
        <label className={`
          flex items-center gap-2 bg-[var(--blue-ios)] text-white px-5 py-2.5 rounded-xl font-medium 
          active:scale-95 transition-transform shadow-sm hover:shadow-md cursor-pointer
          ${uploading ? 'opacity-70 cursor-wait' : ''}
        `}>
          {uploading ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
          <span>{uploading ? 'Загрузка...' : 'Загрузить XML'}</span>
          <input type="file" accept=".xml" onChange={handleFileUpload} disabled={uploading} className="hidden" />
        </label>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-100 text-red-600 p-4 rounded-xl flex items-center gap-3">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {upds.length === 0 ? (
        <div className="bg-[var(--bg-card)] p-10 rounded-2xl border border-[var(--separator)] text-center text-[var(--text-secondary)]">
          <div className="bg-slate-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText size={32} className="text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-[var(--text-primary)]">Нет документов</h3>
          <p>Загрузите первый XML файл УПД для начала работы</p>
        </div>
      ) : (
        <div className="bg-[var(--bg-card)] rounded-2xl shadow-sm border border-[var(--separator)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[var(--bg-ios)] border-b border-[var(--separator-opaque)] text-[var(--text-secondary)] text-sm font-semibold">
                  <th className="p-4 w-12 text-center"></th>
                  <th className="p-4">Документ</th>
                  <th className="p-4">Поставщик</th>
                  <th className="p-4 text-right">Сумма</th>
                  <th className="p-4 text-center">Позиций</th>
                  <th className="p-4 text-center">Статус</th>
                  <th className="p-4 text-center">Действия</th>
                </tr>
              </thead>
              <tbody>
                {upds.map(upd => (
                  <React.Fragment key={upd.id}>
                    <tr
                      onClick={() => toggleRow(upd.id)}
                      className={`
                        border-b border-[var(--separator-opaque)] cursor-pointer transition-colors
                        ${expandedRowId === upd.id ? 'bg-blue-50/50' : 'hover:bg-[var(--bg-ios)]'}
                      `}
                    >
                      <td className="p-4 text-center text-[var(--text-secondary)]">
                        {expandedRowId === upd.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </td>
                      <td className="p-4">
                        <div className="font-medium text-[var(--text-primary)]">№ {upd.document_number}</div>
                        <div className="text-xs text-[var(--text-secondary)]">{new Date(upd.document_date).toLocaleDateString('ru')}</div>
                      </td>
                      <td className="p-4 text-[var(--text-primary)]">{upd.supplier_name}</td>
                      <td className="p-4 text-right font-bold text-[var(--text-primary)] whitespace-nowrap">
                        {upd.total_with_vat.toLocaleString('ru')} ₽
                      </td>
                      <td className="p-4 text-center text-[var(--text-secondary)]">{upd.items_count}</td>
                      <td className="p-4 text-center">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(upd.status)} inline-block`}>
                          {getStatusText(upd.status)}
                        </span>
                      </td>
                      <td className="p-4 text-center">
                        <button
                          onClick={(e) => openDistributeModal(upd.id, e)}
                          disabled={upd.status !== 'NEW'}
                          className={`
                            p-2 rounded-lg transition-colors
                            ${upd.status === 'NEW'
                              ? 'bg-[var(--blue-ios)] text-white hover:bg-blue-600'
                              : 'bg-gray-100 text-gray-400 cursor-not-allowed'}
                          `}
                          title="Распределить"
                        >
                          <Split size={18} />
                        </button>
                      </td>
                    </tr>

                    {/* Expanded Details */}
                    {expandedRowId === upd.id && (
                      <tr className="bg-[var(--bg-ios)]">
                        <td colSpan={7} className="p-4 lg:p-6">
                          {detailsLoading[upd.id] ? (
                            <div className="flex justify-center p-4">
                              <Loader2 className="animate-spin text-[var(--text-secondary)]" />
                            </div>
                          ) : detailsCache[upd.id]?.items ? (
                            <div className="bg-white rounded-xl border border-[var(--separator)] overflow-hidden shadow-sm">
                              <div className="p-3 border-b border-[var(--separator)] bg-gray-50 font-medium text-[var(--text-secondary)] text-sm flex gap-2 items-center">
                                <Box size={16} /> Товары и услуги по документу
                              </div>
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="text-[var(--text-secondary)] border-b border-[var(--separator-opaque)]">
                                    <th className="p-3 text-left">Наименование</th>
                                    <th className="p-3 text-right">Кол-во</th>
                                    <th className="p-3 text-center">Ед.</th>
                                    <th className="p-3 text-right">Цена</th>
                                    <th className="p-3 text-right">Сумма</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-[var(--separator-opaque)]">
                                  {detailsCache[upd.id].items.map((item, idx) => (
                                    <tr key={idx} className="hover:bg-gray-50">
                                      <td className="p-3 text-[var(--text-primary)] max-w-md truncate" title={item.product_name}>{item.product_name}</td>
                                      <td className="p-3 text-right">{item.quantity}</td>
                                      <td className="p-3 text-center text-[var(--text-secondary)]">{item.unit}</td>
                                      <td className="p-3 text-right">{item.price.toLocaleString('ru')}</td>
                                      <td className="p-3 text-right font-medium">{item.total_with_vat.toLocaleString('ru')}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <div className="text-center text-red-500">Не удалось загрузить детали</div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Smart Distribution Modal */}
      {distributeModalOpen && selectedUpdForDistribution && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-[var(--bg-card)] rounded-2xl shadow-2xl max-w-5xl w-full h-[85vh] flex flex-col overflow-hidden border border-[var(--separator)]"
          >
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-[var(--separator)] bg-[var(--bg-card)] shrink-0">
              <div>
                <h2 className="text-xl font-bold text-[var(--text-primary)]">Распределение документа</h2>
                <div className="text-sm text-[var(--text-secondary)] mt-1">
                  УПД № {upds.find(u => u.id === selectedUpdForDistribution)?.document_number} от {new Date(upds.find(u => u.id === selectedUpdForDistribution)?.document_date || '').toLocaleDateString('ru')}
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 bg-[var(--bg-ios)] px-3 py-1.5 rounded-lg border border-[var(--separator-opaque)]">
                  <span className="text-xs text-[var(--text-secondary)]">Для всех:</span>
                  <select
                    onChange={(e) => applyBulkObject(e.target.value ? Number(e.target.value) : null)}
                    className="bg-transparent text-sm font-medium outline-none text-[var(--text-primary)]"
                  >
                    <option value="">-- Выбрать --</option>
                    {objects.map(obj => (
                      <option key={obj.id} value={obj.id}>{obj.name}</option>
                    ))}
                  </select>
                </div>
                <button onClick={() => setDistributeModalOpen(false)} className="p-2 hover:bg-[var(--bg-ios)] rounded-full transition-colors">
                  <X size={24} className="text-[var(--text-secondary)]" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
              {loadingSuggestions ? (
                <div className="h-full flex flex-col items-center justify-center text-[var(--text-secondary)]">
                  <Loader2 className="animate-spin mb-4 text-[var(--blue-ios)]" size={40} />
                  <p>Анализируем номенклатуру и ищем соответствия...</p>
                </div>
              ) : detailsCache[selectedUpdForDistribution] ? (
                <div className="bg-white rounded-xl shadow-sm border border-[var(--separator)] overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-[var(--separator)] sticky top-0 z-10">
                      <tr>
                        <th className="p-4 text-left text-[var(--text-secondary)] font-semibold">Позиция</th>
                        <th className="p-4 text-right text-[var(--text-secondary)] font-semibold w-24">Кол-во</th>
                        <th className="p-4 text-right text-[var(--text-secondary)] font-semibold w-32">Сумма</th>
                        <th className="p-4 text-left text-[var(--text-secondary)] font-semibold w-[350px]">Объект затрат</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--separator-opaque)]">
                      {detailsCache[selectedUpdForDistribution].items.map(item => {
                        const suggestion = getSuggestionForItem(item.id);
                        const currentObjectId = distributionDraft[item.id];
                        // Helper to check if distribution is valid
                        const isValid = (d: any) => d.cost_object_id === currentObjectId && currentObjectId !== null;

                        return (
                          <tr key={item.id} className="hover:bg-blue-50/30 transition-colors">
                            <td className="p-4">
                              <div className="font-medium text-[var(--text-primary)] mb-1">{item.product_name}</div>
                              {suggestion && suggestion.confidence > 0 && (
                                <div className="flex items-center gap-2 mt-1">
                                  <span className={`
                                      text-[10px] px-2 py-0.5 rounded border flex items-center gap-1
                                      ${suggestion.confidence > 80
                                      ? 'bg-green-50 text-green-700 border-green-200'
                                      : 'bg-yellow-50 text-yellow-700 border-yellow-200'}
                                    `}>
                                    AI Match: {Math.round(suggestion.confidence)}%
                                  </span>
                                </div>
                              )}
                            </td>
                            <td className="p-4 text-right align-top pt-5">{item.quantity} {item.unit}</td>
                            <td className="p-4 text-right font-medium align-top pt-5">{item.total_with_vat.toLocaleString('ru')} ₽</td>
                            <td className="p-4 align-top">
                              <div className="relative">
                                <select
                                  value={currentObjectId || ''}
                                  onChange={e => handleDraftChange(item.id, e.target.value ? Number(e.target.value) : null)}
                                  className={`
                                      w-full p-2.5 rounded-lg border outline-none appearance-none cursor-pointer transition-shadow
                                      ${currentObjectId
                                      ? 'bg-blue-50 border-blue-200 text-blue-900 font-medium'
                                      : 'bg-white border-[var(--separator)] text-[var(--text-secondary)]'}
                                      focus:ring-2 focus:ring-[var(--blue-ios)]
                                    `}
                                >
                                  <option value="">-- Не выбрано --</option>
                                  {objects.map(obj => (
                                    <option key={obj.id} value={obj.id}>{obj.name}</option>
                                  ))}
                                </select>
                                <ChevronDown className="absolute right-3 top-3 text-[var(--text-secondary)] pointer-events-none" size={16} />
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center text-red-500 py-10">Ошибка загрузки данных распределения</div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-[var(--separator)] bg-[var(--bg-card)] flex justify-between items-center shrink-0">
              <div className="text-sm text-[var(--text-secondary)]">
                Распределено: <span className="font-bold text-[var(--text-primary)]">
                  {Object.values(distributionDraft).filter(v => v !== null).length}
                </span> из <span>
                  {detailsCache[selectedUpdForDistribution]?.items.length || 0}
                </span>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setDistributeModalOpen(false)}
                  className="px-6 py-3 rounded-xl font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-ios)] transition-colors"
                >
                  Отмена
                </button>
                <button
                  onClick={handleDistributeConfirm}
                  className="px-6 py-3 rounded-xl font-bold text-white bg-[var(--blue-ios)] active:scale-95 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={Object.values(distributionDraft).filter(v => v !== null).length === 0}
                >
                  Подтвердить и сохранить
                </button>
              </div>
            </div>

          </motion.div>
        </div>
      )}
    </div>
  );
}
