import { create } from 'zustand';
import type { CDMField } from '../types';
import * as api from '../api/client';

interface CDMStore {
  fields: CDMField[];
  loading: boolean;
  error: string | null;
  fetchFields: () => Promise<void>;
}

export const useCDMStore = create<CDMStore>((set) => ({
  fields: [],
  loading: false,
  error: null,

  fetchFields: async () => {
    set({ loading: true, error: null });
    try {
      const data = await api.getCDM();
      set({ fields: data.fields, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },
}));
