-- Язык интерфейса: ru | en. Существующие пользователи — русскоязычные.
ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT;
UPDATE users SET lang = 'ru' WHERE lang IS NULL;
