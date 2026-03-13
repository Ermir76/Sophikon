import { useEffect, useMemo, useState } from "react";
import { Navigate, useParams } from "react-router";
import { CalendarDays, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { useAuthStore } from "@/features/auth/store/auth-store";
import {
  useCalendarExceptions,
  useCalendars,
  useCreateCalendar,
  useCreateCalendarException,
  useDeleteCalendar,
  useDeleteCalendarException,
  useUpdateCalendar,
  useUpdateCalendarException,
} from "@/features/calendar";
import type {
  Calendar,
  CalendarCreate,
  CalendarException,
  CalendarExceptionCreate,
  WorkDay,
} from "@/features/calendar";
import { useProjectMembers } from "@/features/projects/hooks/useProjectMembers";
import { useProject, useUpdateProject } from "@/features/projects/hooks/useProjects";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Switch } from "@/shared/ui/switch";
import { QueryError } from "@/shared/components/QueryError";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageEmpty } from "@/shared/components/state/PageEmpty";
import { PageLoading } from "@/shared/components/state/PageLoading";

const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const DEFAULT_DAY: WorkDay = { start: "09:00", end: "17:00", breaks: [] };

function buildDefaultWorkWeek(): Array<WorkDay | null> {
  return [
    null,
    { ...DEFAULT_DAY, breaks: [] },
    { ...DEFAULT_DAY, breaks: [] },
    { ...DEFAULT_DAY, breaks: [] },
    { ...DEFAULT_DAY, breaks: [] },
    { ...DEFAULT_DAY, breaks: [] },
    null,
  ];
}

function cloneWeek(week?: Array<WorkDay | null> | null): Array<WorkDay | null> {
  if (!week || week.length !== 7) return buildDefaultWorkWeek();
  return week.map((day) =>
    day
      ? {
          start: day.start,
          end: day.end,
          breaks: day.breaks.map((breakItem) => ({
            start: breakItem.start,
            end: breakItem.end,
          })),
        }
      : null,
  );
}

function toCalendarPayload(
  name: string,
  isBase: boolean,
  baseCalendarId: string | null,
  week: Array<WorkDay | null>,
): CalendarCreate {
  return {
    name: name.trim(),
    is_base: isBase,
    base_calendar_id: baseCalendarId,
    work_week: cloneWeek(week),
  };
}

export default function CalendarPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const currentUserId = useAuthStore((state) => state.user?.id ?? null);

  const { data: project, isLoading: isProjectLoading } = useProject(projectId);
  const membersQuery = useProjectMembers(projectId);
  const calendarsQuery = useCalendars(projectId);
  const createCalendar = useCreateCalendar(projectId);
  const updateCalendar = useUpdateCalendar(projectId);
  const deleteCalendar = useDeleteCalendar(projectId);
  const createException = useCreateCalendarException(projectId);
  const updateException = useUpdateCalendarException(projectId);
  const deleteException = useDeleteCalendarException(projectId);
  const updateProject = useUpdateProject(projectId);

  const [selectedCalendarId, setSelectedCalendarId] = useState<string | null>(null);
  const [calendarDialogOpen, setCalendarDialogOpen] = useState(false);
  const [calendarEditing, setCalendarEditing] = useState<Calendar | null>(null);
  const [calendarName, setCalendarName] = useState("");
  const [calendarIsBase, setCalendarIsBase] = useState(false);
  const [calendarBaseId, setCalendarBaseId] = useState<string | null>(null);
  const [calendarWeek, setCalendarWeek] = useState<Array<WorkDay | null>>(buildDefaultWorkWeek());

  const [exceptionDialogOpen, setExceptionDialogOpen] = useState(false);
  const [exceptionEditing, setExceptionEditing] = useState<CalendarException | null>(null);
  const [exceptionName, setExceptionName] = useState("");
  const [exceptionStartDate, setExceptionStartDate] = useState("");
  const [exceptionEndDate, setExceptionEndDate] = useState("");
  const [exceptionIsWorking, setExceptionIsWorking] = useState(false);
  const [exceptionStartTime, setExceptionStartTime] = useState("09:00");
  const [exceptionEndTime, setExceptionEndTime] = useState("17:00");

  const exceptionsQuery = useCalendarExceptions(projectId, selectedCalendarId);

  const calendars = calendarsQuery.data ?? [];
  const selectedCalendar = useMemo(
    () => calendars.find((calendar) => calendar.id === selectedCalendarId) ?? null,
    [calendars, selectedCalendarId],
  );

  useEffect(() => {
    if (!selectedCalendarId && calendars.length > 0) {
      setSelectedCalendarId(calendars[0].id);
    }
    if (
      selectedCalendarId &&
      calendars.length > 0 &&
      !calendars.some((calendar) => calendar.id === selectedCalendarId)
    ) {
      setSelectedCalendarId(calendars[0].id);
    }
    if (calendars.length === 0) {
      setSelectedCalendarId(null);
    }
  }, [calendars, selectedCalendarId]);

  const memberRole = membersQuery.data?.items.find(
    (member) => member.user_id === currentUserId,
  )?.role;
  const canManageCalendars =
    (project?.owner_id ?? null) === currentUserId || memberRole === "manager";

  const openCreateCalendar = () => {
    setCalendarEditing(null);
    setCalendarName("");
    setCalendarIsBase(false);
    setCalendarBaseId(null);
    setCalendarWeek(buildDefaultWorkWeek());
    setCalendarDialogOpen(true);
  };

  const openEditCalendar = (calendar: Calendar) => {
    setCalendarEditing(calendar);
    setCalendarName(calendar.name);
    setCalendarIsBase(calendar.is_base);
    setCalendarBaseId(calendar.base_calendar_id);
    setCalendarWeek(cloneWeek(calendar.work_week));
    setCalendarDialogOpen(true);
  };

  const submitCalendar = async () => {
    if (!calendarName.trim()) {
      toast.error("Calendar name is required");
      return;
    }

    const payload = toCalendarPayload(
      calendarName,
      calendarIsBase,
      calendarBaseId,
      calendarWeek,
    );
    try {
      if (calendarEditing) {
        await updateCalendar.mutateAsync({
          calendarId: calendarEditing.id,
          payload,
        });
        toast.success("Calendar updated");
      } else {
        const created = await createCalendar.mutateAsync(payload);
        setSelectedCalendarId(created.id);
        toast.success("Calendar created");
      }
      setCalendarDialogOpen(false);
    } catch {
      toast.error("Failed to save calendar");
    }
  };

  const handleDeleteCalendar = async (calendarId: string) => {
    try {
      await deleteCalendar.mutateAsync(calendarId);
      toast.success("Calendar deleted");
    } catch {
      toast.error("Failed to delete calendar");
    }
  };

  const openCreateException = () => {
    setExceptionEditing(null);
    setExceptionName("");
    setExceptionStartDate("");
    setExceptionEndDate("");
    setExceptionIsWorking(false);
    setExceptionStartTime("09:00");
    setExceptionEndTime("17:00");
    setExceptionDialogOpen(true);
  };

  const openEditException = (exception: CalendarException) => {
    setExceptionEditing(exception);
    setExceptionName(exception.name);
    setExceptionStartDate(exception.start_date);
    setExceptionEndDate(exception.end_date);
    setExceptionIsWorking(exception.is_working);
    setExceptionStartTime(exception.work_times?.start ?? "09:00");
    setExceptionEndTime(exception.work_times?.end ?? "17:00");
    setExceptionDialogOpen(true);
  };

  const submitException = async () => {
    if (!selectedCalendarId) return;
    if (!exceptionName.trim() || !exceptionStartDate || !exceptionEndDate) {
      toast.error("Exception name and date range are required");
      return;
    }

    const payload: CalendarExceptionCreate = {
      name: exceptionName.trim(),
      start_date: exceptionStartDate,
      end_date: exceptionEndDate,
      is_working: exceptionIsWorking,
      work_times: exceptionIsWorking
        ? { start: exceptionStartTime, end: exceptionEndTime, breaks: [] }
        : null,
      recurrence: null,
    };

    try {
      if (exceptionEditing) {
        await updateException.mutateAsync({
          calendarId: selectedCalendarId,
          exceptionId: exceptionEditing.id,
          payload,
        });
        toast.success("Exception updated");
      } else {
        await createException.mutateAsync({
          calendarId: selectedCalendarId,
          payload,
        });
        toast.success("Exception created");
      }
      setExceptionDialogOpen(false);
    } catch {
      toast.error("Failed to save exception");
    }
  };

  const handleDeleteException = async (exceptionId: string) => {
    if (!selectedCalendarId) return;
    try {
      await deleteException.mutateAsync({
        calendarId: selectedCalendarId,
        exceptionId,
      });
      toast.success("Exception deleted");
    } catch {
      toast.error("Failed to delete exception");
    }
  };

  const handleDefaultCalendarChange = async (value: string) => {
    if (!projectId) return;
    const defaultCalendarId = value === "none" ? null : value;
    try {
      await updateProject.mutateAsync({ default_calendar_id: defaultCalendarId });
      toast.success("Default calendar updated");
    } catch {
      toast.error("Failed to update default calendar");
    }
  };

  const updateDayEnabled = (index: number, enabled: boolean) => {
    setCalendarWeek((prev) => {
      const next = cloneWeek(prev);
      next[index] = enabled ? { ...DEFAULT_DAY, breaks: [] } : null;
      return next;
    });
  };

  const updateDayTime = (
    index: number,
    field: "start" | "end",
    value: string,
  ) => {
    setCalendarWeek((prev) => {
      const next = cloneWeek(prev);
      const current = next[index];
      if (!current) return next;
      next[index] = { ...current, [field]: value };
      return next;
    });
  };

  if (!projectId) {
    return <Navigate to="/projects" replace />;
  }

  if (calendarsQuery.isError) {
    return (
      <PageShell className="h-full overflow-y-auto">
        <QueryError
          message="Failed to load calendars."
          onRetry={() => calendarsQuery.refetch()}
        />
      </PageShell>
    );
  }

  return (
    <PageShell className="h-full overflow-y-auto">
      <PageHeader
        title="Calendar"
        description="Manage working weeks, exceptions, and project default calendar."
        action={
          <Button
            size="sm"
            className="h-8 gap-1.5 px-3 text-xs"
            disabled={!canManageCalendars}
            onClick={openCreateCalendar}
          >
            <Plus className="size-4" />
            New Calendar
          </Button>
        }
      />

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Project Default Calendar</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <Label htmlFor="default-calendar" className="text-xs text-muted-foreground">
            Default
          </Label>
          <Select
            value={project?.default_calendar_id ?? "none"}
            onValueChange={handleDefaultCalendarChange}
            disabled={!canManageCalendars || isProjectLoading || updateProject.isPending}
          >
            <SelectTrigger id="default-calendar" className="w-[280px]">
              <SelectValue placeholder="Select default calendar" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None (system default)</SelectItem>
              {calendars.map((calendar) => (
                <SelectItem key={calendar.id} value={calendar.id}>
                  {calendar.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {calendarsQuery.isLoading ? (
        <PageLoading />
      ) : calendars.length === 0 ? (
        <PageEmpty
          icon={CalendarDays}
          title="No calendars yet"
          description="Create your first project calendar to define working days and exceptions."
          action={
            <Button variant="outline" onClick={openCreateCalendar} disabled={!canManageCalendars}>
              Create calendar
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Calendars</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {calendars.map((calendar) => (
                <div
                  key={calendar.id}
                  className={`rounded-md border px-3 py-2 ${
                    selectedCalendarId === calendar.id
                      ? "border-primary bg-accent/40"
                      : "border-border"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <button
                      type="button"
                      className="min-w-0 text-left"
                      onClick={() => setSelectedCalendarId(calendar.id)}
                    >
                      <p className="truncate text-sm font-medium">{calendar.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {calendar.project_id ? "Project calendar" : "Global base calendar"}
                        {calendar.base_calendar_id ? " - inherited" : ""}
                      </p>
                    </button>
                    {canManageCalendars ? (
                      <div className="flex items-center gap-1">
                        <Button
                          size="icon"
                          variant="ghost"
                          className="size-8"
                          onClick={() => openEditCalendar(calendar)}
                        >
                          <Pencil className="size-4" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="size-8 text-destructive"
                          onClick={() => handleDeleteCalendar(calendar.id)}
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                    ) : null}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Exceptions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {selectedCalendar ? (
                <>
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-muted-foreground">
                      Calendar: <span className="font-medium text-foreground">{selectedCalendar.name}</span>
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={openCreateException}
                      disabled={!canManageCalendars}
                    >
                      <Plus className="mr-1 size-3.5" />
                      Add exception
                    </Button>
                  </div>

                  {exceptionsQuery.isLoading ? (
                    <PageLoading />
                  ) : (exceptionsQuery.data ?? []).length === 0 ? (
                    <p className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
                      No exceptions configured.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {(exceptionsQuery.data ?? []).map((exception) => (
                        <div key={exception.id} className="rounded-md border px-3 py-2">
                          <div className="flex items-center justify-between gap-2">
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium">{exception.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {exception.start_date} {"->"} {exception.end_date} {"- "}
                                {exception.is_working ? "Working day override" : "Holiday"}
                              </p>
                            </div>
                            {canManageCalendars ? (
                              <div className="flex items-center gap-1">
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="size-8"
                                  onClick={() => openEditException(exception)}
                                >
                                  <Pencil className="size-4" />
                                </Button>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="size-8 text-destructive"
                                  onClick={() => handleDeleteException(exception.id)}
                                >
                                  <Trash2 className="size-4" />
                                </Button>
                              </div>
                            ) : null}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <p className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
                  Select a calendar to manage exceptions.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      <Dialog open={calendarDialogOpen} onOpenChange={setCalendarDialogOpen}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{calendarEditing ? "Edit calendar" : "Create calendar"}</DialogTitle>
            <DialogDescription>
              Configure working days, inheritance, and base calendar settings.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="calendar-name">Name</Label>
              <Input
                id="calendar-name"
                value={calendarName}
                onChange={(event) => setCalendarName(event.target.value)}
                placeholder="Calendar name"
              />
            </div>

            <div className="flex items-center justify-between rounded-md border px-3 py-2">
              <div>
                <p className="text-sm font-medium">Base calendar template</p>
                <p className="text-xs text-muted-foreground">
                  Mark as template available for inheritance.
                </p>
              </div>
              <Switch checked={calendarIsBase} onCheckedChange={setCalendarIsBase} />
            </div>

            <div className="space-y-2">
              <Label>Base calendar reference</Label>
              <Select
                value={calendarBaseId ?? "none"}
                onValueChange={(value) => setCalendarBaseId(value === "none" ? null : value)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="None" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  {calendars
                    .filter((calendar) => !calendarEditing || calendar.id !== calendarEditing.id)
                    .map((calendar) => (
                      <SelectItem key={calendar.id} value={calendar.id}>
                        {calendar.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium">Work week</p>
              <div className="space-y-2">
                {DAY_NAMES.map((dayName, index) => {
                  const day = calendarWeek[index];
                  const enabled = day !== null;
                  return (
                    <div key={dayName} className="grid grid-cols-[70px_56px_1fr_1fr] items-center gap-2">
                      <span className="text-sm">{dayName}</span>
                      <Switch
                        checked={enabled}
                        onCheckedChange={(value) => updateDayEnabled(index, value)}
                      />
                      <Input
                        type="time"
                        value={day?.start ?? "09:00"}
                        disabled={!enabled}
                        onChange={(event) => updateDayTime(index, "start", event.target.value)}
                      />
                      <Input
                        type="time"
                        value={day?.end ?? "17:00"}
                        disabled={!enabled}
                        onChange={(event) => updateDayTime(index, "end", event.target.value)}
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setCalendarDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={submitCalendar}
                disabled={createCalendar.isPending || updateCalendar.isPending}
              >
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={exceptionDialogOpen} onOpenChange={setExceptionDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {exceptionEditing ? "Edit calendar exception" : "Create calendar exception"}
            </DialogTitle>
            <DialogDescription>
              Add holiday or working-day overrides for this calendar.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="exception-name">Name</Label>
              <Input
                id="exception-name"
                value={exceptionName}
                onChange={(event) => setExceptionName(event.target.value)}
                placeholder="Holiday / Special day"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="exception-start-date">Start date</Label>
                <Input
                  id="exception-start-date"
                  type="date"
                  value={exceptionStartDate}
                  onChange={(event) => setExceptionStartDate(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="exception-end-date">End date</Label>
                <Input
                  id="exception-end-date"
                  type="date"
                  value={exceptionEndDate}
                  onChange={(event) => setExceptionEndDate(event.target.value)}
                />
              </div>
            </div>

            <div className="flex items-center justify-between rounded-md border px-3 py-2">
              <div>
                <p className="text-sm font-medium">Working exception</p>
                <p className="text-xs text-muted-foreground">
                  Enable this to force working hours on normally non-working dates.
                </p>
              </div>
              <Switch checked={exceptionIsWorking} onCheckedChange={setExceptionIsWorking} />
            </div>

            {exceptionIsWorking ? (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="exception-start-time">Start time</Label>
                  <Input
                    id="exception-start-time"
                    type="time"
                    value={exceptionStartTime}
                    onChange={(event) => setExceptionStartTime(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="exception-end-time">End time</Label>
                  <Input
                    id="exception-end-time"
                    type="time"
                    value={exceptionEndTime}
                    onChange={(event) => setExceptionEndTime(event.target.value)}
                  />
                </div>
              </div>
            ) : null}

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setExceptionDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={submitException}
                disabled={createException.isPending || updateException.isPending}
              >
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </PageShell>
  );
}
