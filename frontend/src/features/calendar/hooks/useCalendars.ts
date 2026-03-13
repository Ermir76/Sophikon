import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { calendarService } from "@/features/calendar/api/calendar.service";
import type {
  CalendarCreate,
  CalendarExceptionCreate,
  CalendarExceptionUpdate,
  CalendarUpdate,
} from "@/features/calendar/types";

export const calendarKeys = {
  all: ["calendars"] as const,
  list: (projectId: string | undefined) => [...calendarKeys.all, "list", projectId] as const,
  exceptions: (projectId: string | undefined, calendarId: string | null | undefined) =>
    [...calendarKeys.all, "exceptions", projectId, calendarId] as const,
};

export function useCalendars(projectId: string | undefined) {
  return useQuery({
    queryKey: calendarKeys.list(projectId),
    queryFn: () => calendarService.list(projectId!),
    enabled: !!projectId,
  });
}

export function useCreateCalendar(projectId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CalendarCreate) => {
      if (!projectId) throw new Error("No project ID");
      return calendarService.create(projectId, payload);
    },
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: calendarKeys.list(projectId) });
      }
    },
  });
}

export function useUpdateCalendar(projectId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ calendarId, payload }: { calendarId: string; payload: CalendarUpdate }) => {
      if (!projectId) throw new Error("No project ID");
      return calendarService.update(projectId, calendarId, payload);
    },
    onSuccess: (_, vars) => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: calendarKeys.list(projectId) });
        queryClient.invalidateQueries({
          queryKey: calendarKeys.exceptions(projectId, vars.calendarId),
        });
      }
    },
  });
}

export function useDeleteCalendar(projectId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (calendarId: string) => {
      if (!projectId) throw new Error("No project ID");
      return calendarService.delete(projectId, calendarId);
    },
    onSuccess: (_, calendarId) => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: calendarKeys.list(projectId) });
        queryClient.removeQueries({ queryKey: calendarKeys.exceptions(projectId, calendarId) });
      }
    },
  });
}

export function useCalendarExceptions(
  projectId: string | undefined,
  calendarId: string | null | undefined,
) {
  return useQuery({
    queryKey: calendarKeys.exceptions(projectId, calendarId),
    queryFn: () => calendarService.listExceptions(projectId!, calendarId!),
    enabled: !!projectId && !!calendarId,
  });
}

export function useCreateCalendarException(projectId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ calendarId, payload }: { calendarId: string; payload: CalendarExceptionCreate }) => {
      if (!projectId) throw new Error("No project ID");
      return calendarService.createException(projectId, calendarId, payload);
    },
    onSuccess: (_, vars) => {
      if (projectId) {
        queryClient.invalidateQueries({
          queryKey: calendarKeys.exceptions(projectId, vars.calendarId),
        });
      }
    },
  });
}

export function useUpdateCalendarException(projectId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      calendarId,
      exceptionId,
      payload,
    }: {
      calendarId: string;
      exceptionId: string;
      payload: CalendarExceptionUpdate;
    }) => {
      if (!projectId) throw new Error("No project ID");
      return calendarService.updateException(projectId, calendarId, exceptionId, payload);
    },
    onSuccess: (_, vars) => {
      if (projectId) {
        queryClient.invalidateQueries({
          queryKey: calendarKeys.exceptions(projectId, vars.calendarId),
        });
      }
    },
  });
}

export function useDeleteCalendarException(projectId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ calendarId, exceptionId }: { calendarId: string; exceptionId: string }) => {
      if (!projectId) throw new Error("No project ID");
      return calendarService.deleteException(projectId, calendarId, exceptionId);
    },
    onSuccess: (_, vars) => {
      if (projectId) {
        queryClient.invalidateQueries({
          queryKey: calendarKeys.exceptions(projectId, vars.calendarId),
        });
      }
    },
  });
}
