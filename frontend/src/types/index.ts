/* ------------------------------------------------------------------ */
/*  Periscope Schema Harmonizer — shared TypeScript types              */
/* ------------------------------------------------------------------ */

/* ---- CDM ---- */
export interface CDMField {
  field_id: string;
  field_name: string;
  display_name: string;
  data_type: string;
  description: string;
  is_required: string;       // "true" | "false" from API
  example_values: string;
  added_by: string;
  added_at: string;
  source_customer: string;
}

/* ---- Uploads ---- */
export type UploadStatus =
  | 'PENDING_MAPPING'
  | 'PENDING_REVIEW'
  | 'APPROVED'
  | 'REJECTED';

export interface SchemaColumn {
  dtype: string;
  cdm_type: string;
  sample_values: string[];
  null_count: number;
  unique_count: number;
}

export interface Upload {
  upload_id: string;
  customer_id: string;
  file_name: string;
  source_system: string;
  uploaded_at: string;
  row_count: number;
  column_count: number;
  schema_json: string;        // JSON string of Record<string, SchemaColumn>
  sample_data_json: string;   // JSON string of Record<string, unknown>[]
  status: UploadStatus;
  error_message: string | null;
}

export interface UploadResponse {
  upload_id: string;
  customer_id: string;
  file_name: string;
  row_count: number;
  column_count: number;
  columns: string[];
  schema: Record<string, SchemaColumn>;
  status: UploadStatus;
}

/* ---- Mappings ---- */
export interface MappingEntry {
  source_column: string;
  cdm_field: string | null;
  transformation: string | null;
  confidence: number;
  reasoning: string;
}

export interface MappingData {
  mappings: MappingEntry[];
  overall_confidence: number;
  unmapped_cdm_fields: string[];
  notes: string;
}

export interface SchemaMapping {
  mapping_id: string;
  upload_id: string;
  customer_id: string;
  proposed_at: string;
  mapping_json: string;        // JSON string of MappingData
  confidence_score: number;
  llm_reasoning: string;
  similar_mapping_ids: string;  // JSON string of string[]
  status: string;
  // Joined fields from reviews endpoint
  file_name?: string;
  source_system?: string;
  row_count?: number;
}

/* ---- Reviews ---- */
export interface ReviewDetail {
  mapping: SchemaMapping;
  upload: Upload | null;
}

export interface ReviewDecision {
  mapping_id: string;
  upload_id: string;
  decision: 'APPROVED' | 'REJECTED';
  reviewer: string;
  reviewer_notes: string;
  final_mapping_json?: string;
}

/* ---- Chat ---- */
export interface ChatRequest {
  message: string;
  upload_id?: string | null;
  customer_id?: string | null;
}

export interface ChatResponse {
  response: string;
  context_used: boolean;
}

export interface ChatSuggestions {
  suggestions: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
