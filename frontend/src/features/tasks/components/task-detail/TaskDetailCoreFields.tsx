import { Input } from "@/shared/ui/input";
import { Textarea } from "@/shared/ui/textarea";
import { ColorPicker } from "@/shared/components/ColorPicker";
import type { Task, TaskUpdate } from "@/features/tasks/types";

interface TaskDetailCoreFieldsProps {
    task: Task;
    localData: Partial<TaskUpdate>;
    setLocalData: (data: Partial<TaskUpdate>) => void;
    handleBlur: (field: keyof TaskUpdate) => void;
    onColorChange?: (color: string | null) => void;
}

export function TaskDetailCoreFields({
    task,
    localData,
    setLocalData,
    handleBlur,
    onColorChange,
}: TaskDetailCoreFieldsProps) {
    return (
        <div className="mt-1 space-y-6">
            <div className="grid grid-cols-2 gap-x-4 gap-y-5">
                {/* % Complete */}
                <div className="space-y-2">
                    <label htmlFor="percent_complete" className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        % Complete
                    </label>
                    <div className="relative flex items-center">
                        <Input
                            id="percent_complete"
                            type="number"
                            min={0}
                            max={100}
                            value={localData.percent_complete ?? 0}
                            onChange={(e) => setLocalData({ ...localData, percent_complete: Number(e.target.value) })}
                            // NOTE: Auto-save pattern: text inputs commit on blur to prevent spamming the backend
                            onBlur={() => handleBlur("percent_complete")}
                            className="pr-8"
                        />
                        <span className="pointer-events-none absolute right-3 text-sm text-muted-foreground">%</span>
                    </div>
                </div>

                {/* Start Date */}
                <div className="space-y-2">
                    <label htmlFor="start_date" className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Start Date
                    </label>
                    <Input
                        id="start_date"
                        type="date"
                        value={localData.start_date ?? ""}
                        onChange={(e) => setLocalData({ ...localData, start_date: e.target.value })}
                        onBlur={() => handleBlur("start_date")}
                    />
                </div>

                {/* Duration */}
                <div className="col-span-2 space-y-2 sm:col-span-1">
                    <label htmlFor="duration" className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Duration
                        <span className="rounded border px-1.5 py-0.5 text-[10px] font-medium normal-case text-muted-foreground">mins</span>
                    </label>
                    <Input
                        id="duration"
                        type="number"
                        value={localData.duration ?? 0}
                        onChange={(e) => setLocalData({ ...localData, duration: Number(e.target.value) })}
                        onBlur={() => handleBlur("duration")}
                        disabled={task.is_summary}
                    />
                </div>

                {/* Color (summary tasks only) */}
                {task.is_summary && (
                    <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                            Gantt Color
                        </label>
                        <ColorPicker
                            value={task.color ?? null}
                            // NOTE: Auto-save pattern: discrete selects commit immediately
                            onChange={(color) => onColorChange?.(color)}
                        />
                    </div>
                )}
            </div>

            {/* Notes */}
            <div className="space-y-2.5 pt-1">
                <label htmlFor="notes" className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Notes
                </label>
                <Textarea
                    id="notes"
                    placeholder="Add task notes..."
                    value={localData.notes ?? ""}
                    onChange={(e) => setLocalData({ ...localData, notes: e.target.value })}
                    onBlur={() => handleBlur("notes")}
                    className="min-h-[112px] resize-y leading-relaxed"
                />
            </div>
        </div>
    );
}
