import type { ReactNode } from "react";

interface SettingsLayoutProps {
  anchorNav: ReactNode;
  children: ReactNode;
}

export function SettingsLayout({ anchorNav, children }: SettingsLayoutProps) {
  return (
    <div className="space-y-4 md:grid md:grid-cols-[200px_minmax(0,1fr)] md:gap-6 md:space-y-0">
      <aside className="md:min-h-[calc(100vh-8rem)] md:border-r md:pr-6">{anchorNav}</aside>
      <div>{children}</div>
    </div>
  );
}
