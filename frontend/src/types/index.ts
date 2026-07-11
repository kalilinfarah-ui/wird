export interface User {
  id: string;
  full_name: string;
  email?: string;
  role: "super_admin" | "teacher" | "assistant";
  telegram_id?: number;
  telegram_username?: string;
}

export interface ClassGroup {
  id: string;
  name: string;
  description?: string;
  telegram_chat_id?: number;
  telegram_chat_title?: string;
  wird_time: string;
  timezone: string;
  reminders_enabled: boolean;
  reminder_1_hours: string;
  reminder_2_hours: string;
  reminder_3_time: string;
  is_active: boolean;
  created_at: string;
}

export interface Student {
  id: string;
  full_name: string;
  telegram_username?: string;
  telegram_id: number;
  current_streak: number;
  longest_streak: number;
  total_completed: number;
  total_missed: number;
  completion_percentage: number;
  joined_at: string;
}

export interface AttendanceRecord {
  student_id: string;
  full_name: string;
  telegram_username?: string;
  telegram_id: number;
  completed: boolean;
  completed_at?: string;
  method?: string;
  current_streak: number;
  completion_percentage: number;
}

export interface AttendanceStats {
  total_students: number;
  today_completed: number;
  today_pending: number;
  completion_rate: number;
}

export interface DailyWird {
  id: string;
  class_id: string;
  wird_date: string;
  title: string;
  content?: string;
  file_url?: string;
  file_type?: string;
  wird_type: string;
  status: "scheduled" | "sent" | "failed";
  sent_at?: string;
  telegram_message_id?: number;
  is_holiday: boolean;
}

export interface ReportDay {
  date: string;
  title: string;
  completed: number;
  total: number;
  rate: number;
}

export interface Report {
  start: string;
  end: string;
  total_students: number;
  total_days: number;
  average_completion_rate: number;
  daily: ReportDay[];
}
