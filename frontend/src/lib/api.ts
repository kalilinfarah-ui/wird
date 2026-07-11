import axios from "axios";
import { getSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT on every request
api.interceptors.request.use(async (config) => {
  const session = await getSession();
  if (session?.accessToken) {
    config.headers.Authorization = `Bearer ${session.accessToken}`;
  }
  return config;
});

// ─── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { full_name: string; email: string; password: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  telegramLogin: (data: object) => api.post("/auth/telegram", data),
};

// ─── Classes ─────────────────────────────────────────────────────────────────
export const classesApi = {
  list: () => api.get("/classes/"),
  create: (data: object) => api.post("/classes/", data),
  get: (id: string) => api.get(`/classes/${id}`),
  update: (id: string, data: object) => api.put(`/classes/${id}`, data),
  delete: (id: string) => api.delete(`/classes/${id}`),
  students: (id: string) => api.get(`/classes/${id}/students`),
  setWebhook: (id: string) => api.post(`/classes/${id}/set-webhook`),
};

// ─── Attendance ───────────────────────────────────────────────────────────────
export const attendanceApi = {
  today: (classId: string) => api.get(`/attendance/${classId}/today`),
  stats: (classId: string) => api.get(`/attendance/${classId}/stats`),
  history: (classId: string, days = 30) =>
    api.get(`/attendance/${classId}/history?days=${days}`),
  manualComplete: (classId: string, studentId: string) =>
    api.post(`/attendance/${classId}/manual-complete?student_id=${studentId}`),
  studentHistory: (classId: string, studentId: string, days = 30) =>
    api.get(`/attendance/${classId}/student/${studentId}?days=${days}`),
};

// ─── Wird ─────────────────────────────────────────────────────────────────────
export const wirdApi = {
  create: (data: object) => api.post("/wird/", data),
  today: (classId: string) => api.get(`/wird/${classId}/today`),
  history: (classId: string, days = 30) =>
    api.get(`/wird/${classId}/history?days=${days}`),
  sendNow: (wirdId: string) => api.post(`/wird/${wirdId}/send-now`),
};

// ─── Reports ──────────────────────────────────────────────────────────────────
export const reportsApi = {
  weekly: (classId: string) => api.get(`/reports/${classId}/weekly`),
  monthly: (classId: string) => api.get(`/reports/${classId}/monthly`),
  range: (classId: string, start: string, end: string) =>
    api.get(`/reports/${classId}/range?start=${start}&end=${end}`),
  topStudents: (classId: string, limit = 10) =>
    api.get(`/reports/${classId}/top-students?limit=${limit}`),
  exportCsv: (classId: string) =>
    `${API_URL}/reports/${classId}/export/csv`,
};
