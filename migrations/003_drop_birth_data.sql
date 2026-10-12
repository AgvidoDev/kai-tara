-- Дату, время и место рождения больше не храним (152-ФЗ, GDPR): остаётся только профиль.
-- Перед этой миграцией бот пересчитывает профили из старых зашифрованных записей.
ALTER TABLE birth_data DROP COLUMN IF EXISTS birth_enc;
ALTER TABLE birth_data RENAME TO profiles;
