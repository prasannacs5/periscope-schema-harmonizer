import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ClipboardCheck, Clock, FileText, ArrowRight } from 'lucide-react';
import { useReviewStore } from '../../stores/reviewStore';
import type { MappingData } from '../../types';
import PageHeader from '../../components/PageHeader';
import ConfidenceBadge from '../../components/ConfidenceBadge';
import Spinner from '../../components/Spinner';
import EmptyState from '../../components/EmptyState';

export default function PendingReviews() {
  const { pending, loading, fetchPending } = useReviewStore();

  useEffect(() => {
    fetchPending();
  }, [fetchPending]);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getMappingCount = (jsonStr: string) => {
    try {
      const data: MappingData = JSON.parse(jsonStr);
      return data.mappings?.length ?? 0;
    } catch {
      return 0;
    }
  };

  return (
    <div>
      <PageHeader
        title="Pending Reviews"
        subtitle={`${pending.length} mapping${pending.length !== 1 ? 's' : ''} awaiting analyst review`}
      />

      {loading ? (
        <Spinner text="Loading pending reviews..." />
      ) : pending.length === 0 ? (
        <EmptyState
          icon={ClipboardCheck}
          title="All caught up"
          description="There are no pending schema mappings to review at the moment."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {pending.map((m) => (
            <Link
              key={m.mapping_id}
              to={`/review/${m.mapping_id}`}
              className="card hover:shadow-md hover:border-brand-blue/30 transition-all group"
            >
              {/* Top row */}
              <div className="flex items-start justify-between mb-3">
                <ConfidenceBadge score={m.confidence_score} />
                <span className="text-[10px] text-gray-400 font-mono">
                  {m.mapping_id.slice(0, 8)}
                </span>
              </div>

              {/* File info */}
              <div className="flex items-center gap-2 mb-2">
                <FileText size={14} className="text-brand-slate/50" />
                <span className="text-sm font-semibold text-gray-900 truncate">
                  {m.file_name ?? 'Unknown file'}
                </span>
              </div>

              {/* Details */}
              <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                <span className="font-mono">{m.customer_id}</span>
                <span className="text-gray-300">|</span>
                <span className="rounded bg-gray-100 px-1.5 py-0.5 font-medium text-gray-600">
                  {m.source_system ?? 'N/A'}
                </span>
                {m.row_count && (
                  <>
                    <span className="text-gray-300">|</span>
                    <span>{m.row_count} rows</span>
                  </>
                )}
              </div>

              {/* Mapping summary */}
              <p className="text-xs text-gray-500 line-clamp-2 mb-3">
                {getMappingCount(m.mapping_json)} field mappings proposed
                {m.llm_reasoning && ` -- ${m.llm_reasoning.slice(0, 100)}...`}
              </p>

              {/* Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <div className="flex items-center gap-1 text-xs text-gray-400">
                  <Clock size={12} />
                  {formatDate(m.proposed_at)}
                </div>
                <span className="text-xs font-medium text-brand-blue group-hover:underline flex items-center gap-1">
                  Review <ArrowRight size={12} />
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
