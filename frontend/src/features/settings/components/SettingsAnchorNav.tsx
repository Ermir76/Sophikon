import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { cn } from "@/shared/lib/utils";

const BASE_SECTIONS = [
  { id: "profile", label: "Profile" },
  { id: "security", label: "Security" },
  { id: "notifications", label: "Notifications" },
  { id: "ai-preferences", label: "AI Preferences" },
  { id: "general", label: "General" },
  { id: "members", label: "Members" },
  { id: "billing", label: "Billing" },
] as const;

interface SettingsAnchorNavProps {
  activeSection: string;
  onSectionClick: (id: string) => void;
  isAdminOrOwner: boolean;
}

export function SettingsAnchorNav({
  activeSection,
  onSectionClick,
  isAdminOrOwner,
}: SettingsAnchorNavProps) {
  const sections = BASE_SECTIONS.filter((section) => {
    if (!isAdminOrOwner && (section.id === "general" || section.id === "members")) {
      return false;
    }
    return true;
  });

  return (
    <>
      <nav className="hidden px-4 pb-4 pt-6 md:sticky md:top-6 md:block" aria-label="Settings sections">
        <h2 className="mb-4 text-2xl font-semibold text-foreground">Settings</h2>
        <div className="mb-3 border-t" />
        {sections.map((section) => (
          <div key={section.id}>
            <Button
              type="button"
              variant="ghost"
              className={cn(
                "mb-1 h-9 w-full justify-start text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                activeSection === section.id &&
                  "bg-accent text-accent-foreground hover:bg-accent hover:text-accent-foreground",
                section.id === "billing" && "text-muted-foreground/80",
              )}
              onClick={() => onSectionClick(section.id)}
            >
              <span>{section.label}</span>
              {section.id === "billing" ? (
                <Badge variant="outline" className="ml-2 h-5 rounded-sm px-1.5 text-[10px]">
                  Soon
                </Badge>
              ) : null}
            </Button>
            {section.id === "ai-preferences" ? <div className="my-3 border-t" /> : null}
          </div>
        ))}
      </nav>

      <nav
        className="sticky top-16 z-20 -mx-2 overflow-x-auto border-y bg-background/95 px-2 py-2 backdrop-blur md:hidden"
        aria-label="Settings sections"
      >
        <div className="flex w-max items-center gap-2">
          {sections.map((section) => (
            <div key={section.id} className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                variant="outline"
                className={cn(
                  "h-7 whitespace-nowrap rounded-full px-3 text-xs hover:bg-accent hover:text-accent-foreground",
                  activeSection === section.id &&
                    "border-border bg-accent text-accent-foreground hover:bg-accent hover:text-accent-foreground",
                )}
                onClick={() => onSectionClick(section.id)}
              >
                {section.id === "notifications" ? "Notifs" : section.label}
              </Button>
              {section.id === "billing" ? <span className="text-xs text-muted-foreground">Soon</span> : null}
              {section.id === "ai-preferences" ? <span className="text-xs text-muted-foreground">|</span> : null}
            </div>
          ))}
          <span className="text-xs text-muted-foreground">...</span>
        </div>
      </nav>
    </>
  );
}
