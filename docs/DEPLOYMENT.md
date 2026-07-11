# دليل النشر المجاني — ورد

## الخدمات المجانية (صفر تكلفة)

| الخدمة | الاستخدام | الحد المجاني |
|--------|-----------|-------------|
| **Supabase** | PostgreSQL | 500MB |
| **Render** | FastAPI backend | 750 ساعة/شهر |
| **Vercel** | Next.js frontend | غير محدود |
| **UptimeRobot** | إبقاء Render مستيقظاً | 50 مراقب |
| **cron-job.org** | إرسال الورد والتذكيرات | غير محدود |

> **لا يوجد Redis، لا يوجد Celery، لا يوجد APScheduler.**
> كل المهام الزمنية تُشغَّل بـ HTTP استدعاءات خارجية من cron-job.org.

---

## الخطوة 1 — Supabase

1. **https://supabase.com** → حساب جديد → مشروع جديد
2. **SQL Editor** → الصقي محتوى `docs/schema.sql` → **Run**
3. **Settings → Database** → انسخي `Connection string` → هذا `DATABASE_URL`
4. **Settings → API** → انسخي `URL` و `service_role key`

---

## الخطوة 2 — بوت تيليغرام

1. افتحي **@BotFather** → `/newbot`
2. انسخي الـ **Bot Token**
3. أضيفي البوت لمجموعتك وأعطيه صلاحية **Administrator**
4. للحصول على Chat ID:
   - أرسلي أي رسالة في المجموعة
   - افتحي: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - ابحثي عن `"chat":{"id":` — سيكون رقماً سالباً مثل `-100123456789`

---

## الخطوة 3 — Render (Backend)

1. **https://render.com** → حساب بـ GitHub
2. **New → Web Service** → ربط المستودع
3. الإعدادات:
   - Root Directory: `backend`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables**:
   ```
   DATABASE_URL        = <Supabase connection string>
   SECRET_KEY          = <نص عشوائي طويل>
   TELEGRAM_BOT_TOKEN  = <من BotFather>
   TELEGRAM_WEBHOOK_SECRET = <أي نص عشوائي>
   CRON_SECRET         = <أي نص عشوائي — ستستخدمينه في cron-job.org>
   FRONTEND_URL        = https://your-app.vercel.app
   SUPABASE_URL        = <من Supabase>
   SUPABASE_SERVICE_KEY= <من Supabase>
   ```
5. انتظري النشر → انسخي الرابط: `https://wird-api.onrender.com`

---

## الخطوة 4 — UptimeRobot (إبقاء Render مستيقظاً)

> Render المجاني ينام بعد 15 دقيقة. UptimeRobot يمنعه من النوم.

1. **https://uptimerobot.com** → حساب مجاني
2. **Add New Monitor**:
   - Type: **HTTP(s)**
   - Friendly Name: `ورد Backend`
   - URL: `https://wird-api.onrender.com/health`
   - Monitoring Interval: **5 minutes**
3. احفظي — الآن Render لن ينام أبداً ✅

---

## الخطوة 5 — cron-job.org (المهام الزمنية)

> هذا يستبدل APScheduler + Celery + Redis بالكامل.

1. **https://cron-job.org** → حساب مجاني
2. أنشئي **3 مهام** (Cronjobs):

### مهمة 1: إرسال الورد اليومي

| الحقل | القيمة |
|-------|--------|
| URL | `https://wird-api.onrender.com/api/tasks/send-wird` |
| Method | POST |
| Header | `X-Cron-Secret: <نفس CRON_SECRET في Render>` |
| Schedule | كل دقيقة: `* * * * *` |

> تُرسَل كل دقيقة، لكن الكود يتحقق إذا كانت الساعة تطابق `wird_time` للفصل.
> إذا أردتِ تحسين الأداء: شغّليها فقط بين 5:00 و 12:00: `* 5-12 * * *`

### مهمة 2: إرسال التذكيرات

| الحقل | القيمة |
|-------|--------|
| URL | `https://wird-api.onrender.com/api/tasks/send-reminders` |
| Method | POST |
| Header | `X-Cron-Secret: <CRON_SECRET>` |
| Schedule | كل 5 دقائق: `*/5 * * * *` |

### مهمة 3: ملخص المجموعة المسائي

| الحقل | القيمة |
|-------|--------|
| URL | `https://wird-api.onrender.com/api/tasks/send-summary` |
| Method | POST |
| Header | `X-Cron-Secret: <CRON_SECRET>` |
| Schedule | كل يوم الساعة 10 مساءً: `0 22 * * *` |

---

## الخطوة 6 — Vercel (Frontend) — اختياري

> لوحة التحكم اختيارية الآن — يمكن إدارة كل شيء من تيليغرام مباشرةً.

1. **https://vercel.com** → New Project → ربط المستودع
2. Root Directory: `frontend`
3. Environment Variables:
   ```
   NEXTAUTH_URL    = https://your-app.vercel.app
   NEXTAUTH_SECRET = <نص عشوائي>
   NEXT_PUBLIC_API_URL = https://wird-api.onrender.com/api
   NEXT_PUBLIC_TELEGRAM_BOT_USERNAME = your_bot_username
   ```
4. Deploy

---

## الخطوة 7 — ربط Webhook وإنشاء الفصل الأول

### من تيليغرام (الطريقة السريعة):

```
1. أرسلي في المجموعة:  /id
   ← ستحصلين على Chat ID

2. سجّلي دخول على لوحة التحكم (أو استخدمي API مباشرةً)

3. أنشئي فصلاً جديداً مع Bot Token + Chat ID

4. اضغطي "ربط Webhook"
```

### مباشرةً عبر API:

```bash
# 1. تسجيل دخول
curl -X POST https://wird-api.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpass"}'
# ← احفظي access_token

# 2. إنشاء فصل
curl -X POST https://wird-api.onrender.com/api/classes/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "حلقة القرآن",
    "bot_token": "123456:ABC...",
    "telegram_chat_id": -100123456789,
    "wird_time": "07:00",
    "timezone": "Asia/Riyadh"
  }'
# ← احفظي class_id

# 3. ربط Webhook
curl -X POST https://wird-api.onrender.com/api/classes/<class_id>/set-webhook \
  -H "Authorization: Bearer <token>"
```

---

## أوامر البوت للمعلمة

بعد إضافة البوت للمجموعة، هذه الأوامر متاحة للمعلمة فقط:

| الأمر | الوظيفة |
|-------|---------|
| `/wird سورة الكهف` | تعيين ورد اليوم |
| `/report` | تقرير الحضور الآن |
| `/report week` | تقرير الأسبوع |
| `/remind` | إرسال تذكير يدوي |
| `/summary` | نشر ملخص المجموعة الآن |
| `/settings` | لوحة إعدادات بأزرار |
| `/id` | معرفة Chat ID |
| `/myid` | معرفة Telegram ID الشخصي |

وللطلاب:

| الأمر | الوظيفة |
|-------|---------|
| `/today` | ورد اليوم |
| `/myprogress` | إحصائياتي |
| `/streak` | سلسلتي 🔥 |

---

## التحقق من أن كل شيء يعمل

```bash
# Backend حي؟
curl https://wird-api.onrender.com/health
# → {"status":"ok","app":"ورد"}

# Webhook مضبوط؟
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
# → تحقق من url و pending_update_count

# اختبار مهمة الورد يدوياً
curl -X POST https://wird-api.onrender.com/api/tasks/send-wird \
  -H "X-Cron-Secret: <CRON_SECRET>"
```

---

## هيكل الملفات

```
wird_tel/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── tasks.py          ← cron endpoints (الجديد)
│   │   │   ├── attendance.py
│   │   │   ├── auth.py
│   │   │   ├── classes.py
│   │   │   ├── reports.py
│   │   │   ├── telegram_webhook.py
│   │   │   └── wird.py
│   │   ├── telegram/
│   │   │   ├── bot.py            ← student commands + callback handlers
│   │   │   └── teacher_commands.py  ← /wird /report /remind /summary /settings
│   │   ├── services/
│   │   │   ├── attendance_service.py
│   │   │   ├── student_service.py
│   │   │   └── wird_service.py   ← (scheduler_service.py حُذف)
│   │   ├── models/  core/  db/
│   │   └── main.py               ← no scheduler, just routes
│   └── requirements.txt          ← أبسط (حُذف celery/redis/apscheduler)
├── frontend/                     ← Next.js (اختياري)
├── docs/
│   ├── schema.sql
│   └── DEPLOYMENT.md             ← هذا الملف
└── docker-compose.yml
```
