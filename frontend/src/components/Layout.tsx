import { FileUp, LayoutDashboard, LineChart, ScanText, ShieldCheck } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/upload", label: "Upload document", icon: FileUp, end: false },
  { to: "/trends", label: "Trends", icon: LineChart, end: false },
  { to: "/privacy", label: "Privacy & data", icon: ShieldCheck, end: false },
];

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="border-b border-line bg-surface md:w-60 md:shrink-0 md:border-b-0 md:border-r">
        <div className="flex items-center gap-2 px-5 py-5">
          <ScanText className="h-6 w-6 text-teal" aria-hidden="true" />
          <span className="font-serif text-xl font-semibold">MediLens</span>
        </div>
        <nav aria-label="Main" className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:pb-0">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 whitespace-nowrap rounded-md border-l-2 px-3 py-2 text-sm font-medium ${
                  isActive
                    ? "border-teal bg-teal-soft text-teal"
                    : "border-transparent text-slate hover:bg-paper hover:text-ink"
                }`
              }
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="min-w-0 flex-1 px-5 py-8 md:px-10">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
