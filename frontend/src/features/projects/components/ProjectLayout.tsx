import { Outlet } from "react-router";

export function ProjectLayout() {
  return (
    <div className="flex flex-col h-full w-full">
      <Outlet />
    </div>
  );
}
