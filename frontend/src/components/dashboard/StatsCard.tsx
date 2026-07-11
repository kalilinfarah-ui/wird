import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color: "green" | "blue" | "orange" | "red";
  trend?: { value: number; label: string };
}

const palette = {
  green:  { wrap: "bg-emerald-50 border-emerald-100", icon: "bg-emerald-100 text-emerald-600", val: "text-emerald-700" },
  blue:   { wrap: "bg-blue-50   border-blue-100",   icon: "bg-blue-100   text-blue-600",   val: "text-blue-700"   },
  orange: { wrap: "bg-orange-50 border-orange-100", icon: "bg-orange-100 text-orange-600", val: "text-orange-700" },
  red:    { wrap: "bg-red-50    border-red-100",    icon: "bg-red-100    text-red-500",    val: "text-red-600"    },
};

export default function StatsCard({ title, value, subtitle, icon: Icon, color, trend }: Props) {
  const p = palette[color];
  return (
    <div className={cn("rounded-2xl border p-4 flex items-center gap-4", p.wrap)}>
      <div className={cn("w-11 h-11 rounded-xl flex items-center justify-center shrink-0", p.icon)}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-slate-500 font-medium truncate">{title}</p>
        <p className={cn("text-2xl font-extrabold leading-tight", p.val)}>{value}</p>
        {subtitle && <p className="text-[11px] text-slate-400 mt-0.5 truncate">{subtitle}</p>}
        {trend && (
          <p className={cn("text-[11px] mt-0.5 font-medium", trend.value >= 0 ? "text-emerald-600" : "text-red-500")}>
            {trend.value >= 0 ? "↑" : "↓"} {Math.abs(trend.value)}% {trend.label}
          </p>
        )}
      </div>
    </div>
  );
}
