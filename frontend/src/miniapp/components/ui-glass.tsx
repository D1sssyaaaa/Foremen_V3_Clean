import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { motion } from "framer-motion";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Modern Card (Solid White/Dark, Clean Shadow)
export const GlassCard = ({ children, className, onClick }: { children: React.ReactNode, className?: string, onClick?: () => void }) => (
    <motion.div
        whileTap={onClick ? { scale: 0.99 } : undefined}
        onClick={onClick}
        className={cn(
            "bg-white dark:bg-[#1C1C1E] rounded-xl border border-slate-200 dark:border-white/10 shadow-sm p-4",
            "transition-all duration-200 hover:shadow-md",
            "text-slate-900 dark:text-white",
            onClick ? "cursor-pointer active:border-blue-300 dark:active:border-blue-500" : "",
            className
        )}
    >
        {children}
    </motion.div>
);

// Modern Button (Vibrant, accessible)
export const GlassButton = ({ children, onClick, variant = 'primary', className, disabled }: any) => {
    const variants = {
        primary: "bg-blue-600 hover:bg-blue-700 text-white shadow-sm shadow-blue-200 dark:shadow-none",
        secondary: "bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-sm dark:bg-[#2C2C2E] dark:text-white dark:border-white/10 dark:hover:bg-[#3A3A3C]",
        danger: "bg-white hover:bg-red-50 text-red-500 border border-red-200 dark:bg-[#2C2C2E] dark:border-red-500/30 dark:text-red-400"
    };

    return (
        <motion.button
            whileTap={{ scale: 0.97 }}
            disabled={disabled}
            onClick={onClick}
            className={cn(
                "rounded-xl px-5 py-3 font-semibold text-[15px] transition-all duration-200 flex items-center justify-center gap-2",
                "disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none",
                variants[variant as keyof typeof variants],
                className
            )}
        >
            {children}
        </motion.button>
    );
};
