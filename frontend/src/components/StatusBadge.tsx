import type { UploadStatus } from '../types';

const config: Record<
  string,
  { bg: string; text: string; dot: string; label: string }
> = {
  PENDING_MAPPING: {
    bg: 'bg-gray-100',
    text: 'text-gray-700',
    dot: 'bg-gray-400',
    label: 'Pending Mapping',
  },
  PENDING_REVIEW: {
    bg: 'bg-amber-50',
    text: 'text-amber-800',
    dot: 'bg-warning',
    label: 'Pending Review',
  },
  PENDING: {
    bg: 'bg-amber-50',
    text: 'text-amber-800',
    dot: 'bg-warning',
    label: 'Pending Review',
  },
  APPROVED: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-800',
    dot: 'bg-success',
    label: 'Approved',
  },
  REJECTED: {
    bg: 'bg-red-50',
    text: 'text-red-800',
    dot: 'bg-error',
    label: 'Rejected',
  },
};

export default function StatusBadge({
  status,
}: {
  status: UploadStatus | string;
}) {
  const c = config[status] ?? config.PENDING_MAPPING;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${c.bg} ${c.text}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}
