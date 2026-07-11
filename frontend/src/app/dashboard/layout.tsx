import Sidebar from "@/components/dashboard/Sidebar";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession(authOptions);
  if (!session) redirect("/auth/login");

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar (desktop) + Top bar + Bottom nav (mobile) */}
      <Sidebar />

      {/* Main content */}
      <main className="flex-1 min-w-0
                       pt-14 md:pt-0          /* offset for mobile top bar */
                       pb-20 md:pb-0          /* offset for mobile bottom nav */
                       px-4 md:px-8
                       py-4 md:py-8
                       overflow-auto">
        <div className="max-w-6xl mx-auto page-enter">
          {children}
        </div>
      </main>
    </div>
  );
}
