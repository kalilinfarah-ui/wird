"use client";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import { ReportDay } from "@/types";

interface Props {
  data: ReportDay[];
  title?: string;
  height?: number;
}

export default function CompletionChart({ data, title = "نسبة الإنجاز", height = 200 }: Props) {
  const formatted = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString("ar-SA", { weekday: "short", day: "numeric" }),
    نسبة: d.rate,
    مكتمل: d.completed,
    الإجمالي: d.total,
  }));

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-600 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={formatted} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
          <defs>
            <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#059669" stopOpacity={0.18} />
              <stop offset="95%" stopColor="#059669" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: "#94a3b8" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            unit="%"
            tick={{ fontSize: 10, fill: "#94a3b8" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(v: number, name: string) =>
              name === "نسبة" ? [`${v}%`, "نسبة الإنجاز"] : [v, name]
            }
            contentStyle={{
              borderRadius: 12,
              border: "1px solid #f1f5f9",
              boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
              fontSize: 12,
              fontFamily: "Cairo, sans-serif",
            }}
            labelStyle={{ fontWeight: 600, color: "#334155" }}
          />
          <Area
            type="monotone"
            dataKey="نسبة"
            stroke="#059669"
            strokeWidth={2.5}
            fill="url(#grad)"
            dot={{ r: 3, fill: "#059669", strokeWidth: 0 }}
            activeDot={{ r: 5, fill: "#059669" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
