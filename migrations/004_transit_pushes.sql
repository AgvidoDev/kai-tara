-- Пуши о больших транзитах (смена узлов, Юпитер): анонс и день события, без повторов.
CREATE TABLE IF NOT EXISTS transit_pushes (
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key         TEXT NOT NULL,          -- nodes-2026-12 | jupiter-2026-10
    stage       TEXT NOT NULL,          -- teaser | day
    sent_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, key, stage)
);
