import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileUp, X, AlertCircle } from 'lucide-react';
import { useUploadStore } from '../../stores/uploadStore';
import PageHeader from '../../components/PageHeader';
import Spinner from '../../components/Spinner';

const SOURCE_SYSTEMS = ['POS', 'CRM', 'ERP', 'Other'] as const;

export default function FileUpload() {
  const navigate = useNavigate();
  const { upload: submitUpload, uploading, error } = useUploadStore();

  const [file, setFile] = useState<File | null>(null);
  const [customerId, setCustomerId] = useState('');
  const [sourceSystem, setSourceSystem] = useState<string>('POS');
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && isValidFile(dropped)) {
      setFile(dropped);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected && isValidFile(selected)) {
      setFile(selected);
    }
  };

  const isValidFile = (f: File) => {
    const name = f.name.toLowerCase();
    return name.endsWith('.csv') || name.endsWith('.xlsx') || name.endsWith('.xls');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !customerId.trim()) return;

    try {
      const result = await submitUpload(file, customerId.trim(), sourceSystem);
      navigate(`/uploads/${result.upload_id}`);
    } catch {
      // Error is captured in store
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div>
      <PageHeader
        title="Upload Data File"
        subtitle="Upload CSV or Excel files containing customer sales data for schema harmonization"
      />

      <form onSubmit={handleSubmit} className="max-w-2xl">
        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`card cursor-pointer border-2 border-dashed transition-all ${
            dragOver
              ? 'border-brand-blue bg-brand-blue/5'
              : file
                ? 'border-success/40 bg-emerald-50/50'
                : 'border-gray-300 hover:border-brand-blue/40'
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileSelect}
            className="hidden"
          />

          {file ? (
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-success/10 p-3">
                <FileUp size={24} className="text-success" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">
                  {file.name}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {formatSize(file.size)}
                </p>
              </div>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center py-6 text-center">
              <div className="mb-3 rounded-xl bg-gray-100 p-3">
                <Upload size={28} className="text-brand-slate/50" />
              </div>
              <p className="text-sm font-semibold text-gray-700">
                Drop your file here, or click to browse
              </p>
              <p className="mt-1 text-xs text-gray-500">
                Supports CSV, XLS, and XLSX files
              </p>
            </div>
          )}
        </div>

        {/* Fields */}
        <div className="mt-5 grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Customer ID
            </label>
            <input
              type="text"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              placeholder="e.g. CUST_001"
              className="input-field"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Source System
            </label>
            <select
              value={sourceSystem}
              onChange={(e) => setSourceSystem(e.target.value)}
              className="input-field"
            >
              {SOURCE_SYSTEMS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Submit */}
        <div className="mt-6">
          {uploading ? (
            <Spinner text="Uploading and analyzing schema..." />
          ) : (
            <button
              type="submit"
              disabled={!file || !customerId.trim()}
              className="btn-primary"
            >
              <Upload size={16} />
              Upload File
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
