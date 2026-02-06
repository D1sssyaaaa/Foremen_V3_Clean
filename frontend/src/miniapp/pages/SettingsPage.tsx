import { useState } from 'react';
import { useTimeSheetStore } from '../store/useTimeSheetStore';
import { IosSection, IosInputRow, IosListRow, IosButton } from '../components/ui-ios';
import { ChevronLeft, Plus, Trash2 } from 'lucide-react';

export const SettingsPage = ({ onBack }: { onBack: () => void }) => {
    const store = useTimeSheetStore();
    const [newWorkerName, setNewWorkerName] = useState('');
    const [profile, setProfile] = useState(store.foremanProfile);

    const handleAddWorker = () => {
        if (newWorkerName.trim()) {
            store.addToBrigade({ id: Date.now(), fullName: newWorkerName.trim() });
            setNewWorkerName('');
        }
    };

    const formatPhoneNumber = (value: string) => {
        // Remove non-digits
        const digits = value.replace(/\D/g, '');
        // Ensure starts with 7
        if (!digits.startsWith('7')) {
            if (digits.startsWith('8')) return '+7' + digits.slice(1);
            return '+7' + digits;
        }

        // Format: +7 999 111 22 33
        let formatted = '+7';
        if (digits.length > 1) formatted += ' ' + digits.slice(1, 4);
        if (digits.length > 4) formatted += ' ' + digits.slice(4, 7);
        if (digits.length > 7) formatted += ' ' + digits.slice(7, 9);
        if (digits.length > 9) formatted += ' ' + digits.slice(9, 11);

        return formatted;
    };

    const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;
        // If user is deleting and current is "+7", allow clear? Or enforce? 
        // User asked "always substituted +7", so enforce.
        if (val.length < 2) {
            setProfile(p => ({ ...p, phone: '+7' }));
            return;
        }
        const formatted = formatPhoneNumber(val);
        setProfile(p => ({ ...p, phone: formatted }));
    };

    const handleSaveProfile = () => {
        store.updateForemanProfile(profile);
        onBack();
    };

    // Ensure phone starts with +7 on mount/init if empty
    if (!profile.phone) {
        // modifying state during render is bad, better use useEffect or init in useState. 
        // But for now, we handle it in Input value or init.
    }

    return (
        <div className="min-h-screen bg-[var(--bg-ios)]">
            {/* iOS Navigation Bar */}
            <div className="bg-[var(--bg-ios)]/90 backdrop-blur-md border-b border-[var(--separator-opaque)] sticky top-0 z-50">
                <div className="h-[44px] flex items-center px-2 relative justify-center">
                    <button
                        onClick={onBack}
                        className="absolute left-2 flex items-center text-[var(--blue-ios)] hover:opacity-70 transition-opacity"
                    >
                        <ChevronLeft size={26} strokeWidth={2} className="-ml-1" />
                        <span className="text-[17px] font-normal leading-none pb-0.5">Табель</span>
                    </button>

                    <h1 className="text-[17px] font-semibold text-[var(--text-primary)]">Настройки</h1>
                </div>
            </div>

            <div className="pt-6 pb-24">
                {/* Profile Section */}
                <IosSection title="ЛИЧНЫЕ ДАННЫЕ" footer="Эти данные используются для формирования табеля.">
                    <IosInputRow
                        label="ФИО"
                        value={profile.fullName}
                        onChange={(e: any) => setProfile(p => ({ ...p, fullName: e.target.value }))}
                        placeholder="Иванов Иван Иванович"
                    />
                    <div className="border-t border-[var(--separator)]" />
                    <IosInputRow
                        label="Телефон"
                        type="tel"
                        value={profile.phone}
                        onChange={handlePhoneChange}
                        placeholder="+7 999 000 00 00"
                    />
                    <div className="border-t border-[var(--separator)]" />
                    <IosInputRow
                        label="Дата рождения"
                        type="date"
                        value={profile.birthDate}
                        onChange={(e: any) => {
                            setProfile(p => ({ ...p, birthDate: e.target.value }));
                            // Removed auto-save on date change to be consistent with button
                        }}
                    />
                </IosSection>

                {/* Brigade Section */}
                <IosSection title="СОСТАВ БРИГАДЫ">
                    <div className="flex items-center px-4 py-2 bg-[var(--bg-card)]">
                        <input
                            type="text"
                            value={newWorkerName}
                            onChange={(e) => setNewWorkerName(e.target.value)}
                            placeholder="Добавить нового работника"
                            className="flex-1 text-[17px] py-1 outline-none placeholder-[var(--text-secondary)]/50 bg-transparent text-[var(--text-primary)]"
                            onKeyDown={(e) => e.key === 'Enter' && handleAddWorker()}
                        />
                        <button
                            onClick={handleAddWorker}
                            className="w-8 h-8 rounded-full bg-[var(--bg-pressed)] flex items-center justify-center text-[var(--blue-ios)] ml-2"
                        >
                            <Plus size={20} />
                        </button>
                    </div>
                </IosSection>

                {/* Brigade List */}
                <IosSection>
                    {store.brigade.length === 0 ? (
                        <div className="p-4 text-center text-[var(--text-secondary)]">Список пуст</div>
                    ) : (
                        store.brigade.map((worker, idx) => (
                            <div key={worker.id} className={idx !== store.brigade.length - 1 ? "border-b border-[var(--separator)]" : ""}>
                                <IosListRow>
                                    <span className="text-[17px] text-[var(--text-primary)]">{worker.fullName}</span>
                                    {worker.id !== store.foremanId && (
                                        <button
                                            onClick={() => store.removeFromBrigade(worker.id)}
                                            className="text-[#FF3B30]"
                                        >
                                            <Trash2 size={20} />
                                        </button>
                                    )}
                                </IosListRow>
                            </div>
                        ))
                    )}
                </IosSection>

                <div className="px-6 mt-4">
                    <IosButton onClick={handleSaveProfile}>Сохранить</IosButton>
                </div>
            </div>
        </div>
    );
};
