-- Разовые покупки PDF-разбора натальной карты.
ALTER TABLE users ADD COLUMN IF NOT EXISTS report_credits INT NOT NULL DEFAULT 0;
