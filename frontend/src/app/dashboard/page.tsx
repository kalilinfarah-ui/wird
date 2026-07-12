"use client";
import { useQuery } from "@tanstack/react-query";
import { attendanceApi, reportsApi, classesApi, wirdApi } from "@/lib/api";
import StatsCard from "@/components/dashboard/StatsCard";
import CompletionChart from "@/components/charts/CompletionChart";
import AttendanceTable from "@/components/dashboard/AttendanceTable";
import { Users, CheckCircle, XCircle, TrendingUp, RefreshCw, BookOpen, Send } from "lucide-react";
import { useState } from "react";
import { ClassGroup, DailyWird, AttendanceStats } from "@/types";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { formatTime } from "@/lib/utils";

export default function DashboardPage() {
  const qc = useQueryClient();

  const { data: classes = [] } = useQuery<ClassGroup[]>({
    queryKey: ["classes"],
    queryFn: () => classesApi.list().then((r) => r.data),
  });

  const [selectedClass, setSelectedClass] = useState("");
  const classId = selectedClass || classes[0]?.id || "";

  const { data: stats, isFetching: statsFetching } = useQuery<AttendanceStats>({
    queryKey: ["stats", classId],
    queryFn: () => attendanceApi.stats(classId).then((r) => r.data),
    enabled: !!classId,
    refetchInterval: 30_000,
  });

  const { data: todayAttendance = [] } = useQuery({
    queryKey: ["attendance-today", classId],
    queryFn: () => attendanceApi.today(classId).then((r) => r.data),
    enabled: !!classId,
    refetchInterval: 30_000,
  });

  const { data: weeklyReport } = useQuery({
    queryKey: ["weekly-report", classId],
    queryFn: () => reportsApi.weekly(classId).then((r) => r.data),
    enabled: !!classId,
  });

  const { data: todayWird } = useQuery<DailyWird | null>({
    queryKey: ["today-wird", classId],
    queryFn: () => wirdApi.today(classId).then((r) => r.data),
    enabled: !!classId,
  });

  const sendNow = useMutation({
    mutationFn: (wirdId: string) => wirdApi.sendNow(wirdId),
    onSuccess: () => {
      toast.success("تم إرسال الورد للمجموعة ✅");
      qc.invalidateQueries({ queryKey: ["today-wird", classId] });
    },
    onError: () => toast.error("فشل الإرسال — تحقق من Bot Token"),
  });

  const className = classes.find((c) => c.id === classId)?.name;

  return (
    <div className="space-y-5">

      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold text-slate-800">لوحة التحكم</h1>
          <p className="text-slate-400 text-xs mt-0.5">
            {new Date().toLocaleDateString("ar-SA", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {statsFetching && <RefreshCw className="w-4 h-4 text-slate-300 animate-spin" />}
          {classes.length > 1 && (
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="input py-1.5 text-xs max-w-[130px]"
            >
              {classes.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* ── Today's Wird card ── */}
      {todayWird ? (
        <div className="rounded-2xl bg-gradient-to-l from-emerald-600 to-emerald-700 p-4 text-white shadow-md shadow-emerald-100">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-emerald-200 text-xs font-medium mb-1">📖 ورد اليوم</p>
              <p className="font-bold text-base leading-snug truncate">{todayWird.title}</p>
              <p className="text-emerald-200 text-xs mt-1">
                الحالة: {todayWird.status === "sent" ? "✅ تم الإرسال" : "⏳ لم يُرسَل بعد"}
                {todayWird.sent_at && ` · ${formatTime(todayWird.sent_at)}`}
              </p>
            </div>
            {todayWird.status !== "sent" && (
              <button
                onClick={() => sendNow.mutate(todayWird.id)}
                disabled={sendNow.isPending}
                className="bg-white/20 hover:bg-white/30 text-white text-xs font-semibold
                           px-3 py-2 rounded-xl flex items-center gap-1.5 transition-colors shrink-0"
              >
                <Send className="w-3.5 h-3.5" />
                {sendNow.isPending ? "جارٍ..." : "إرسال الآن"}
              </button>
            )}
          </div>
        </div>
      ) : classId ? (
        <div className="rounded-2xl border-2 border-dashed border-slate-200 p-4 text-center">
          <BookOpen className="w-7 h-7 text-slate-200 mx-auto mb-2" />
          <p className="text-slate-400 text-sm font-medium">لم يُضَف ورد اليوم بعد</p>
          <p className="text-slate-300 text-xs mt-0.5">أضيفيه من الإعدادات أو أرسلي <code className="bg-slate-100 px-1 rounded">/wird النص</code> في المجموعة</p>
        </div>
      ) : null}

      {/* ── Stats grid — 2×2 on mobile, 4×1 on desktop ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatsCard title="إجمالي الطلاب"  value={stats?.total_students ?? "—"} icon={Users}       color="blue"   />
        <StatsCard title="أكملوا اليوم"   value={stats?.today_completed ?? "—"} icon={CheckCircle} color="green"  />
        <StatsCard title="لم يكملوا"       value={stats?.today_pending ?? "—"}   icon={XCircle}     color="red"    />
        <StatsCard title="نسبة الإنجاز"   value={stats ? `${stats.completion_rate}%` : "—"} icon={TrendingUp} color="orange" />
      </div>

      {/* ── Weekly chart ── */}
      {weeklyReport?.daily?.length > 0 && (
        <CompletionChart data={weeklyReport.daily} title="إنجاز الأسبوع الحالي" height={180} />
      )}

      {/* ── Attendance ── */}
      {classId ? (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="section-title mb-0">حضور اليوم</h2>
            {className && <span className="badge-gray">{className}</span>}
          </div>
          <AttendanceTable records={todayAttendance} classId={classId} />
        </div>
      ) : (
        <div className="card text-center py-16">
          <p className="text-slate-300 text-5xl mb-3">📚</p>
          <p className="text-slate-400 font-medium">لا توجد مجموعات بعد</p>
          <p className="text-slate-300 text-xs mt-1">أضيفي مجموعة من صفحة الإعدادات</p>
        </div>
      )}
    </div>
  );
}
