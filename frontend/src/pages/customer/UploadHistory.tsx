import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Database, FileText, ArrowRight } from 'lucide-react';
import { useUploadStore } from '../../stores/uploadStore';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import Spinner from '../../components/Spinner';
import EmptyState from '../../components/EmptyState';

export default function UploadHistory() {
  const { uploads, loading, fetchUploads } = useUploadStore();

  useEffect(() => {
    fetchUploads();
  }, [fetchUploads]);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div>
      <PageHeader
        title="Upload History"
        subtitle="All uploaded data files and their harmonization status"
        action={
          <Link to="/" className="btn-primary">
            <FileText size={16} />
            New Upload
          </Link>
        }
      />

      {loading ? (
        <Spinner text="Loading uploads..." />
      ) : uploads.length === 0 ? (
        <EmptyState
          icon={Database}
          title="No uploads yet"
          description="Upload a CSV or Excel file to get started with schema harmonization."
          action={
            <Link to="/" className="btn-primary">
              Upload File
            </Link>
          }
        />
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/50">
                <th className="text-left px-5 py-3 font-semibold text-gray-600">File Name</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Customer</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Source</th>
                <th className="text-right px-5 py-3 font-semibold text-gray-600">Rows</th>
                <th className="text-right px-5 py-3 font-semibold text-gray-600">Columns</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Status</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Uploaded</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {uploads.map((u) => (
                <tr key={u.upload_id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <FileText size={14} className="text-brand-slate/50 flex-shrink-0" />
                      <span className="font-medium truncate max-w-[200px]">{u.file_name}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-gray-600 font-mono text-xs">{u.customer_id}</td>
                  <td className="px-5 py-3">
                    <span className="inline-flex rounded bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                      {u.source_system}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right tabular-nums text-gray-600">{u.row_count.toLocaleString()}</td>
                  <td className="px-5 py-3 text-right tabular-nums text-gray-600">{u.column_count}</td>
                  <td className="px-5 py-3"><StatusBadge status={u.status} /></td>
                  <td className="px-5 py-3 text-gray-500 text-xs">{formatDate(u.uploaded_at)}</td>
                  <td className="px-5 py-3">
                    <Link
                      to={`/uploads/${u.upload_id}`}
                      className="inline-flex items-center gap-1 text-xs font-medium text-brand-blue hover:text-brand-navy"
                    >
                      View <ArrowRight size={12} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
