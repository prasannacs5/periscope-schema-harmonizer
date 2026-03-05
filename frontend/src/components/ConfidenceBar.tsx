export default function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  let barColor: string;

  if (score >= 0.9) {
    barColor = 'bg-success';
  } else if (score >= 0.7) {
    barColor = 'bg-warning';
  } else {
    barColor = 'bg-error';
  }

  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-semibold tabular-nums w-9 text-right">
        {pct}%
      </span>
    </div>
  );
}
