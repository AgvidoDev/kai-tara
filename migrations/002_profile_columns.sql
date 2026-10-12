-- Астропрофиль вместо данных рождения: дополнительные вычисленные поля.
ALTER TABLE birth_data ADD COLUMN IF NOT EXISTS moon_pada       SMALLINT CHECK (moon_pada BETWEEN 1 AND 4);
ALTER TABLE birth_data ADD COLUMN IF NOT EXISTS moon_first_half BOOLEAN;
ALTER TABLE birth_data ADD COLUMN IF NOT EXISTS planet_rashi    SMALLINT[];
ALTER TABLE birth_data ADD COLUMN IF NOT EXISTS dashas          JSONB;
