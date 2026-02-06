
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface TimeEntryPayload {
    worker_id: number;
    hours: number;
}

export const timesheetApi = {
    submit: async (date: string, objectId: number, entries: TimeEntryPayload[]) => {
        // date string should be YYYY-MM-DD
        return axios.post(`${API_URL}/api/v2/timesheets/submit`, {
            date,
            object_id: objectId,
            entries
        });
    }
};
