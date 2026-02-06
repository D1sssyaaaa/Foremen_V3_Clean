import { motion } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// 1. IOS SECTION (Inset Grouped)
// The fundamental building block of iOS Settings/Lists
export const IosSection = ({ children, title, footer, className }: { children: React.ReactNode, title?: string, footer?: string, className?: string }) => (
    <div className={cn("mb-6", className)}>
        {title && (
            <div className="px-4 pb-2 text-[13px] text-[var(--text-secondary)] uppercase tracking-wide font-normal ml-1">
                {title}
            </div>
        )}
        <div className="bg-[var(--bg-card)] overflow-hidden md:rounded-xl rounded-xl border border-[var(--separator)] shadow-sm relative mx-4">
            <div className="divide-y divide-[var(--separator)]">
                {children}
            </div>
        </div>
        {footer && (
            <div className="px-5 pt-2 text-[13px] text-[var(--text-secondary)] font-normal leading-tight">
                {footer}
            </div>
        )}
    </div>
);

// 2. IOS LIST ROW
// A single row in a section. Handles the "press" state elegantly.
export const IosListRow = ({ children, onClick, className }: { children: React.ReactNode, onClick?: () => void, className?: string }) => {
    return (
        <motion.div
            whileTap={onClick ? { backgroundColor: "var(--bg-pressed)" } : undefined}
            onClick={onClick}
            className={cn(
                "px-4 py-3 bg-[var(--bg-card)] flex items-center justify-between min-h-[44px]",
                onClick ? "cursor-pointer" : "", // Removed active:bg-gray-100 as motion handles it, or use CSS var
                className
            )}
        >
            {children}
        </motion.div>
    );
};

// 3. IOS BUTTON (Filled & Plain)
export const IosButton = ({ children, onClick, variant = 'filled', disabled, className }: any) => {
    const variants = {
        filled: "bg-[var(--blue-ios)] text-white font-semibold rounded-[14px] active:opacity-80",
        plain: "text-[var(--blue-ios)] font-normal active:opacity-50",
        destructive: "bg-[var(--bg-card)] text-[#FF3B30] font-normal active:bg-[var(--bg-pressed)]"
    };

    return (
        <motion.button
            whileTap={{ scale: 0.98 }}
            disabled={disabled}
            onClick={onClick}
            className={cn(
                "flex items-center justify-center transition-all duration-200",
                variant === 'filled' ? "w-full py-3.5 text-[17px]" : "text-[17px]",
                "disabled:opacity-40 disabled:cursor-not-allowed",
                variants[variant as keyof typeof variants],
                className
            )}
        >
            {children}
        </motion.button>
    );
};

// 4. IOS INPUT ROW
export const IosInputRow = ({ label, value, onChange, type = "text", placeholder }: any) => (
    <div className="flex items-center justify-between px-4 py-3 bg-[var(--bg-card)]">
        <span className="text-[17px] text-[var(--text-primary)] min-w-[100px]">{label}</span>
        <input
            type={type}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            className="flex-1 text-[17px] text-right text-[var(--blue-ios)] placeholder-[#C7C7CC] outline-none bg-transparent"
        />
    </div>
);
