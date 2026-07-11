"use client";
import { useQuery } from "@tanstack/react-query";
import { classesApi } from "@/lib/api";
import { Student, ClassGroup } from "@/types";
import { useState } from "react";
import { Users, Flame, Award, TrendingUp, Search } from "lucide-react";
import { cn } from "@/lib/utils";

export default function StudentsPage() {
  const { data: classes = [] } = useQuery<ClassGroup[]>({
    queryKey: ["classes"],
    queryFn: () => classesApi.list().then((r) => r.data),
  });

  const [selectedClass, setSelectedClass] = useState("");
  const classId = selectedClass || classes[0]?.id || "";

  const { data: students = [], isLoading } = useQuery<Student[]>({
    queryKey: ["students", classId],
    queryFn: () => classesApi.students(classId).then((r) => r.data),
    enabled: !!classId,
  });

  const [search, setSearch]   = useState("");
  const [sort, setSort]       = useState<"name" | "streak" | "rate">("rate");

  const filtered = students
    .filter((s) =>
      s.full_name.includes(search) ||
      (s.telegram_username || "").toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => {
      if (sort === "streak") return b.current_streak - a.current_streak;
      if (sort === "rate")   return b.completion_percentage - a.completion_percentage;
      return a.full_name.localeCompare(b.full_name, "ar");
    });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl md:text-2xl font-extrabold text-slate-800">الطلاب</h1>
        {students.length > 0 && (
          <span className="badge-blue">{students.length} طالب</span>
        )}
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="بحث..."
            className="input pr-9"
          />
        </div>
        <div className="flex gap-1.5">
          {classes.length > 1 && (
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="input py-2 text-xs"
            >
              {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          )}
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as any)}
            className="input py-2 text-xs"
          >
            <option value="rate">الأعلى نسبة</option>
            <option value="streak">الأعلى سلسلة</option>
            <option value="name">أبجدي</option>
          </select>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse h-32 bg-slate-100" />
          ))}
        </div>
      )}

      {/* Grid */}
      {!isLoading && filtered.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((s, i) => <StudentCard key={s.id} student={s} rank={i + 1} />)}
        </div>
      )}

      {/* Empty */}
      {!isLoading && filtered.length === 0 && (
        <div className="card text-center py-16">
          <p className="text-5xl mb-3">👥</p>
          <p className="text-slate-400 font-medium">لا يوجد طلاب</p>
          <p className="text-slate-300 text-xs mt-1">سيُضافون تلقائياً عند تفاعلهم في المجموعة</p>
        </div>
      )}
    </div>
  );
}

function StudentCard({ student: s, rank }: { student: Student; rank: number }) {
  const rate  = s.completion_percentage;
  const isTop = rank <= 3;

  const rateColor =
    rate >= 80 ? "bg-emerald-500" :
    rate >= 50 ? "bg-amber-400"   : "bg-red-400";

  const rateText =
    rate >= 80 ? "text-emerald-600" :
    rate >= 50 ? "text-amber-600"   : "text-red-500";

  const medals: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

  return (
    <div className={cn(
      "card hover:shadow-md transition-all duration-200",
      isTop && "border-amber-100 bg-gradient-to-br from-white to-amber-50/30"
    )}>
      {/* Top row */}
      <div className="flex items-center gap-3 mb-3">
        <div className={cn(
          "w-10 h-10 rounded-full flex items-center justify-center text-base font-extrabold shrink-0",
          rate >= 80 ? "bg-emerald-100 text-emerald-700"
          : rate >= 50 ? "bg-amber-100 text-amber-700"
          : "bg-red-50 text-red-500"
        )}>
          {medals[rank] ?? s.full_name.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-bold text-slate-800 text-sm truncate">{s.full_name}</p>
          {s.telegram_username && (
            <p className="text-xs text-slate-400 truncate">@{s.telegram_username}</p>
          )}
        </div>
        <span className={cn("text-sm font-extrabold shrink-0", rateText)}>{rate}%</span>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden mb-3">
        <div className={cn("h-full rounded-full transition-all", rateColor)} style={{ width: `${rate}%` }} />
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-0 divide-x divide-x-reverse divide-slate-100 text-center">
        <div className="px-2">
          <p className="text-[10px] text-slate-400 flex items-center justify-center gap-0.5 mb-0.5">
            <Flame className="w-2.5 h-2.5 text-orange-400" /> سلسلة
          </p>
          <p className="font-extrabold text-orange-500 text-sm">{s.current_streak}</p>
        </div>
        <div className="px-2">
          <p className="text-[10px] text-slate-400 flex items-center justify-center gap-0.5 mb-0.5">
            <Award className="w-2.5 h-2.5 text-blue-400" /> أطول
          </p>
          <p className="font-extrabold text-blue-500 text-sm">{s.longest_streak}</p>
        </div>
        <div className="px-2">
          <p className="text-[10px] text-slate-400 flex items-center justify-center gap-0.5 mb-0.5">
            <TrendingUp className="w-2.5 h-2.5 text-slate-400" /> مكتمل
          </p>
          <p className="font-extrabold text-slate-600 text-sm">{s.total_completed}</p>
        </div>
      </div>
    </div>
  );
}
