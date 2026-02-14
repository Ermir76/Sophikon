import { Loader2 } from "lucide-react";

export function PageLoader() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <Loader2 className="size-10 animate-spin text-primary" />
    </div>
  );
}
