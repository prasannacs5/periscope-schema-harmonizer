import { create } from 'zustand';
import type { ChatMessage } from '../types';
import * as api from '../api/client';

let msgCounter = 0;

interface ChatStore {
  messages: ChatMessage[];
  suggestions: string[];
  loading: boolean;
  error: string | null;

  fetchSuggestions: (uploadId?: string) => Promise<void>;
  sendMessage: (
    text: string,
    uploadId?: string | null,
    customerId?: string | null,
  ) => Promise<void>;
  clearMessages: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  suggestions: [],
  loading: false,
  error: null,

  fetchSuggestions: async (uploadId?: string) => {
    try {
      const data = await api.chatSuggestions(uploadId);
      set({ suggestions: data.suggestions });
    } catch {
      // Ignore — non-critical
    }
  },

  sendMessage: async (text, uploadId, customerId) => {
    const userMsg: ChatMessage = {
      id: `msg-${++msgCounter}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    set((s) => ({ messages: [...s.messages, userMsg], loading: true, error: null }));

    try {
      const resp = await api.chat({
        message: text,
        upload_id: uploadId ?? undefined,
        customer_id: customerId ?? undefined,
      });
      const assistantMsg: ChatMessage = {
        id: `msg-${++msgCounter}`,
        role: 'assistant',
        content: resp.response,
        timestamp: new Date(),
      };
      set((s) => ({ messages: [...s.messages, assistantMsg], loading: false }));
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  clearMessages: () => set({ messages: [], error: null }),
}));
