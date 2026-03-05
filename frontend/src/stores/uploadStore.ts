import { create } from 'zustand';
import type { Upload, UploadResponse } from '../types';
import * as api from '../api/client';

interface UploadStore {
  uploads: Upload[];
  current: Upload | null;
  loading: boolean;
  uploading: boolean;
  error: string | null;

  fetchUploads: (customerId?: string) => Promise<void>;
  fetchUpload: (id: string) => Promise<void>;
  upload: (file: File, customerId: string, sourceSystem: string) => Promise<UploadResponse>;
  requestMapping: (uploadId: string) => Promise<void>;
}

export const useUploadStore = create<UploadStore>((set, get) => ({
  uploads: [],
  current: null,
  loading: false,
  uploading: false,
  error: null,

  fetchUploads: async (customerId?: string) => {
    set({ loading: true, error: null });
    try {
      const uploads = await api.listUploads(customerId);
      set({ uploads, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  fetchUpload: async (id: string) => {
    set({ loading: true, error: null });
    try {
      const upload = await api.getUpload(id);
      set({ current: upload, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  upload: async (file, customerId, sourceSystem) => {
    set({ uploading: true, error: null });
    try {
      const result = await api.uploadFile(file, customerId, sourceSystem);
      // Refresh list after upload
      await get().fetchUploads();
      set({ uploading: false });
      return result;
    } catch (e) {
      set({ error: (e as Error).message, uploading: false });
      throw e;
    }
  },

  requestMapping: async (uploadId: string) => {
    set({ loading: true, error: null });
    try {
      await api.mapSchema(uploadId);
      // Refresh the current upload to see status change
      await get().fetchUpload(uploadId);
      set({ loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
      throw e;
    }
  },
}));
