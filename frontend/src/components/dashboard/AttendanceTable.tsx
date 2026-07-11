"use client";
import { useState } from "react";
import { AttendanceRecord } from "@/types";
import { formatTime, cn } from "@/lib/utils";
import { CheckCircle, XCircle, Clock, Search, UserCheck, ChevronDown } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { attendanceApi } from "@/lib/api";
import { toast } from "sonner";

interface Props {
  records: AttendanceRecord[];
  classId: string;
}

const methodLabel: Record<string, string> = {
  button:   "زر ✅",
  keyword:  "كلمة",
  reaction: "تفاعل",
  manual:   "يدوي",
};

type Filter = "all" | "completed" | "pending";

export default function AttendanceTable({ records, classId }: Props) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const queryClient = useQueryClient();

  const markComplete = useMutation({
    mutationFn: (studentId: string) => attendanceApi.manualComplete(classId, studentId),
    onSuccess: () => {
      toast.success("✅ تم تسجيل الحضور");
      queryClient.invalidateQueries({ queryKey: ["attendance-today", classId] });
    },
    onError: () => toast.error("حدث خطأ، حاول مجدداً"),
  });

  const filtered = records.filter((r) => {
    const matchSearch =
      r.full_name.includes(search) ||
      (r.telegram_username || "").toLowerCase().includes(search.toLowerCase());
    const matchFilter =
      filter === "all" ||
      (filter === "completed" && r.completed) ||
      (filter === "pending" && !r.completed);
    return matchSearch && matchFilter;
  });

  const completedCount = records.filter((r) => r.completed).length;
  const pendingCount   = records.filter((r) => !r.completed).length;

  return (
    <div className="space-y-3">
      {/* ── Filter bar ── */}
      <div className="flex flex-col sm:flex-row gap-2">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="بحث عن طالب..."
            className="input pr-9"
          />
        </div>

        {/* Filter chips */}
        <div className="flex gap-1.5 shrink-0">
          {([
            { key: "all",       label: `الكل (${records.length})` },
            { key: "completed", label: `مكتمل (${completedCount})` },
            { key: "pending",   label: `معلق (${pendingCount})` },
          ] as { key: Filter; label: string }[]).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={cn(
                "px-3 py-2 rounded-xl text-xs font-semibold transition-colors whitespace-nowrap",
                filter === key
                  ? key === "completed" ? "bg-emerald-600 text-white"
                  : key === "pending"   ? "bg-red-500 text-white"
                  : "bg-slate-800 text-white"
                  : "bg-slate-100 text-slate-500 hover:bg-slate-200"
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Mobile card list (visible on small screens) ── */}
      <div className="block md:hidden space-y-2">
        {filtered.length === 0 && <EmptyState />}
        {filtered.map((r) => (
          <MobileCard key={r.student_id} r={r} onMark={() => markComplete.mutate(r.student_id)} />
        ))}
      </div>

      {/* ── Desktop table (hidden on small screens) ── */}
      <div className="hidden md:block card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100">
              {["الطالب","الحالة","وقت الإكمال","الطريقة","🔥 سلسلة","النسبة",""].map((h) => (
                <th key={h} className="text-right py-3 px-4 font-semibold text-slate-400 text-xs uppercase tracking-wide">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {filtered.map((r) => (
              <DesktopRow key={r.student_id} r={r} onMark={() => markComplete.mutate(r.student_id)} />
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <EmptyState />}
      </div>
    </div>
  );
}

/* ── Mobile card ── */
function MobileCard({ r, onMark }: { r: AttendanceRecord; onMark: () => void }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div
      className={cn(
        "card-sm transition-all",
        r.completed ? "border-emerald-100 bg-emerald-50/40" : "border-slate-100"
      )}
    >
      <div className="flex items-center gap-3">
        {/* Avatar initial */}
        <div className={cn(
          "w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0",
          r.completed ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
        )}>
          {r.full_name.charAt(0)}
        </div>

        {/* Name + username */}
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-slate-800 text-sm truncate">{r.full_name}</p>
          {r.telegram_username && (
            <p className="text-xs text-slate-400 truncate">@{r.telegram_username}</p>
          )}
        </div>

        {/* Status badge */}
        <div className="shrink-0 flex items-center gap-2">
          {r.completed ? (
            <span className="badge-green">✅ مكتمل</span>
          ) : (
            <span className="badge-red">⏳ معلق</span>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 rounded-lg text-slate-300 hover:text-slate-500"
          >
            <ChevronDown className={cn("w-4 h-4 transition-transform", expanded && "rotate-180")} />
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-3 gap-2 text-center text-xs">
          <div>
            <p className="text-slate-400">وقت الإكمال</p>
            <p className="font-medium text-slate-700 mt-0.5">
              {r.completed_at ? formatTime(r.completed_at) : "—"}
            </p>
          </div>
          <div>
            <p className="text-slate-400">🔥 السلسلة</p>
            <p className="font-bold text-orange-500 mt-0.5">{r.current_streak} يوم</p>
          </div>
          <div>
            <p className="text-slate-400">النسبة</p>
            <p className={cn("font-bold mt-0.5",
              r.completion_percentage >= 80 ? "text-emerald-600"
              : r.completion_percentage >= 50 ? "text-amber-600"
              : "text-red-500"
            )}>
              {r.completion_percentage}%
            </p>
          </div>
          {!r.completed && (
            <div className="col-span-3 mt-1">
              <button
                onClick={onMark}
                className="btn-primary w-full text-xs py-2"
              >
                <UserCheck className="w-3.5 h-3.5" />
                تسجيل الحضور يدوياً
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Desktop row ── */
function DesktopRow({ r, onMark }: { r: AttendanceRecord; onMark: () => void }) {
  return (
    <tr className="hover:bg-slate-50 transition-colors">
      <td className="py-3 px-4">
        <div className="flex items-center gap-2.5">
          <div className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0",
            r.completed ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-400"
          )}>
            {r.full_name.charAt(0)}
          </div>
          <div>
            <p className="font-medium text-slate-800">{r.full_name}</p>
            {r.telegram_username && (
              <p className="text-xs text-slate-400">@{r.telegram_username}</p>
            )}
          </div>
        </div>
      </td>
      <td className="py-3 px-4">
        {r.completed
          ? <span className="badge-green flex items-center gap-1 w-fit"><CheckCircle className="w-3 h-3" /> مكتمل</span>
          : <span className="badge-red flex items-center gap-1 w-fit"><XCircle className="w-3 h-3" /> معلق</span>
        }
      </td>
      <td className="py-3 px-4 text-slate-500 text-xs">
        {r.completed_at ? (
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3 text-slate-300" />
            {formatTime(r.completed_at)}
          </span>
        ) : "—"}
      </td>
      <td className="py-3 px-4">
        {r.method ? <span className="badge-gray">{methodLabel[r.method] || r.method}</span> : "—"}
      </td>
      <td className="py-3 px-4 font-bold text-orange-500">{r.current_streak}</td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={cn("h-full rounded-full",
                r.completion_percentage >= 80 ? "bg-emerald-500"
                : r.completion_percentage >= 50 ? "bg-amber-400"
                : "bg-red-400"
              )}
              style={{ width: `${r.completion_percentage}%` }}
            />
          </div>
          <span className="text-xs text-slate-500 w-8 text-left">{r.completion_percentage}%</span>
        </div>
      </td>
      <td className="py-3 px-4">
        {!r.completed && (
          <button
            onClick={onMark}
            className="flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-800
                       font-medium transition-colors px-2 py-1 rounded-lg hover:bg-emerald-50"
          >
            <UserCheck className="w-3.5 h-3.5" /> تسجيل
          </button>
        )}
      </td>
    </tr>
  );
}

function EmptyState() {
  return (
    <div className="text-center py-12">
      <p className="text-slate-300 text-4xl mb-2">🔍</p>
      <p className="text-slate-400 text-sm">لا توجد نتائج</p>
    </div>
  );
}
