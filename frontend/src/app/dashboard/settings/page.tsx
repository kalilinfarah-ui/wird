"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { classesApi } from "@/lib/api";
import { ClassGroup } from "@/types";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Settings, Plus, Link2, Bell, ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

const schema = z.object({
  name:              z.string().min(2, "اسم قصير جداً"),
  description:       z.string().optional(),
  bot_token:         z.string().optional(),
  telegram_chat_id:  z.number().optional(),
  wird_time:         z.string().regex(/^\d{2}:\d{2}$/, "صيغة HH:MM"),
  timezone:          z.string(),
  reminders_enabled: z.boolean(),
  reminder_1_hours:  z.string(),
  reminder_2_hours:  z.string(),
  reminder_3_time:   z.string().regex(/^\d{2}:\d{2}$/, "صيغة HH:MM"),
});
type FormData = z.infer<typeof schema>;

export default function SettingsPage() {
  const qc = useQueryClient();
  const [showNew, setShowNew] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data: classes = [] } = useQuery<ClassGroup[]>({
    queryKey: ["classes"],
    queryFn: () => classesApi.list().then((r) => r.data),
  });

  const createClass = useMutation({
    mutationFn: (d: FormData) => classesApi.create(d),
    onSuccess: () => { toast.success("تم إنشاء المجموعة ✅"); qc.invalidateQueries({ queryKey: ["classes"] }); setShowNew(false); },
    onError: () => toast.error("حدث خطأ"),
  });

  const updateClass = useMutation({
    mutationFn: ({ id, data }: { id: string; data: FormData }) => classesApi.update(id, data),
    onSuccess: () => { toast.success("تم الحفظ ✅"); qc.invalidateQueries({ queryKey: ["classes"] }); setExpandedId(null); },
    onError: () => toast.error("حدث خطأ"),
  });

  const setWebhook = useMutation({
    mutationFn: (id: string) => classesApi.setWebhook(id),
    onSuccess: () => toast.success("تم ربط Webhook ✅"),
    onError:   () => toast.error("فشل ربط Webhook — تحقق من Bot Token"),
  });

  return (
    <div className="space-y-4 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl md:text-2xl font-extrabold text-slate-800">الإعدادات</h1>
        <button onClick={() => { setShowNew(true); setExpandedId(null); }} className="btn-primary text-sm">
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">مجموعة جديدة</span>
          <span className="sm:hidden">إضافة</span>
        </button>
      </div>

      {/* How it works — quick guide */}
      <div className="card bg-blue-50 border-blue-100 p-4">
        <p className="font-semibold text-blue-800 text-sm mb-2">🚀 كيفية البدء</p>
        <ol className="text-xs text-blue-700 space-y-1 list-decimal list-inside">
          <li>أنشئ بوت من @BotFather واحصل على <strong>Bot Token</strong></li>
          <li>أضف البوت لمجموعتك وأعطه صلاحية <strong>Administrator</strong></li>
          <li>أرسل <code className="bg-blue-100 px-1 rounded">/id</code> في المجموعة لمعرفة الـ <strong>Chat ID</strong></li>
          <li>أنشئ مجموعة هنا وأدخل البيانات ثم اضغط <strong>ربط Webhook</strong></li>
        </ol>
      </div>

      {/* New class form */}
      {showNew && (
        <div className="card border-emerald-100 bg-emerald-50/30">
          <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
            <Plus className="w-4 h-4 text-emerald-600" /> مجموعة جديدة
          </h3>
          <ClassForm
            onSubmit={(d) => createClass.mutate(d)}
            onCancel={() => setShowNew(false)}
            loading={createClass.isPending}
          />
        </div>
      )}

      {/* Existing classes */}
      {classes.map((c) => {
        const isOpen = expandedId === c.id;
        return (
          <div key={c.id} className="card">
            {/* Collapsed header */}
            <div
              className="flex items-center gap-3 cursor-pointer"
              onClick={() => setExpandedId(isOpen ? null : c.id)}
            >
              <div className="w-9 h-9 rounded-xl bg-emerald-100 flex items-center justify-center shrink-0">
                <Bell className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-bold text-slate-800 text-sm truncate">{c.name}</p>
                <p className="text-xs text-slate-400 mt-0.5">
                  ⏰ {c.wird_time} · 🌍 {TIMEZONES.find(([tz]) => tz === c.timezone)?.[1] ?? c.timezone} · {c.reminders_enabled ? "🔔 تذكيرات" : "🔕 بدون تذكيرات"}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {c.telegram_chat_id
                  ? <span className="badge-green hidden sm:flex">مرتبط</span>
                  : <span className="badge-red  hidden sm:flex">غير مرتبط</span>
                }
                {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </div>
            </div>

            {/* Expanded */}
            {isOpen && (
              <div className="mt-4 pt-4 border-t border-slate-100 space-y-4">
                {/* Quick actions */}
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => setWebhook.mutate(c.id)}
                    disabled={setWebhook.isPending || !c.bot_token}
                    className="btn-primary text-xs py-2"
                  >
                    <Link2 className="w-3.5 h-3.5" />
                    ربط Webhook
                  </button>
                  <button
                    onClick={() => { /* copy chat id */ navigator.clipboard.writeText(String(c.telegram_chat_id || "")); toast.success("تم نسخ Chat ID"); }}
                    className="btn-secondary text-xs py-2"
                    disabled={!c.telegram_chat_id}
                  >
                    نسخ Chat ID
                  </button>
                </div>

                {/* Info grid */}
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
                  <InfoRow label="Chat ID"          value={c.telegram_chat_id ? String(c.telegram_chat_id) : "غير محدد"} />
                  <InfoRow label="وقت الورد"        value={c.wird_time} />
                  <InfoRow label="المنطقة الزمنية"  value={c.timezone} />
                  <InfoRow label="تذكير 3"           value={c.reminder_3_time} />
                </div>

                {/* Edit form */}
                <details className="group">
                  <summary className="cursor-pointer text-xs text-emerald-600 font-semibold flex items-center gap-1 select-none">
                    <Settings className="w-3.5 h-3.5" />
                    تعديل الإعدادات
                  </summary>
                  <div className="mt-3">
                    <ClassForm
                      defaultValues={c}
                      onSubmit={(d) => updateClass.mutate({ id: c.id, data: d })}
                      onCancel={() => setExpandedId(null)}
                      loading={updateClass.isPending}
                    />
                  </div>
                </details>
              </div>
            )}
          </div>
        );
      })}

      {classes.length === 0 && !showNew && (
        <div className="card text-center py-16">
          <Settings className="w-12 h-12 text-slate-200 mx-auto mb-3" />
          <p className="text-slate-400 font-medium">لا توجد مجموعات</p>
          <p className="text-slate-300 text-xs mt-1">ابدأي بإضافة مجموعتك الأولى</p>
        </div>
      )}
    </div>
  );
}

/* ── Small helpers ── */
function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-50 rounded-lg px-3 py-2">
      <p className="text-slate-400 text-[10px]">{label}</p>
      <p className="font-semibold text-slate-700 truncate">{value}</p>
    </div>
  );
}

/* ── Class form ── */
const TIMEZONES: [string, string][] = [
  ["Africa/Algiers",    "الجزائر، تونس (UTC+1)"],
  ["Asia/Riyadh",       "السعودية، الكويت، قطر (UTC+3)"],
  ["Africa/Cairo",      "مصر (UTC+2)"],
  ["Asia/Dubai",        "الإمارات (UTC+4)"],
  ["Africa/Casablanca", "المغرب (UTC+1)"],
  ["Asia/Amman",        "الأردن (UTC+3)"],
  ["Asia/Beirut",       "لبنان (UTC+3)"],
  ["Asia/Baghdad",      "العراق (UTC+3)"],
  ["Africa/Tripoli",    "ليبيا (UTC+2)"],
  ["Asia/Aden",         "اليمن (UTC+3)"],
  ["Asia/Muscat",       "عُمان (UTC+4)"],
  ["Europe/London",     "المملكة المتحدة (UTC+0/1)"],
  ["Europe/Paris",      "أوروبا الوسطى (UTC+1/2)"],
  ["UTC",               "UTC (توقيت عالمي)"],
];

function ClassForm({ defaultValues, onSubmit, onCancel, loading }: {
  defaultValues?: Partial<ClassGroup>;
  onSubmit: (d: FormData) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name:              defaultValues?.name             || "",
      description:       defaultValues?.description      || "",
      bot_token:         "",
      telegram_chat_id:  defaultValues?.telegram_chat_id || undefined,
      wird_time:         defaultValues?.wird_time        || "07:00",
      timezone:          defaultValues?.timezone         || "Asia/Riyadh",
      reminders_enabled: defaultValues?.reminders_enabled ?? true,
      reminder_1_hours:  defaultValues?.reminder_1_hours || "2",
      reminder_2_hours:  defaultValues?.reminder_2_hours || "6",
      reminder_3_time:   defaultValues?.reminder_3_time  || "21:00",
    },
  });

  const Field = ({ label, name, type = "text", placeholder, hint }: {
    label: string; name: keyof FormData; type?: string; placeholder?: string; hint?: string;
  }) => (
    <div>
      <label className="input-label">{label}</label>
      <input
        type={type}
        placeholder={placeholder}
        {...register(name, type === "number" ? { valueAsNumber: true } : {})}
        className={cn("input", errors[name] && "border-red-300 focus:ring-red-400")}
      />
      {hint    && <p className="text-[11px] text-slate-400 mt-0.5">{hint}</p>}
      {errors[name] && <p className="text-red-500 text-xs mt-0.5">{(errors[name] as any)?.message}</p>}
    </div>
  );

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Field label="اسم المجموعة *"              name="name"             placeholder="حلقة القرآن" />
        <Field label="Bot Token *"                 name="bot_token"        placeholder="123456789:ABC..." hint="من @BotFather" />
        <Field label="Chat ID"                     name="telegram_chat_id" type="number" placeholder="-100123456789" hint="أرسل /id في المجموعة" />
        <Field label="وقت إرسال الورد"             name="wird_time"        placeholder="07:00" />

        <div>
          <label className="input-label">المنطقة الزمنية</label>
          <select {...register("timezone")} className="input">
            {TIMEZONES.map(([tz, label]) => <option key={tz} value={tz}>{label}</option>)}
          </select>
        </div>

        <div className="flex items-center gap-3 pt-5">
          <input type="checkbox" id="rem" {...register("reminders_enabled")} className="w-4 h-4 accent-emerald-600 rounded" />
          <label htmlFor="rem" className="text-sm text-slate-600 select-none cursor-pointer">تفعيل التذكيرات التلقائية</label>
        </div>

        <Field label="تذكير 1 — بعد (ساعات)"  name="reminder_1_hours" placeholder="2" />
        <Field label="تذكير 2 — بعد (ساعات)"  name="reminder_2_hours" placeholder="6" />
        <Field label="تذكير 3 — وقت ثابت"     name="reminder_3_time"  placeholder="21:00" />
      </div>

      <div className="flex gap-2 pt-1">
        <button type="submit" disabled={loading} className="btn-primary flex-1 sm:flex-none">
          {loading ? "جارٍ الحفظ..." : "حفظ"}
        </button>
        <button type="button" onClick={onCancel} className="btn-secondary flex-1 sm:flex-none">
          إلغاء
        </button>
      </div>
    </form>
  );
}
