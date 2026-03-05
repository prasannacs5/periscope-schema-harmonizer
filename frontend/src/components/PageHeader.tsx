export default function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">{title}</h1>
        {subtitle && (
          <p className="mt-0.5 text-sm text-brand-slate">{subtitle}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
