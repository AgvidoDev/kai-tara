-- Астрологические прогнозы: схема PostgreSQL
-- Данные рождения = персональные данные (152-ФЗ): шифровать на уровне приложения, хранить согласие.

CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    tg_id           BIGINT UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    sign_mode       TEXT NOT NULL DEFAULT 'sun_trop'   -- moon | sun_sid | sun_trop
                    CHECK (sign_mode IN ('moon','sun_sid','sun_trop')),
    city_key        TEXT NOT NULL DEFAULT 'moscow',
    tz              TEXT NOT NULL DEFAULT 'Europe/Moscow',
    consent_pd_at   TIMESTAMPTZ                         -- когда дано согласие на обработку ПД
);

CREATE TABLE birth_data (
    user_id         BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    birth_enc       BYTEA NOT NULL,      -- зашифрованные: дата, время, место, координаты
    time_known      BOOLEAN NOT NULL DEFAULT false,
    -- вычисленные (не идентифицирующие) поля для быстрых рассылок:
    moon_rashi      SMALLINT CHECK (moon_rashi BETWEEN 0 AND 11),
    sun_sid_rashi   SMALLINT CHECK (sun_sid_rashi BETWEEN 0 AND 11),
    sun_trop_sign   SMALLINT CHECK (sun_trop_sign BETWEEN 0 AND 11),
    lagna_rashi     SMALLINT CHECK (lagna_rashi BETWEEN 0 AND 11),
    moon_nakshatra  SMALLINT CHECK (moon_nakshatra BETWEEN 0 AND 26),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Сырые расчёты (JSON из jyotish.forecast.build) — источник для текстов и видео
CREATE TABLE forecast_runs (
    id              BIGSERIAL PRIMARY KEY,
    kind            TEXT NOT NULL,       -- new_moon | full_moon | eclipse | ingress | day | week | month | year | mundane
    event_at        TIMESTAMPTZ NOT NULL,
    period_end      TIMESTAMPTZ,
    city_key        TEXT NOT NULL,
    ayanamsha       TEXT NOT NULL DEFAULT 'lahiri',
    true_node       BOOLEAN NOT NULL DEFAULT false,
    facts           JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (kind, event_at, city_key, ayanamsha, true_node)
);

-- Готовые тексты по знакам и каналам
CREATE TABLE forecast_texts (
    id              BIGSERIAL PRIMARY KEY,
    run_id          BIGINT NOT NULL REFERENCES forecast_runs(id) ON DELETE CASCADE,
    sign_mode       TEXT NOT NULL,
    sign            SMALLINT NOT NULL CHECK (sign BETWEEN 0 AND 11),
    channel         TEXT NOT NULL,       -- telegram | youtube_script | site | email
    style           TEXT NOT NULL DEFAULT 'pentacore',
    body            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','published')),
    published_at    TIMESTAMPTZ,
    UNIQUE (run_id, sign_mode, sign, channel, style)
);

-- Персональные прогнозы
CREATE TABLE personal_forecasts (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    facts           JSONB NOT NULL,      -- даша, транзиты от лагны и Луны
    body            TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Корпус референсных прогнозов лидеров рынка (для анализа структуры и стиля, не для копирования)
CREATE TABLE reference_corpus (
    id              BIGSERIAL PRIMARY KEY,
    author          TEXT NOT NULL,
    system          TEXT,                -- jyotish | western | tarot | numerology | deep_sky
    source_url      TEXT,
    published_at    DATE,
    kind            TEXT,
    transcript      TEXT,
    structure       JSONB                -- разметка: блоки, длина, призывы, темы
);

CREATE INDEX ON birth_data (moon_rashi);
CREATE INDEX ON birth_data (sun_trop_sign);
CREATE INDEX ON forecast_texts (status, channel);
