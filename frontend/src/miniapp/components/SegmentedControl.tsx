import { motion } from "framer-motion";

interface SegmentedControlProps {
    options: { id: number; name: string }[];
    selectedId: number;
    onChange: (id: number, name: string) => void;
}

export const SegmentedControl = ({ options, selectedId, onChange }: SegmentedControlProps) => {
    return (
        <div className="bg-[#E3E3E8] p-0.5 rounded-lg flex relative h-[32px] w-full">
            {options.map((option) => {
                const isSelected = selectedId === option.id;
                return (
                    <button
                        key={option.id}
                        onClick={() => onChange(option.id, option.name)}
                        className={`
                            relative z-10 flex-1 text-[13px] font-medium leading-none transition-colors duration-200
                            ${isSelected ? 'text-black' : 'text-black'}
                        `}
                    >
                        {option.name}

                        {isSelected && (
                            <motion.div
                                layoutId="segmented-tab"
                                className="absolute inset-0 bg-white rounded-[7px] shadow-[0_1px_2px_rgba(0,0,0,0.12),0_0_1px_rgba(0,0,0,0.08)] -z-10 m-[1px]"
                                transition={{ type: "spring", stiffness: 500, damping: 30 }}
                            />
                        )}
                    </button>
                );
            })}
        </div>
    );
};
