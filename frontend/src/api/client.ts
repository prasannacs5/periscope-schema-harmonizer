/* ------------------------------------------------------------------ */
/*  API client — thin fetch wrapper for all backend endpoints          */
/* ------------------------------------------------------------------ */
import type {
  Upload,
  UploadResponse,
  SchemaMapping,
  CDMField,
  ReviewDetail,
  ReviewDecision,
  ChatRequest,
  ChatResponse,
  ChatSuggestions,
} from '../types';

const BASE = '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      ...(init?.body instanceof FormData
        ? {}
        : { 'Content-Type': 'application/json' }),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

/* ---- Health ---- */
export const health = () => request<{ status: string }>('/health');

/* ---- Uploads ---- */
export const listUploads = (customerId?: string) =>
  request<Upload[]>(
    customerId ? `/uploads?customer_id=${customerId}` : '/uploads',
  );

export const getUpload = (id: string) => request<Upload>(`/uploads/${id}`);

export const uploadFile = (
  file: File,
  customerId: string,
  sourceSystem: string,
) => {
  const form = new FormData();
  form.append('file', file);
  form.append('customer_id', customerId);
  form.append('source_system', sourceSystem);
  return request<UploadResponse>('/upload', { method: 'POST', body: form });
};

/* ---- Mappings ---- */
export const mapSchema = (uploadId: string) =>
  request<{
    mapping_id: string;
    upload_id: string;
    customer_id: string;
    status: string;
    mapping: Record<string, unknown>;
    similar_mappings_used: number;
  }>('/map-schema', {
    method: 'POST',
    body: JSON.stringify({ upload_id: uploadId }),
  });

export const listMappings = (status?: string) =>
  request<SchemaMapping[]>(
    status ? `/mappings?status=${status}` : '/mappings',
  );

export const getMapping = (id: string) =>
  request<SchemaMapping>(`/mappings/${id}`);

/* ---- CDM ---- */
export const getCDM = () =>
  request<{ fields: CDMField[]; total: number }>('/cdm');

/* ---- Reviews ---- */
export const listReviews = (status?: string) =>
  request<SchemaMapping[]>(
    status ? `/reviews?status=${status}` : '/reviews',
  );

export const getReviewDetail = (mappingId: string) =>
  request<ReviewDetail>(`/reviews/${mappingId}`);

export const submitReview = (decision: ReviewDecision) =>
  request<{ status: string; review_id: string; message: string }>(
    '/reviews/decide',
    { method: 'POST', body: JSON.stringify(decision) },
  );

/* ---- Chat ---- */
export const chat = (msg: ChatRequest) =>
  request<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(msg),
  });

export const chatSuggestions = (uploadId?: string) =>
  request<ChatSuggestions>(
    uploadId ? `/chat/suggestions?upload_id=${uploadId}` : '/chat/suggestions',
  );
