import { Loader2 } from 'lucide-react';

export default function Spinner({ text }: { text?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-12 text-brand-slate">
      <Loader2 size={20} className="animate-spin" />
      {text && <span className="text-sm">{text}</span>}
    </div>
  );
}
