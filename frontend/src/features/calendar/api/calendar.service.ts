import { api } from "@/shared/api/api";
import type {
  Calendar,
  CalendarCreate,
  CalendarException,
  CalendarExceptionCreate,
  CalendarExceptionUpdate,
  CalendarUpdate,
} from "@/features/calendar/types";

export const calendarService = {
  list: async (projectId: string) => {
    const response = await api.get<Calendar[]>(`/projects/${projectId}/calendars`);
    return response.data;
  },

  create: async (projectId: string, data: CalendarCreate) => {
    const response = await api.post<Calendar>(`/projects/${projectId}/calendars`, data);
    return response.data;
  },

  update: async (projectId: string, calendarId: string, data: CalendarUpdate) => {
    const response = await api.patch<Calendar>(
      `/projects/${projectId}/calendars/${calendarId}`,
      data,
    );
    return response.data;
  },

  delete: async (projectId: string, calendarId: string) => {
    await api.delete(`/projects/${projectId}/calendars/${calendarId}`);
  },

  listExceptions: async (projectId: string, calendarId: string) => {
    const response = await api.get<CalendarException[]>(
      `/projects/${projectId}/calendars/${calendarId}/exceptions`,
    );
    return response.data;
  },

  createException: async (
    projectId: string,
    calendarId: string,
    data: CalendarExceptionCreate,
  ) => {
    const response = await api.post<CalendarException>(
      `/projects/${projectId}/calendars/${calendarId}/exceptions`,
      data,
    );
    return response.data;
  },

  updateException: async (
    projectId: string,
    calendarId: string,
    exceptionId: string,
    data: CalendarExceptionUpdate,
  ) => {
    const response = await api.patch<CalendarException>(
      `/projects/${projectId}/calendars/${calendarId}/exceptions/${exceptionId}`,
      data,
    );
    return response.data;
  },

  deleteException: async (
    projectId: string,
    calendarId: string,
    exceptionId: string,
  ) => {
    await api.delete(
      `/projects/${projectId}/calendars/${calendarId}/exceptions/${exceptionId}`,
    );
  },
};
