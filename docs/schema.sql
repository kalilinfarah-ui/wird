-- ================================================================
-- ورد — Database Schema for Supabase (PostgreSQL)
-- Run this in Supabase SQL Editor
-- ================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────────────
-- USERS (Teachers, Admins)
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE,
    hashed_password TEXT,
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(50) NOT NULL DEFAULT 'teacher'
                        CHECK (role IN ('super_admin','teacher','assistant')),
    telegram_id     BIGINT UNIQUE,
    telegram_username VARCHAR(100),
    telegram_photo_url TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- ORGANIZATIONS
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE organizations (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    logo_url    TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    owner_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- CLASSES (Telegram Groups/Channels)
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE classes (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    telegram_chat_id    BIGINT UNIQUE,
    telegram_chat_title VARCHAR(255),
    telegram_chat_type  VARCHAR(50),
    bot_token           TEXT,
    wird_time           VARCHAR(10) NOT NULL DEFAULT '07:00',
    timezone            VARCHAR(50) NOT NULL DEFAULT 'Asia/Riyadh',
    reminder_1_hours    VARCHAR(10) DEFAULT '2',
    reminder_2_hours    VARCHAR(10) DEFAULT '6',
    reminder_3_time     VARCHAR(10) DEFAULT '21:00',
    reminders_enabled   BOOLEAN NOT NULL DEFAULT TRUE,
    completion_keywords TEXT DEFAULT 'تم,done,finished,✔,✅,قرأت,read',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    teacher_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id     UUID REFERENCES organizations(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- STUDENTS
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE students (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id       BIGINT NOT NULL,
    telegram_username VARCHAR(100),
    full_name         VARCHAR(255) NOT NULL,
    photo_url         TEXT,
    class_id          UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    left_at           TIMESTAMPTZ,
    total_completed   INTEGER NOT NULL DEFAULT 0,
    total_missed      INTEGER NOT NULL DEFAULT 0,
    current_streak    INTEGER NOT NULL DEFAULT 0,
    longest_streak    INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(telegram_id, class_id)
);

-- ─────────────────────────────────────────────────────────────────
-- DAILY WIRD
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE daily_wirds (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id            UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    wird_date           DATE NOT NULL,
    wird_type           VARCHAR(50) NOT NULL DEFAULT 'quran'
                            CHECK (wird_type IN ('quran','adhkar','hadith','mixed')),
    title               VARCHAR(500) NOT NULL,
    content             TEXT,
    file_url            TEXT,
    file_type           VARCHAR(50),   -- pdf, image, audio, video
    motivational_message TEXT,
    telegram_message_id BIGINT,
    status              VARCHAR(50) NOT NULL DEFAULT 'scheduled'
                            CHECK (status IN ('scheduled','sent','failed')),
    sent_at             TIMESTAMPTZ,
    scheduled_time      VARCHAR(10),
    is_holiday          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(class_id, wird_date)
);

-- ─────────────────────────────────────────────────────────────────
-- ATTENDANCE
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE attendance (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id        UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    daily_wird_id     UUID NOT NULL REFERENCES daily_wirds(id) ON DELETE CASCADE,
    class_id          UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    completed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completion_method VARCHAR(50) NOT NULL DEFAULT 'button'
                          CHECK (completion_method IN ('button','keyword','reaction','manual')),
    note              TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, daily_wird_id)
);

-- ─────────────────────────────────────────────────────────────────
-- REMINDERS
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE reminders (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id         UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    daily_wird_id    UUID NOT NULL REFERENCES daily_wirds(id) ON DELETE CASCADE,
    reminder_number  SMALLINT NOT NULL CHECK (reminder_number IN (1,2,3)),
    scheduled_at     TIMESTAMPTZ NOT NULL,
    sent_at          TIMESTAMPTZ,
    status           VARCHAR(50) NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending','sent','skipped','failed')),
    recipients_count INTEGER DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- STREAKS
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE streaks (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id   UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date   DATE,
    length     INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- NOTIFICATIONS
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE notifications (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type       VARCHAR(50) NOT NULL,
    title      VARCHAR(255) NOT NULL,
    body       TEXT NOT NULL,
    is_read    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- INDEXES (for performance)
-- ─────────────────────────────────────────────────────────────────
CREATE INDEX idx_students_telegram_id   ON students(telegram_id);
CREATE INDEX idx_students_class_id      ON students(class_id);
CREATE INDEX idx_daily_wirds_date       ON daily_wirds(wird_date);
CREATE INDEX idx_daily_wirds_class_date ON daily_wirds(class_id, wird_date);
CREATE INDEX idx_attendance_student     ON attendance(student_id);
CREATE INDEX idx_attendance_wird        ON attendance(daily_wird_id);
CREATE INDEX idx_attendance_class       ON attendance(class_id);
CREATE INDEX idx_reminders_scheduled    ON reminders(scheduled_at) WHERE status = 'pending';
CREATE INDEX idx_classes_chat_id        ON classes(telegram_chat_id);

-- ─────────────────────────────────────────────────────────────────
-- Row Level Security (Supabase)
-- ─────────────────────────────────────────────────────────────────
-- Enable RLS on all tables
ALTER TABLE users         ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE classes       ENABLE ROW LEVEL SECURITY;
ALTER TABLE students      ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_wirds   ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance    ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders     ENABLE ROW LEVEL SECURITY;
ALTER TABLE streaks       ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Service role bypasses RLS (used by backend)
-- The backend uses SUPABASE_SERVICE_KEY which bypasses RLS automatically.
-- No additional policies needed for the backend service account.
