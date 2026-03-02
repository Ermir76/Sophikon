import { Outlet } from "react-router";

export function ProjectLayout() {
  return (
    <div className="flex flex-col h-full w-full min-w-0 min-h-0">
      <Outlet />
    </div>
  );
}
