import { Outlet } from "react-router";
import { RefreshCw, TrendingUp, Sparkles } from "lucide-react";

const features = [
  {
    icon: RefreshCw,
    title: "Real-time collaboration",
    description: "Sync with your team across the globe instantly.",
    color: "oklch(0.56 0.08 196)",
  },
  {
    icon: TrendingUp,
    title: "Advanced analytics",
    description: "Data-driven insights to optimize your output.",
    color: "oklch(0.69 0.08 130)",
  },
  {
    icon: Sparkles,
    title: "Automated Task Management",
    description: "Let AI handle the routine while you focus on the big picture.",
    color: "oklch(0.52 0.12 310)",
  },
];

export default function AuthLayout() {
  return (
    <div className="auth-layout flex min-h-screen">

      {/* Left panel */}
      <div className="auth-panel relative hidden lg:flex lg:w-1/2 items-center justify-center overflow-hidden ">

        <div className="relative z-10 max-w-lg px-12">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-12">
            <div className="bg-primary p-2 rounded-lg shadow-[0_4px_16px_rgba(0,0,0,0.4),0_0_30px_8px_oklch(0.50_0.18_251/30%),inset_0_1px_0_rgba(255,255,255,0.25)]">
              <svg className="w-8 h-8 text-background" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path clipRule="evenodd" d="M24 4H6V17.3333V30.6667H24V44H42V30.6667V17.3333H24V4Z" fill="currentColor" fillRule="evenodd" />
              </svg>
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">Sophikon</span>
          </div>

          {/* Headline */}
          <h1 className="text-5xl font-bold leading-tight text-white mb-6">
            Empower Your <span className="text-primary">Workflow</span>
          </h1>
          <p className="text-muted-foreground text-lg mb-10 leading-relaxed">
            The next generation of project management. Built for speed, designed for clarity, and engineered for teams that deliver.
          </p>

          {/* Features */}
          <ul className="space-y-6">
            {features.map(({ icon: Icon, title, description, color }) => (
              <li key={title} className="flex items-center gap-4">
                <div
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
                  style={{ background: `color-mix(in oklch, ${color} 15%, transparent)`, border: `1px solid color-mix(in oklch, ${color} 30%, transparent)` }}
                >
                  <Icon className="size-5" style={{ color }} />
                </div>
                <div>
                  <p className="font-semibold text-white">{title}</p>
                  <p className="text-sm text-muted-foreground">{description}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Right panel */}
      <div className="auth-form-side flex w-full lg:w-1/2 items-center justify-center p-8">
        <div className="w-full max-w-md gradient-border bg-transparent backdrop-blur-xl rounded-2xl p-8 shadow-[0_0_120px_40px_oklch(0.50_0.18_251/10%)]">
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
