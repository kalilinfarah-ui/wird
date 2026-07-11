"use client";
import { useQuery } from "@tanstack/react-query";
import { classesApi, reportsApi } from "@/lib/api";
import { ClassGroup, Report } from "@/types";
import { useState } from "react";
import CompletionChart from "@/components/charts/CompletionChart";
import { Download, BarChart3, TrendingUp, Users, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";

type Period = "weekly" | "monthly";

export default function ReportsPage() {
  const { data: classes = [] } = useQuery<ClassGroup[]>({
    queryKey: ["classes"],
    queryFn: () => classesApi.list().then((r) => r.data),
  });

  const [selectedClass, setSelectedClass] = useState("");
  const [period, setPeriod] = useState<Period>("weekly");
  const classId = selectedClass || classes[0]?.id || "";

  const { data: report, isLoading } = useQuery<Report>({
    queryKey: ["report", classId, period],
    queryFn: () =>
      (period === "weekly" ? reportsApi.weekly(classId) : reportsApi.monthly(classId))
        .then((r) => r.data),
    enabled: !!classId,
  });

  const { data: topStudents = [] } = useQuery<any[]>({
    queryKey: ["top-students", classId],
    queryFn: () => reportsApi.topStudents(classId, 5).then((r) => r.data),
    enabled: !!classId,
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl md:text-2xl font-extrabold text-slate-800">التقارير</h1>

        <div className="flex flex-wrap gap-2 items-center">
          {classes.length > 1 && (
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="input py-2 text-xs"
            >
              {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          )}

          {/* Period toggle */}
          <div className="flex bg-slate-100 rounded-xl p-1 gap-1">
            {(["weekly","monthly"] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all",
                  period === p ? "bg-white shadow-sm text-emerald-700" : "text-slate-400"
                )}
              >
                {p === "weekly" ? "أسبوعي" : "شهري"}
              </button>
            ))}
          </div>

          {classId && (
            <a
              href={reportsApi.exportCsv(classId)}
              download
              className="btn-secondary py-2 text-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">تصدير CSV</span>
            </a>
          )}
        </div>
      </div>

      {/* Loading skeleton */}
      {isLoading && (
        <div className="space-y-3">
          <div className="grid grid-cols-3 gap-3">
            {[...Array(3)].map((_, i) => <div key={i} className="card h-20 animate-pulse bg-slate-100" />)}
          </div>
          <div className="card h-48 animate-pulse bg-slate-100" />
        </div>
      )}

      {report && !isLoading && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-3">
            <SummaryCard icon={Users}       label="الطلاب"      value={report.total_students} color="blue" />
            <SummaryCard icon={Calendar}    label="الأيام"      value={report.total_days}     color="slate" />
            <SummaryCard icon={TrendingUp}  label="متوسط"       value={`${report.average_completion_rate}%`} color="emerald" />
          </div>

          {/* Chart */}
          <CompletionChart data={report.daily} title={`نسبة الإنجاز — ${period === 'weekly' ? 'هذا الأسبوع' : 'هذا الشهر'}`} height={180} />

          {/* Daily breakdown — scrollable table */}
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100">
              <h3 className="font-semibold text-slate-700 text-sm">التفاصيل اليومية</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs min-w-[360px]">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="text-right py-2.5 px-4 text-slate-400 font-semibold">اليوم</th>
                    <th className="text-right py-2.5 px-4 text-slate-400 font-semibold">الورد</th>
                    <th className="text-right py-2.5 px-4 text-slate-400 font-semibold">مكتمل</th>
                    <th className="text-right py-2.5 px-4 text-slate-400 font-semibold">النسبة</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {report.daily.map((d) => (
                    <tr key={d.date} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2.5 px-4 text-slate-500 whitespace-nowrap">
                        {new Date(d.date).toLocaleDateString("ar-SA", { weekday: "short", month: "short", day: "numeric" })}
                      </td>
                      <td className="py-2.5 px-4 text-slate-700 max-w-[120px] truncate">{d.title}</td>
                      <td className="py-2.5 px-4 text-slate-600">{d.completed}/{d.total}</td>
                      <td className="py-2.5 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-12 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={cn("h-full rounded-full",
                                d.rate >= 80 ? "bg-emerald-500" :
                                d.rate >= 50 ? "bg-amber-400" : "bg-red-400"
                              )}
                              style={{ width: `${d.rate}%` }}
                            />
                          </div>
                          <span className={cn("font-bold",
                            d.rate >= 80 ? "text-emerald-600" :
                            d.rate >= 50 ? "text-amber-600" : "text-red-500"
                          )}>
                            {d.rate}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Empty */}
      {!report && !isLoading && (
        <div className="card text-center py-16">
          <BarChart3 className="w-12 h-12 text-slate-200 mx-auto mb-3" />
          <p className="text-slate-400 font-medium">لا توجد بيانات بعد</p>
          <p className="text-slate-300 text-xs mt-1">ستظهر البيانات بعد بدء إرسال الورد</p>
        </div>
      )}

      {/* Top students */}
      {topStudents.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-slate-700 text-sm mb-4">🏆 أفضل الطلاب</h3>
          <div className="space-y-2.5">
            {topStudents.map((s, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="w-5 text-center text-xs font-bold text-slate-300">{i + 1}</span>
                <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center
                                text-emerald-700 font-bold text-xs shrink-0">
                  {["🥇","🥈","🥉"][i] ?? s.full_name?.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-800 truncate">{s.full_name}</p>
                </div>
                <span className="badge-green text-xs">{s.completion_percentage}%</span>
                <span className="text-orange-500 text-xs font-bold">🔥{s.current_streak}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, color }: {
  icon: any; label: string; value: string | number; color: string;
}) {
  const colors: Record<string, string> = {
    blue:    "text-blue-600 bg-blue-50",
    slate:   "text-slate-600 bg-slate-100",
    emerald: "text-emerald-600 bg-emerald-50",
  };
  return (
    <div className="card text-center p-3">
      <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center mx-auto mb-1.5", colors[color])}>
        <Icon className="w-4 h-4" />
      </div>
      <p className="text-xl font-extrabold text-slate-800">{value}</p>
      <p className="text-[11px] text-slate-400 mt-0.5">{label}</p>
    </div>
  );
}
