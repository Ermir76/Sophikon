import { useState } from "react";
import { Loader2 } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/shared/ui/dialog";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { useCreateResource } from "@/features/resources/hooks/useResources";
import { useCalendars } from "@/features/calendar";
import { toast } from "sonner";
import type { ResourceType } from "@/features/resources/types";

interface CreateResourceDialogProps {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
}

export function CreateResourceDialog({ projectId, isOpen, onClose }: CreateResourceDialogProps) {
    const [name, setName] = useState("");
    const [type, setType] = useState<ResourceType>("WORK");
    const [initials, setInitials] = useState("");
    const [email, setEmail] = useState("");
    const [calendarId, setCalendarId] = useState<string | null>(null);

    const createResource = useCreateResource(projectId);
    const calendarsQuery = useCalendars(projectId);
    const calendars = calendarsQuery.data ?? [];

    const resetForm = () => {
        setName("");
        setType("WORK");
        setInitials("");
        setEmail("");
        setCalendarId(null);
    };

    const handleSubmit = () => {
        if (!name.trim()) {
            toast.error("Resource name is required");
            return;
        }

        createResource.mutate(
            {
                name: name.trim(),
                type,
                initials: initials.trim() || undefined,
                email: email.trim() || undefined,
                calendar_id: calendarId,
            },
            {
                onSuccess: () => {
                    toast.success("Resource created");
                    resetForm();
                    onClose();
                },
                onError: () => {
                    toast.error("Failed to create resource");
                },
            }
        );
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => { if (!open) { resetForm(); onClose(); } }}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Add Resource</DialogTitle>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="space-y-2">
                        <label htmlFor="res-name" className="text-sm font-medium">Name</label>
                        <Input
                            id="res-name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder={
                                type === "WORK" ? "e.g. John Smith" :
                                    type === "MATERIAL" ? "e.g. Concrete" :
                                        "e.g. Travel Expenses"
                            }
                            autoFocus
                        />
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="res-type" className="text-sm font-medium">Type</label>
                        <Select value={type} onValueChange={(v) => setType(v as ResourceType)}>
                            <SelectTrigger id="res-type">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="WORK">Work (People)</SelectItem>
                                <SelectItem value="MATERIAL">Material (Consumables)</SelectItem>
                                <SelectItem value="COST">Cost (Fixed)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="res-calendar" className="text-sm font-medium">Calendar</label>
                        <Select
                            value={calendarId ?? "none"}
                            onValueChange={(value) => setCalendarId(value === "none" ? null : value)}
                            disabled={calendarsQuery.isLoading}
                        >
                            <SelectTrigger id="res-calendar">
                                <SelectValue placeholder="Project default" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="none">Project default</SelectItem>
                                {calendars.map((calendar) => (
                                    <SelectItem key={calendar.id} value={calendar.id}>
                                        {calendar.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="res-initials" className="text-sm font-medium">Initials</label>
                        <Input
                            id="res-initials"
                            value={initials}
                            onChange={(e) => setInitials(e.target.value)}
                            placeholder={
                                type === "WORK" ? "e.g. JS" :
                                    type === "MATERIAL" ? "e.g. CON" :
                                        "e.g. TRV"
                            }
                            maxLength={10}
                        />
                    </div>

                    {type === "WORK" && (
                        <div className="space-y-2">
                            <label htmlFor="res-email" className="text-sm font-medium">Email</label>
                            <Input
                                id="res-email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="john@example.com"
                            />
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => { resetForm(); onClose(); }}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={!name.trim() || createResource.isPending}
                    >
                        {createResource.isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
                        Add
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
