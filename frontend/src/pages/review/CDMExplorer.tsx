import { useEffect } from 'react';
import { CheckCircle2, Circle } from 'lucide-react';
import { useCDMStore } from '../../stores/cdmStore';
import PageHeader from '../../components/PageHeader';
import Spinner from '../../components/Spinner';

export default function CDMExplorer() {
  const { fields, loading, fetchFields } = useCDMStore();

  useEffect(() => {
    fetchFields();
  }, [fetchFields]);

  return (
    <div>
      <PageHeader
        title="Common Data Model"
        subtitle={`${fields.length} standardized fields defining the Periscope data schema`}
      />

      {loading ? (
        <Spinner text="Loading CDM fields..." />
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/50">
                <th className="text-left px-5 py-3 font-semibold text-gray-600 w-10">#</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Field Name</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Display Name</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Data Type</th>
                <th className="text-center px-5 py-3 font-semibold text-gray-600">Required</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Description</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Example</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {fields.map((f, i) => (
                <tr key={f.field_id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-5 py-3 text-gray-400 text-xs">{i + 1}</td>
                  <td className="px-5 py-3">
                    <span className="font-mono text-xs font-semibold text-brand-blue">
                      {f.field_name}
                    </span>
                  </td>
                  <td className="px-5 py-3 font-medium text-gray-900">{f.display_name}</td>
                  <td className="px-5 py-3">
                    <span className="rounded bg-brand-navy/5 px-2 py-0.5 text-xs font-medium text-brand-navy">
                      {f.data_type}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-center">
                    {f.is_required === 'true' ? (
                      <CheckCircle2 size={15} className="inline text-success" />
                    ) : (
                      <Circle size={15} className="inline text-gray-300" />
                    )}
                  </td>
                  <td className="px-5 py-3 text-gray-600 max-w-[300px]">{f.description}</td>
                  <td className="px-5 py-3 text-xs text-gray-500 font-mono">{f.example_values}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
