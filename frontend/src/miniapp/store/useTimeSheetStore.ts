import { create } from 'zustand';


export interface TimeEntryLocal {
    workerId: number;
    fullName: string;
    hours: number;
    isOvertime: boolean;
    isVisible: boolean; // For "Did Not Work" logic (instead of removing, we hide or mark)
    // Actually, "otseit" (filter out) means they shouldn't be in the report.
    // But for UI, maybe we keep them in a "Removed" list?
    // Let's use a flag isWorking: boolean. If false, they are visually different or moved to bottom.
    isWorking: boolean;
}

interface TimeSheetState {
    currentDate: Date;
    selectedObjectId: number | null;

    entries: TimeEntryLocal[];
    drafts: Record<string, TimeEntryLocal[]>;

    // Brigade State (Base Team)
    brigade: { id: number, fullName: string }[];
    // Foreman State
    foremanId: number | null;
    foremanProfile: {
        fullName: string;
        phone: string;
        birthDate: string; // ISO string YYYY-MM-DD
    };

    // Actions
    setDate: (date: Date) => void;
    setObjectId: (id: number) => void;
    setForemanId: (id: number) => void;
    updateForemanProfile: (profile: Partial<{ fullName: string; phone: string; birthDate: string }>) => void;

    // Worker Actions
    updateHours: (workerId: number, delta: number) => void;
    setHours: (workerId: number, hours: number) => void;
    addWorker: (worker: { id: number, fullName: string }) => void; // Adds to current view AND brigade? No, separate.
    removeWorker: (workerId: number) => void; // Removes from current view
    updateWorkerName: (workerId: number, newName: string) => void;
    toggleWorkerStatus: (workerId: number) => void; // The new "Did Not Work" button

    // Brigade Actions
    addToBrigade: (worker: { id: number, fullName: string }) => void;
    removeFromBrigade: (workerId: number) => void;

    reset: () => void;

    // Internal Helper
    saveCurrentToDraft: () => void;
    loadDraftForCurrentContext: () => void;
    removeDraft: (date: Date, objectId: number) => void;
}

const getDraftKey = (date: Date, objectId: number | null) => {
    if (!objectId) return null;
    return `${date.toDateString()}:${objectId}`;
};

export const useTimeSheetStore = create<TimeSheetState>((set, get) => ({
    currentDate: new Date(),
    selectedObjectId: null,

    entries: [],
    drafts: {},
    foremanId: null,
    foremanProfile: {
        fullName: "",
        phone: "",
        birthDate: ""
    },
    brigade: [
        { id: 101, fullName: "Алексей Волков" },
        { id: 102, fullName: "Иван Петров" },
        { id: 103, fullName: "Сергей Смирнов" }
    ], // Default Mock Brigade

    saveCurrentToDraft: () => {
        const { currentDate, selectedObjectId, entries, drafts } = get();
        const key = getDraftKey(currentDate, selectedObjectId);
        if (key) { // Save even if empty? Maybe.
            set({ drafts: { ...drafts, [key]: entries } });
        }
    },

    loadDraftForCurrentContext: () => {
        const { currentDate, selectedObjectId, drafts, brigade } = get();
        const key = getDraftKey(currentDate, selectedObjectId);

        if (key && drafts[key]) {
            // Found draft -> Load it
            set({ entries: drafts[key] });
        } else {
            // No draft -> Auto-populate from Brigade
            const initialEntries: TimeEntryLocal[] = brigade.map(b => ({
                workerId: b.id,
                fullName: b.fullName,
                hours: 8,
                isOvertime: false,
                isWorking: true, // Default to working
                isVisible: true
            }));
            set({ entries: initialEntries });
        }
    },

    setDate: (date) => {
        get().saveCurrentToDraft();
        set({ currentDate: date });
        get().loadDraftForCurrentContext();
    },

    setObjectId: (id) => {
        get().saveCurrentToDraft();
        set({ selectedObjectId: id });
        get().loadDraftForCurrentContext();
    },

    setForemanId: (id) => set({ foremanId: id }),

    updateForemanProfile: (profile) => set((state) => {
        const newProfile = { ...state.foremanProfile, ...profile };
        // If name changes, update foreman in brigade and entries too?
        // User requested profile edit. Usually this should propagate.
        let newBrigade = state.brigade;
        let newEntries = state.entries;

        if (profile.fullName && state.foremanId) {
            newBrigade = state.brigade.map(b => b.id === state.foremanId ? { ...b, fullName: profile.fullName! } : b);
            newEntries = state.entries.map(e => e.workerId === state.foremanId ? { ...e, fullName: profile.fullName! } : e);
        }

        return {
            foremanProfile: newProfile,
            brigade: newBrigade,
            entries: newEntries
        };
    }),

    updateHours: (workerId, delta) => set((state) => {
        const newEntries = state.entries.map(e => {
            if (e.workerId === workerId) {
                let newHours = e.hours + delta;
                newHours = Math.max(0, Math.min(24, newHours)); // Clamp
                return {
                    ...e,
                    hours: newHours,
                    isOvertime: newHours > 8,
                    isWorking: true // If updating hours, assume working
                };
            }
            return e;
        });
        // Auto-save on update? better to save on context switch, but for safety lets sync
        // actually, let's keep entries as "current view" and only sync to draft on switch or unmount
        // but if we crash/reload, we lose it.
        // For now, simple context switch save is enough as per user request.
        return { entries: newEntries };
    }),

    setHours: (workerId, hours) => set((state) => {
        const newEntries = state.entries.map(e =>
            e.workerId === workerId ? { ...e, hours, isOvertime: hours > 8, isWorking: true } : e
        );
        return { entries: newEntries };
    }),

    addWorker: (worker) => set((state) => {
        if (state.entries.find(e => e.workerId === worker.id)) return state;
        const newEntry: TimeEntryLocal = {
            workerId: worker.id,
            fullName: worker.fullName,
            hours: 8,
            isOvertime: false,
            isWorking: true,
            isVisible: true
        };
        return { entries: [...state.entries, newEntry] };
    }),

    removeWorker: (workerId) => set((state) => ({
        entries: state.entries.filter(e => e.workerId !== workerId)
    })),

    updateWorkerName: (workerId, newName) => set((state) => ({
        entries: state.entries.map(e =>
            e.workerId === workerId ? { ...e, fullName: newName } : e
        ),
        brigade: state.brigade.map(b =>
            b.id === workerId ? { ...b, fullName: newName } : b
        )
    })),

    toggleWorkerStatus: (workerId) => set((state) => ({
        entries: state.entries.map(e => {
            if (e.workerId === workerId) {
                // If marks as NOT working, zero hours? Or just flag?
                // User said "otseit" (filter out).
                // Let's toggle flag. UI will decide how to show.
                return { ...e, isWorking: !e.isWorking };
            }
            return e;
        })
    })),

    addToBrigade: (worker) => set((state) => {
        if (state.brigade.find(b => b.id === worker.id)) return state;

        // Also add to current entries if not present
        const newBrigade = [...state.brigade, worker];
        let newEntries = state.entries;

        if (!state.entries.find(e => e.workerId === worker.id)) {
            const newEntry: TimeEntryLocal = {
                workerId: worker.id,
                fullName: worker.fullName,
                hours: 8,
                isOvertime: false,
                isWorking: true,
                isVisible: true
            };
            newEntries = [...state.entries, newEntry];
        }

        return {
            brigade: newBrigade,
            entries: newEntries
        };
    }),

    removeFromBrigade: (workerId) => set((state) => ({
        brigade: state.brigade.filter(b => b.id !== workerId)
    })),

    removeDraft: (date, objectId) => {
        const { currentDate, selectedObjectId, drafts } = get();
        const key = getDraftKey(date, objectId);

        if (key && drafts[key]) {
            const newDrafts = { ...drafts };
            delete newDrafts[key];

            // If deleting current view, reset entries?
            // Only if date and object match current context
            const isCurrent = date.toDateString() === currentDate.toDateString() && objectId === selectedObjectId;

            set({ drafts: newDrafts });

            if (isCurrent) {
                // Determine what "reset" means. Empty list? Or reload from brigade (default)?
                // Probably default from brigade
                get().loadDraftForCurrentContext(); // This will default to brigade if draft missing
            }
        }
    },

    reset: () => set({ entries: [], drafts: {} }) // Clear all? Or just current? User might want to clear just current.
}));
