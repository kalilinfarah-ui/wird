"use client";
import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { BookOpen, Eye, EyeOff, Loader2 } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [loading,  setLoading]  = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const res = await signIn("credentials", { email, password, redirect: false });
    setLoading(false);
    if (res?.ok) router.push("/dashboard");
    else toast.error("البريد الإلكتروني أو كلمة المرور غير صحيحة");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-slate-100
                    flex flex-col items-center justify-center p-4 safe-top safe-bottom">

      {/* Card */}
      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-emerald-600 rounded-2xl flex items-center justify-center
                          mx-auto mb-4 shadow-lg shadow-emerald-200">
            <BookOpen className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-emerald-700">ورد</h1>
          <p className="text-slate-400 text-sm mt-1">منصة إدارة الورد اليومي</p>
        </div>

        {/* Form card */}
        <div className="bg-white rounded-2xl shadow-xl shadow-slate-100 border border-slate-100 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-5">تسجيل الدخول</h2>

          <form onSubmit={handleLogin} className="space-y-4">
            {/* Email */}
            <div>
              <label className="input-label">البريد الإلكتروني</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="teacher@example.com"
                autoComplete="email"
                className="input"
              />
            </div>

            {/* Password */}
            <div>
              <label className="input-label">كلمة المرور</label>
              <div className="relative">
                <input
                  type={showPass ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="input pl-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-300
                             hover:text-slate-500 transition-colors p-1"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 text-base mt-2"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "دخول"}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-100" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white px-3 text-xs text-slate-400">أو سجّل دخول بـ</span>
            </div>
          </div>

          {/* Telegram login widget */}
          <div className="flex justify-center min-h-[44px] items-center">
            <script
              async
              src="https://telegram.org/js/telegram-widget.js?22"
              // @ts-ignore
              data-telegram-login={process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME ?? "your_bot"}
              data-size="large"
              data-auth-url={`${process.env.NEXTAUTH_URL}/api/auth/callback/telegram`}
              data-request-access="write"
            />
          </div>

          {/* Register link */}
          <p className="text-center text-xs text-slate-400 mt-5">
            ليس لديك حساب؟{" "}
            <Link href="/auth/register" className="text-emerald-600 font-semibold hover:underline">
              إنشاء حساب مجاني
            </Link>
          </p>
        </div>

        {/* Footer note */}
        <p className="text-center text-[11px] text-slate-300 mt-6">
          منصة ورد © {new Date().getFullYear()} — لإدارة الورد اليومي عبر تيليغرام
        </p>
      </div>
    </div>
  );
}
