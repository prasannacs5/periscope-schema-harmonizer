import { NavLink, Outlet } from 'react-router-dom';
import {
  Upload,
  ClipboardCheck,
  Database,
  MessageSquare,
} from 'lucide-react';

const customerLinks = [
  { to: '/', label: 'Upload', icon: Upload, end: true },
  { to: '/history', label: 'History', icon: Database },
  { to: '/chat', label: 'Chat', icon: MessageSquare },
];

const analystLinks = [
  { to: '/review', label: 'Pending', icon: ClipboardCheck, end: true },
  { to: '/review/cdm', label: 'CDM Explorer', icon: Database },
];

function NavGroup({
  title,
  links,
}: {
  title: string;
  links: { to: string; label: string; icon: React.ElementType; end?: boolean }[];
}) {
  return (
    <div>
      <p className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-wider text-brand-slate/60">
        {title}
      </p>
      <div className="flex items-center gap-1">
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-white text-brand-blue shadow-sm'
                  : 'text-white/80 hover:bg-white/10 hover:text-white'
              }`
            }
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </div>
    </div>
  );
}

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-brand-navy text-white">
        <div className="max-w-screen-2xl mx-auto px-6 py-3 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded bg-brand-blue flex items-center justify-center">
                <span className="text-xs font-black tracking-tight">P</span>
              </div>
              <div>
                <span className="text-base font-bold tracking-tight">
                  Periscope
                </span>
                <span className="text-white/50 mx-1.5">|</span>
                <span className="text-sm font-medium text-white/80">
                  Schema Harmonizer
                </span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-6">
            <NavGroup title="Customer" links={customerLinks} />
            <div className="w-px h-6 bg-white/20" />
            <NavGroup title="Analyst" links={analystLinks} />
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 max-w-screen-2xl mx-auto w-full px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}
