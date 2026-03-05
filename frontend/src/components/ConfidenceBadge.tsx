export default function ConfidenceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  let color: string;
  let bgColor: string;

  if (score >= 0.9) {
    color = 'text-emerald-700';
    bgColor = 'bg-emerald-50 border-emerald-200';
  } else if (score >= 0.7) {
    color = 'text-amber-700';
    bgColor = 'bg-amber-50 border-amber-200';
  } else {
    color = 'text-red-700';
    bgColor = 'bg-red-50 border-red-200';
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-bold ${bgColor} ${color}`}
    >
      <span className="tabular-nums">{pct}%</span>
      <span className="font-normal opacity-70">confidence</span>
    </span>
  );
}
