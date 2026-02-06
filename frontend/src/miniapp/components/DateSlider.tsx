
import { format, addDays, isSameDay } from 'date-fns';
import { ru } from 'date-fns/locale';

export const DateSlider = ({ selectedDate, onSelect }: { selectedDate: Date, onSelect: (date: Date) => void }) => {
    // Generate range: 3 days before, today, 3 days after
    const dates = Array.from({ length: 7 }, (_, i) => addDays(selectedDate, i - 3));

    // Custom 2-letter Russian abbreviations
    const weekDays = ['ВС', 'ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ'];

    return (
        <div className="overflow-x-auto no-scrollbar px-4 pb-2 -mx-4">
            <div className="flex gap-2 justify-center md:justify-center">
                {dates.map((date, i) => {
                    const isSelected = isSameDay(date, selectedDate);
                    const dayOfWeek = weekDays[date.getDay()];
                    const dayNumber = format(date, 'd');

                    return (
                        <button
                            key={i}
                            onClick={() => onSelect(date)}
                            className={`
                                flex flex-col items-center justify-center min-w-[54px] h-[64px] rounded-[12px] transition-all
                                ${isSelected
                                    ? 'bg-[var(--blue-ios)] text-white shadow-sm scale-105'
                                    : 'bg-[var(--bg-card)] text-[var(--text-secondary)]'}
                            `}
                        >
                            <span className={`text-[10px] font-bold uppercase tracking-wide opacity-80 ${isSelected ? 'text-white' : 'text-[var(--text-secondary)]'}`}>
                                {dayOfWeek}
                            </span>
                            <span className={`text-[18px] font-semibold leading-none mt-0.5 ${isSelected ? 'text-white' : 'text-[var(--text-primary)]'}`}>
                                {dayNumber}
                            </span>
                            {isSelected && (
                                <span className="text-[9px] mt-0.5 opacity-80 font-medium">
                                    {format(date, 'MMMM', { locale: ru }).slice(0, 3)}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>
        </div>
    );
};
