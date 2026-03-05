import { create } from 'zustand';
import type { SchemaMapping, ReviewDetail, ReviewDecision } from '../types';
import * as api from '../api/client';

interface ReviewStore {
  pending: SchemaMapping[];
  completed: SchemaMapping[];
  currentDetail: ReviewDetail | null;
  loading: boolean;
  submitting: boolean;
  error: string | null;

  fetchPending: () => Promise<void>;
  fetchCompleted: () => Promise<void>;
  fetchDetail: (mappingId: string) => Promise<void>;
  submitDecision: (decision: ReviewDecision) => Promise<string>;
}

export const useReviewStore = create<ReviewStore>((set, get) => ({
  pending: [],
  completed: [],
  currentDetail: null,
  loading: false,
  submitting: false,
  error: null,

  fetchPending: async () => {
    set({ loading: true, error: null });
    try {
      const pending = await api.listReviews('pending');
      set({ pending, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  fetchCompleted: async () => {
    set({ loading: true, error: null });
    try {
      const completed = await api.listReviews('completed');
      set({ completed, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  fetchDetail: async (mappingId: string) => {
    set({ loading: true, error: null, currentDetail: null });
    try {
      const detail = await api.getReviewDetail(mappingId);
      set({ currentDetail: detail, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  submitDecision: async (decision: ReviewDecision) => {
    set({ submitting: true, error: null });
    try {
      const result = await api.submitReview(decision);
      set({ submitting: false });
      // Refresh pending list
      await get().fetchPending();
      return result.message;
    } catch (e) {
      set({ error: (e as Error).message, submitting: false });
      throw e;
    }
  },
}));
