import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Briefcase,
  Building2,
  FileText,
  FolderGit2,
  LayoutDashboard,
  LogOut,
  Menu,
  Route,
  Settings,
  Sparkles,
  Target,
  User,
  X,
} from "lucide-react";
import { useAuth } from "../lib/auth";
import { cn } from "../lib/utils";
import { Button } from "./ui";

const navItems = [
  { to: "/app", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/app/resumes", label: "Resumes", icon: FileText },
  { to: "/app/jobs", label: "Job descriptions", icon: Briefcase },
  { to: "/app/match", label: "Match & keywords", icon: Target },
  { to: "/app/career-roadmap", label: "Career roadmap", icon: Route },
  { to: "/app/projects", label: "Projects", icon: FolderGit2 },
  { to: "/app/portfolio", label: "Portfolio", icon: Sparkles },
  { to: "/app/company-insights", label: "Company insights", icon: Building2 },
  { to: "/app/applications", label: "Applications", icon: Briefcase },
  { to: "/app/profile", label: "Profile", icon: User },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <div className="min-h-screen bg-ivory-100 lg:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:m-2 focus:rounded focus:bg-ivory-50 focus:p-2">
        Skip to content
      </a>
      <aside
        className={cn(
          "fixed inset-y-0 z-30 w-64 flex-col border-r border-stone-200 bg-ivory-50 p-4 lg:static lg:flex",
          open ? "flex" : "hidden",
        )}
        aria-label="Workspace navigation"
      >
        <div className="mb-6 flex items-center justify-between">
          <NavLink to="/app" className="font-serif text-2xl text-ink" onClick={() => setOpen(false)}>
            Resumo
          </NavLink>
          <button className="lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation">
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                  isActive ? "bg-forest-tint text-forest font-medium" : "text-ink-soft hover:bg-ivory-200",
                )
              }
            >
              <item.icon className="h-4 w-4" aria-hidden />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-4 border-t border-stone-200 pt-4">
          <p className="truncate text-xs text-ink-muted">{user?.email}</p>
          <Button variant="ghost" size="sm" className="mt-2 w-full justify-start" onClick={handleLogout}>
            <LogOut className="h-4 w-4" aria-hidden /> Sign out
          </Button>
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-stone-200 bg-ivory-100 px-4 py-3 lg:hidden">
          <button onClick={() => setOpen(true)} aria-label="Open navigation">
            <Menu className="h-5 w-5" />
          </button>
          <span className="font-serif text-xl">Resumo</span>
        </header>
        <main id="main" className="container-app flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function PublicLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  return (
    <div className="flex min-h-screen flex-col bg-ivory-100">
      <header className="border-b border-stone-200">
        <div className="container-page flex items-center justify-between py-4">
          <NavLink to="/" className="font-serif text-2xl text-ink">
            Resumo
          </NavLink>
          <nav className="flex items-center gap-1 sm:gap-4">
            <NavLink to="/features" className="hidden px-2 py-1 text-sm text-ink-soft hover:text-ink sm:block">
              Features
            </NavLink>
            <NavLink to="/how-it-works" className="hidden px-2 py-1 text-sm text-ink-soft hover:text-ink sm:block">
              How it works
            </NavLink>
            {user ? (
              <NavLink to="/app">
                <Button size="sm">Open workspace</Button>
              </NavLink>
            ) : (
              <>
                <NavLink to="/login" className="px-2 py-1 text-sm text-ink-soft hover:text-ink">
                  Sign in
                </NavLink>
                <NavLink to="/signup">
                  <Button size="sm">Get started</Button>
                </NavLink>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-stone-200">
        <div className="container-page flex flex-col items-start justify-between gap-3 py-6 text-sm text-ink-muted sm:flex-row sm:items-center">
          <p>Resumo — advisory career tooling. Scores are guidance, not hiring predictions.</p>
          <div className="flex gap-4">
            <NavLink to="/privacy" className="hover:text-ink">
              Privacy
            </NavLink>
            <NavLink to="/terms" className="hover:text-ink">
              Terms
            </NavLink>
          </div>
        </div>
      </footer>
    </div>
  );
}

export function PageHeader({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="font-serif text-3xl text-ink">{title}</h1>
        {description && <p className="mt-1 max-w-prose text-sm text-ink-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}
