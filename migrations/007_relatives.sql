-- Близкие: только астропрофиль и имя, без даты, времени и места рождения.
CREATE TABLE IF NOT EXISTS relatives (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    time_known      BOOLEAN NOT NULL DEFAULT false,
    moon_rashi      SMALLINT CHECK (moon_rashi BETWEEN 0 AND 11),
    sun_sid_rashi   SMALLINT CHECK (sun_sid_rashi BETWEEN 0 AND 11),
    sun_trop_sign   SMALLINT CHECK (sun_trop_sign BETWEEN 0 AND 11),
    lagna_rashi     SMALLINT CHECK (lagna_rashi BETWEEN 0 AND 11),
    moon_nakshatra  SMALLINT CHECK (moon_nakshatra BETWEEN 0 AND 26),
    moon_pada       SMALLINT CHECK (moon_pada BETWEEN 1 AND 4),
    moon_first_half BOOLEAN,
    planet_rashi    SMALLINT[],
    dashas          JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS relatives_user ON relatives (user_id);
