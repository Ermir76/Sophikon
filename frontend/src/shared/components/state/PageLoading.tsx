import { Loader2 } from "lucide-react";

interface PageLoadingProps {
    message?: string;
}

/**
 * Standardized full-page loading state.
 * Centers a spinner and an optional message within the available vertical space.
 */
export function PageLoading({ message = "Loading..." }: PageLoadingProps) {
    return (
        <div className="flex flex-col flex-1 items-center justify-center p-12 text-center animate-in fade-in-50 duration-500">
            <Loader2 className="size-8 animate-spin text-muted-foreground mb-4" />
            <p className="text-sm text-muted-foreground font-medium">{message}</p>
        </div>
    );
}
