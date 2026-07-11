"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Users, BookMarked,
  BarChart3, Settings, LogOut, BookOpen,
} from "lucide-react";
import { signOut } from "next-auth/react";

const navItems = [
  { href: "/dashboard",            icon: LayoutDashboard, label: "الرئيسية",  shortLabel: "الرئيسية" },
  { href: "/dashboard/attendance", icon: BookMarked,       label: "الحضور",    shortLabel: "الحضور"  },
  { href: "/dashboard/students",   icon: Users,            label: "الطلاب",    shortLabel: "الطلاب"  },
  { href: "/dashboard/reports",    icon: BarChart3,        label: "التقارير",  shortLabel: "تقارير"  },
  { href: "/dashboard/settings",   icon: Settings,         label: "الإعدادات", shortLabel: "إعدادات" },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) =>
    href === "/dashboard"
      ? pathname === "/dashboard"
      : pathname.startsWith(href);

  return (
    <>
      {/* ── Desktop sidebar (hidden on mobile) ── */}
      <aside className="hidden md:flex w-60 min-h-screen bg-white border-l border-slate-100 flex-col shrink-0">
        {/* Logo */}
        <div className="p-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-emerald-600 rounded-xl flex items-center justify-center shadow-sm">
              <BookOpen className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-emerald-700 leading-none">ورد</h1>
              <p className="text-[10px] text-slate-400 mt-0.5">إدارة الورد اليومي</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5">
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
                  active
                    ? "bg-emerald-50 text-emerald-700"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
                )}
              >
                <item.icon className={cn("w-4 h-4 shrink-0", active ? "text-emerald-600" : "text-slate-400")} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Sign out */}
        <div className="p-3 border-t border-slate-100">
          <button
            onClick={() => signOut({ callbackUrl: "/auth/login" })}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-slate-400
                       hover:bg-red-50 hover:text-red-500 w-full transition-all"
          >
            <LogOut className="w-4 h-4" />
            خروج
          </button>
        </div>
      </aside>

      {/* ── Mobile top bar ── */}
      <header className="md:hidden fixed top-0 inset-x-0 z-40 bg-white border-b border-slate-100
                         flex items-center justify-between px-4 h-14 safe-top">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-emerald-600 rounded-lg flex items-center justify-center">
            <BookOpen className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-bold text-emerald-700 text-base">ورد</span>
        </div>
        <button
          onClick={() => signOut({ callbackUrl: "/auth/login" })}
          className="p-2 rounded-lg text-slate-400 hover:bg-red-50 hover:text-red-500 transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </header>

      {/* ── Mobile bottom navigation ── */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-slate-100
                      flex items-center safe-bottom">
        {navItems.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex-1 flex flex-col items-center gap-0.5 py-2 transition-colors min-h-[56px] justify-center",
                active ? "text-emerald-600" : "text-slate-400"
              )}
            >
              <item.icon className={cn("w-5 h-5", active && "text-emerald-600")} />
              <span className="text-[10px] font-medium">{item.shortLabel}</span>
              {active && (
                <span className="absolute bottom-0 w-8 h-0.5 bg-emerald-600 rounded-t-full" />
              )}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
