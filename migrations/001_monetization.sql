-- Премиум-подписка (Telegram Stars), разовые покупки, рефералы, утренняя рассылка.
ALTER TABLE users ADD COLUMN IF NOT EXISTS premium_until  TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_used     BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS compat_credits INT     NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by    BIGINT;              -- tg_id пригласившего
ALTER TABLE users ADD COLUMN IF NOT EXISTS ref_rewarded   BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_push     BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS sub_charge_id  TEXT;                -- последний платёж подписки
ALTER TABLE users ADD COLUMN IF NOT EXISTS sub_canceled   BOOLEAN NOT NULL DEFAULT false;

-- Платежи храним и после удаления пользователя (учёт, возвраты), поэтому tg_id, а не FK
CREATE TABLE IF NOT EXISTS payments (
    id              BIGSERIAL PRIMARY KEY,
    tg_id           BIGINT NOT NULL,
    charge_id       TEXT NOT NULL UNIQUE,      -- telegram_payment_charge_id
    product         TEXT NOT NULL,             -- premium_sub | compat
    stars           INT NOT NULL,
    is_recurring    BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    refunded_at     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS payments_tg_id_idx ON payments (tg_id);

CREATE TABLE IF NOT EXISTS daily_sent (
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day             DATE NOT NULL,
    PRIMARY KEY (user_id, day)
);
