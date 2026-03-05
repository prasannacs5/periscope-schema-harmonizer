import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  Columns3,
  Wand2,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { useUploadStore } from '../../stores/uploadStore';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import Spinner from '../../components/Spinner';

export default function UploadDetail() {
  const { id } = useParams<{ id: string }>();
  const { current, loading, error, fetchUpload, requestMapping } = useUploadStore();
  const [mapping, setMapping] = useState(false);
  const [mapSuccess, setMapSuccess] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  useEffect(() => {
    if (id) fetchUpload(id);
  }, [id, fetchUpload]);

  const handleRequestMapping = async () => {
    if (!id) return;
    setMapping(true);
    setMapError(null);
    setMapSuccess(false);
    try {
      await requestMapping(id);
      setMapSuccess(true);
    } catch (e) {
      setMapError((e as Error).message);
    } finally {
      setMapping(false);
    }
  };

  if (loading && !current) return <Spinner text="Loading upload details..." />;
  if (error) {
    return (
      <div className="card flex items-center gap-2 text-error">
        <AlertCircle size={16} /> {error}
      </div>
    );
  }
  if (!current) return null;

  // Schema may be in full form {dtype, cdm_type, sample_values, ...} or
  // seed-data form {type, cdm_field}. Normalise to a common shape.
  interface NormalizedCol {
    type: string;
    unique_count?: number;
    null_count?: number;
    sample_values: string[];
  }

  let schema: Record<string, NormalizedCol> = {};
  try {
    const raw: Record<string, Record<string, unknown>> = JSON.parse(current.schema_json || '{}');
    for (const [col, info] of Object.entries(raw)) {
      schema[col] = {
        type: (info.cdm_type ?? info.type ?? 'string') as string,
        unique_count: info.unique_count as number | undefined,
        null_count: info.null_count as number | undefined,
        sample_values: Array.isArray(info.sample_values) ? info.sample_values : [],
      };
    }
  } catch {
    // Ignore parse error
  }

  let sampleData: Record<string, unknown>[] = [];
  try {
    sampleData = JSON.parse(current.sample_data_json || '[]');
  } catch {
    // Ignore parse error
  }

  const columns = Object.entries(schema);

  return (
    <div>
      <Link
        to="/history"
        className="inline-flex items-center gap-1.5 text-sm text-brand-slate hover:text-brand-blue mb-4"
      >
        <ArrowLeft size={14} /> Back to History
      </Link>

      <PageHeader
        title={current.file_name}
        subtitle={`${current.customer_id} / ${current.source_system} / ${current.row_count.toLocaleString()} rows / ${current.column_count} columns`}
        action={<StatusBadge status={current.status} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Schema table */}
        <div className="lg:col-span-2">
          <div className="card p-0 overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 bg-gray-50/50 flex items-center gap-2">
              <Columns3 size={15} className="text-brand-slate" />
              <h2 className="text-sm font-semibold text-gray-700">
                Detected Schema ({columns.length} columns)
              </h2>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left px-5 py-2.5 font-semibold text-gray-600">Column</th>
                  <th className="text-left px-5 py-2.5 font-semibold text-gray-600">Type</th>
                  <th className="text-right px-5 py-2.5 font-semibold text-gray-600">Unique</th>
                  <th className="text-right px-5 py-2.5 font-semibold text-gray-600">Nulls</th>
                  <th className="text-left px-5 py-2.5 font-semibold text-gray-600">Sample Values</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {columns.map(([name, col]) => (
                  <tr key={name} className="hover:bg-gray-50/50">
                    <td className="px-5 py-2.5 font-mono text-xs font-medium text-gray-900">{name}</td>
                    <td className="px-5 py-2.5">
                      <span className="rounded bg-brand-blue/5 px-2 py-0.5 text-xs font-medium text-brand-blue">
                        {col.type}
                      </span>
                    </td>
                    <td className="px-5 py-2.5 text-right tabular-nums text-gray-600">
                      {col.unique_count ?? '--'}
                    </td>
                    <td className="px-5 py-2.5 text-right tabular-nums text-gray-600">
                      {col.null_count ?? '--'}
                    </td>
                    <td className="px-5 py-2.5 text-xs text-gray-500 max-w-[260px] truncate">
                      {col.sample_values.length > 0 ? col.sample_values.join(', ') : '--'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right sidebar */}
        <div className="space-y-4">
          {/* Actions */}
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Actions</h3>

            {current.status === 'PENDING_MAPPING' && (
              <>
                {mapping ? (
                  <Spinner text="LLM is analyzing schema..." />
                ) : (
                  <button
                    onClick={handleRequestMapping}
                    className="btn-primary w-full"
                  >
                    <Wand2 size={16} />
                    Request AI Mapping
                  </button>
                )}
              </>
            )}

            {current.status === 'PENDING_REVIEW' && (
              <div className="flex items-start gap-2 text-sm text-amber-700 bg-amber-50 rounded-lg p-3">
                <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
                Mapping has been generated and is waiting for analyst review.
              </div>
            )}

            {current.status === 'APPROVED' && (
              <div className="flex items-start gap-2 text-sm text-emerald-700 bg-emerald-50 rounded-lg p-3">
                <CheckCircle2 size={16} className="mt-0.5 flex-shrink-0" />
                Schema mapping has been approved and data is being ingested.
              </div>
            )}

            {mapSuccess && (
              <div className="mt-3 flex items-start gap-2 text-sm text-emerald-700 bg-emerald-50 rounded-lg p-3">
                <CheckCircle2 size={16} className="mt-0.5 flex-shrink-0" />
                Mapping generated. An analyst will review it shortly.
              </div>
            )}

            {mapError && (
              <div className="mt-3 flex items-start gap-2 text-sm text-red-700 bg-red-50 rounded-lg p-3">
                <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
                {mapError}
              </div>
            )}
          </div>

          {/* File info */}
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">File Details</h3>
            <dl className="space-y-2 text-sm">
              {[
                ['File', current.file_name],
                ['Customer', current.customer_id],
                ['Source', current.source_system],
                ['Rows', current.row_count.toLocaleString()],
                ['Columns', current.column_count.toString()],
                ['Uploaded', new Date(current.uploaded_at).toLocaleString()],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between">
                  <dt className="text-gray-500">{label}</dt>
                  <dd className="font-medium text-gray-900">{value}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Sample data */}
          {sampleData.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                <FileText size={14} className="inline mr-1" />
                Sample Data (first {sampleData.length} rows)
              </h3>
              <div className="overflow-x-auto -mx-6 px-6">
                <div className="max-h-64 overflow-y-auto">
                  <table className="text-xs min-w-full">
                    <thead>
                      <tr>
                        {Object.keys(sampleData[0]).map((k) => (
                          <th key={k} className="text-left px-2 py-1.5 font-semibold text-gray-600 whitespace-nowrap">
                            {k}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {sampleData.slice(0, 5).map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((v, j) => (
                            <td key={j} className="px-2 py-1.5 text-gray-600 whitespace-nowrap max-w-[120px] truncate">
                              {String(v ?? '')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
