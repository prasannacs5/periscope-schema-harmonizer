import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  FileText,
  BookOpen,
  Lightbulb,
  AlertCircle,
} from 'lucide-react';
import { useReviewStore } from '../../stores/reviewStore';
import { useCDMStore } from '../../stores/cdmStore';
import type { MappingData } from '../../types';
import PageHeader from '../../components/PageHeader';
import ConfidenceBadge from '../../components/ConfidenceBadge';
import ConfidenceBar from '../../components/ConfidenceBar';
import Spinner from '../../components/Spinner';

export default function ReviewDetail() {
  const { mappingId } = useParams<{ mappingId: string }>();
  const navigate = useNavigate();
  const { currentDetail, loading, submitting, fetchDetail, submitDecision } = useReviewStore();
  const { fields: cdmFields, fetchFields } = useCDMStore();

  const [notes, setNotes] = useState('');
  const [resultMsg, setResultMsg] = useState<string | null>(null);
  const [resultType, setResultType] = useState<'success' | 'error'>('success');

  useEffect(() => {
    if (mappingId) fetchDetail(mappingId);
    fetchFields();
  }, [mappingId, fetchDetail, fetchFields]);

  if (loading) return <Spinner text="Loading review details..." />;
  if (!currentDetail) return null;

  const { mapping, upload } = currentDetail;

  let mappingData: MappingData | null = null;
  try {
    mappingData = JSON.parse(mapping.mapping_json);
  } catch {
    // Ignore
  }

  interface NormalizedCol {
    type: string;
    sample_values: string[];
  }
  let sourceSchema: Record<string, NormalizedCol> = {};
  try {
    if (upload?.schema_json) {
      const raw: Record<string, Record<string, unknown>> = JSON.parse(upload.schema_json);
      for (const [col, info] of Object.entries(raw)) {
        sourceSchema[col] = {
          type: (info.cdm_type ?? info.type ?? 'string') as string,
          sample_values: Array.isArray(info.sample_values) ? info.sample_values : [],
        };
      }
    }
  } catch {
    // Ignore
  }

  const sourceColumns = Object.keys(sourceSchema);

  const handleDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!mappingId || !mapping.upload_id) return;
    try {
      const msg = await submitDecision({
        mapping_id: mappingId,
        upload_id: mapping.upload_id,
        decision,
        reviewer: 'analyst',
        reviewer_notes: notes,
      });
      setResultMsg(msg);
      setResultType('success');
      // Navigate back after 2 seconds
      setTimeout(() => navigate('/review'), 2000);
    } catch (e) {
      setResultMsg((e as Error).message);
      setResultType('error');
    }
  };

  return (
    <div>
      <Link
        to="/review"
        className="inline-flex items-center gap-1.5 text-sm text-brand-slate hover:text-brand-blue mb-4"
      >
        <ArrowLeft size={14} /> Back to Reviews
      </Link>

      <PageHeader
        title={`Review: ${upload?.file_name ?? mapping.mapping_id.slice(0, 8)}`}
        subtitle={`${mapping.customer_id} / ${upload?.source_system ?? 'N/A'} / ${upload?.row_count ?? 0} rows`}
        action={<ConfidenceBadge score={mapping.confidence_score} />}
      />

      <div className="grid grid-cols-12 gap-4">
        {/* LEFT: Source schema */}
        <div className="col-span-12 lg:col-span-3">
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 bg-gray-50/50 flex items-center gap-2">
              <FileText size={14} className="text-brand-slate" />
              <h3 className="text-sm font-semibold text-gray-700">
                Source Schema ({sourceColumns.length})
              </h3>
            </div>
            <div className="divide-y divide-gray-50 max-h-[600px] overflow-y-auto">
              {sourceColumns.map((col) => {
                const info = sourceSchema[col];
                return (
                  <div key={col} className="px-4 py-2.5">
                    <div className="font-mono text-xs font-medium text-gray-900">
                      {col}
                    </div>
                    <div className="text-[10px] text-gray-500 mt-0.5">
                      {info.type}
                      {info.sample_values?.length > 0 && (
                        <span className="ml-1 text-gray-400">
                          -- {info.sample_values.slice(0, 2).join(', ')}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* CENTER: Mapping table */}
        <div className="col-span-12 lg:col-span-6">
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 bg-gray-50/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lightbulb size={14} className="text-brand-blue" />
                <h3 className="text-sm font-semibold text-gray-700">
                  Proposed Mapping
                </h3>
              </div>
              {mappingData && (
                <span className="text-xs text-gray-500">
                  {mappingData.mappings.length} fields mapped
                </span>
              )}
            </div>

            {mappingData ? (
              <>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left px-4 py-2.5 font-semibold text-gray-600">Source Column</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-gray-600">CDM Field</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-gray-600">Transform</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-gray-600 w-[140px]">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {mappingData.mappings.map((entry, i) => (
                      <tr key={i} className="hover:bg-gray-50/50 group">
                        <td className="px-4 py-2.5 font-mono text-xs font-medium text-gray-900">
                          {entry.source_column}
                        </td>
                        <td className="px-4 py-2.5">
                          {entry.cdm_field ? (
                            <span className="rounded bg-brand-blue/10 px-2 py-0.5 text-xs font-semibold text-brand-blue">
                              {entry.cdm_field}
                            </span>
                          ) : (
                            <span className="text-xs text-gray-400 italic">unmapped</span>
                          )}
                        </td>
                        <td className="px-4 py-2.5 font-mono text-xs text-gray-500">
                          {entry.transformation ?? '--'}
                        </td>
                        <td className="px-4 py-2.5">
                          <ConfidenceBar score={entry.confidence} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* Unmapped CDM fields */}
                {mappingData.unmapped_cdm_fields.length > 0 && (
                  <div className="px-4 py-3 border-t border-gray-100 bg-amber-50/50">
                    <p className="text-xs font-semibold text-amber-800 mb-1.5">
                      Unmapped CDM Fields ({mappingData.unmapped_cdm_fields.length})
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {mappingData.unmapped_cdm_fields.map((f) => (
                        <span
                          key={f}
                          className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-800"
                        >
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* LLM notes */}
                {mappingData.notes && (
                  <div className="px-4 py-3 border-t border-gray-100">
                    <p className="text-xs font-semibold text-gray-600 mb-1">AI Notes</p>
                    <p className="text-xs text-gray-500 leading-relaxed">{mappingData.notes}</p>
                  </div>
                )}
              </>
            ) : (
              <div className="px-4 py-8 text-center text-sm text-gray-400">
                Could not parse mapping data
              </div>
            )}
          </div>

          {/* Decision area */}
          <div className="card mt-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Review Decision</h3>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add reviewer notes (optional)..."
              rows={3}
              className="input-field mb-4"
            />

            {resultMsg && (
              <div
                className={`mb-4 flex items-start gap-2 rounded-lg px-4 py-3 text-sm ${
                  resultType === 'success'
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}
              >
                {resultType === 'success' ? (
                  <CheckCircle2 size={16} className="mt-0.5 flex-shrink-0" />
                ) : (
                  <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
                )}
                {resultMsg}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => handleDecision('APPROVED')}
                disabled={submitting || !!resultMsg}
                className="btn-success flex-1"
              >
                <CheckCircle2 size={16} />
                Approve Mapping
              </button>
              <button
                onClick={() => handleDecision('REJECTED')}
                disabled={submitting || !!resultMsg}
                className="btn-danger flex-1"
              >
                <XCircle size={16} />
                Reject Mapping
              </button>
            </div>

            {submitting && <Spinner text="Submitting decision..." />}
          </div>
        </div>

        {/* RIGHT: CDM reference */}
        <div className="col-span-12 lg:col-span-3">
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 bg-gray-50/50 flex items-center gap-2">
              <BookOpen size={14} className="text-brand-slate" />
              <h3 className="text-sm font-semibold text-gray-700">
                CDM Reference ({cdmFields.length})
              </h3>
            </div>
            <div className="divide-y divide-gray-50 max-h-[600px] overflow-y-auto">
              {cdmFields.map((f) => (
                <div key={f.field_id} className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-medium text-gray-900">
                      {f.field_name}
                    </span>
                    <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600">
                      {f.data_type}
                    </span>
                    {f.is_required === 'true' && (
                      <span className="text-[10px] font-bold text-error">REQ</span>
                    )}
                  </div>
                  <p className="text-[10px] text-gray-500 mt-0.5">
                    {f.description}
                  </p>
                  {f.example_values && (
                    <p className="text-[10px] text-gray-400 mt-0.5">
                      e.g. {f.example_values}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
