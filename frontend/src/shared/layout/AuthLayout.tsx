import { Outlet } from "react-router";
import { RefreshCw, TrendingUp, Sparkles } from "lucide-react";

const features = [
  {
    icon: RefreshCw,
    title: "Real-time collaboration",
    description: "Sync with your team across the globe instantly.",
    tone: "collab",
  },
  {
    icon: TrendingUp,
    title: "Advanced analytics",
    description: "Data-driven insights to optimize your output.",
    tone: "analytics",
  },
  {
    icon: Sparkles,
    title: "Automated Task Management",
    description: "Let AI handle the routine while you focus on the big picture.",
    tone: "automation",
  },
];

export default function AuthLayout() {
  return (
    <div className="flex min-h-screen">

      {/* Left panel */}
      <div className="relative hidden items-center justify-center overflow-hidden border-r bg-muted/20 lg:flex lg:w-1/2">

        <div className="relative z-10 max-w-lg px-12">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-12">
            <div className="rounded-lg bg-primary p-2">
              <svg className="w-8 h-8 text-background" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path clipRule="evenodd" d="M24 4H6V17.3333V30.6667H24V44H42V30.6667V17.3333H24V4Z" fill="currentColor" fillRule="evenodd" />
              </svg>
            </div>
            <span className="text-2xl font-bold tracking-tight text-foreground">Sophikon</span>
          </div>

          {/* Headline */}
          <h1 className="text-5xl font-bold leading-tight text-foreground mb-6">
            Empower Your <span className="text-primary">Workflow</span>
          </h1>
          <p className="text-muted-foreground text-lg mb-10 leading-relaxed">
            The next generation of project management. Built for speed, designed for clarity, and engineered for teams that deliver.
          </p>

          {/* Features */}
          <ul className="space-y-6">
            {features.map(({ icon: Icon, title, description, tone }) => (
              <li key={title} className="flex items-center gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-muted">
                  <Icon className="size-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">{title}</p>
                  <p className="text-sm text-muted-foreground">{description}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Right panel */}
      <div className="auth-form-side flex w-full lg:w-1/2 items-center justify-center p-8">
        <div className="ui-border-anim-primary w-full max-w-md rounded-2xl border bg-card p-8 text-card-foreground shadow-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-10 lg:hidden">
            <div className="bg-primary p-2 rounded-lg">
              <svg className="w-6 h-6 text-background" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path clipRule="evenodd" d="M24 4H6V17.3333V30.6667H24V44H42V30.6667V17.3333H24V4Z" fill="currentColor" fillRule="evenodd" />
              </svg>
            </div>
            <span className="text-xl font-bold tracking-tight">Sophikon</span>
          </div>
          <Outlet />
        </div>
      </div>

    </div>
  );
}
