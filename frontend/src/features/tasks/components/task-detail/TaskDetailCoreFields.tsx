import { Input } from "@/shared/ui/input";
import { Textarea } from "@/shared/ui/textarea";
import type { Task, TaskUpdate } from "@/features/tasks/types";

interface TaskDetailCoreFieldsProps {
    task: Task;
    localData: Partial<TaskUpdate>;
    setLocalData: (data: Partial<TaskUpdate>) => void;
    handleBlur: (field: keyof TaskUpdate) => void;
}

export function TaskDetailCoreFields({
    task,
    localData,
    setLocalData,
    handleBlur
}: TaskDetailCoreFieldsProps) {
    return (
        <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                    <label htmlFor="percent_complete" className="text-sm font-medium">% Complete</label>
                    <div className="flex items-center gap-2">
                        <Input
                            id="percent_complete"
                            type="number"
                            min={0}
                            max={100}
                            value={localData.percent_complete ?? 0}
                            onChange={(e) => setLocalData({ ...localData, percent_complete: Number(e.target.value) })}
                            onBlur={() => handleBlur("percent_complete")}
                        />
                        <span className="text-sm text-muted-foreground">%</span>
                    </div>
                </div>

                <div className="space-y-2">
                    <label htmlFor="start_date" className="text-sm font-medium">Start Date</label>
                    <Input
                        id="start_date"
                        type="date"
                        value={localData.start_date ?? ""}
                        onChange={(e) => setLocalData({ ...localData, start_date: e.target.value })}
                        onBlur={() => handleBlur("start_date")}
                    />
                </div>

                <div className="space-y-2">
                    <label htmlFor="duration" className="text-sm font-medium">Duration (mins)</label>
                    <Input
                        id="duration"
                        type="number"
                        value={localData.duration ?? 0}
                        onChange={(e) => setLocalData({ ...localData, duration: Number(e.target.value) })}
                        onBlur={() => handleBlur("duration")}
                        disabled={task.is_summary}
                    />
                </div>
            </div>

            {/* Notes */}
            <div className="space-y-2">
                <label htmlFor="notes" className="text-sm font-medium">Notes</label>
                <Textarea
                    id="notes"
                    placeholder="Add task notes..."
                    value={localData.notes ?? ""}
                    onChange={(e) => setLocalData({ ...localData, notes: e.target.value })}
                    onBlur={() => handleBlur("notes")}
                    className="min-h-[120px] resize-y"
                />
            </div>
        </div>
    );
}
