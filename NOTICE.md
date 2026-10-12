# Kai Tara — лицензии и сторонние компоненты

Исходный код бота Kai Tara распространяется по лицензии **GNU AGPL-3.0** (файл `LICENSE`).
Это требование библиотеки Swiss Ephemeris: сервис, работающий для пользователей по сети, обязан
предоставлять им исходный код. В боте ссылка на код — команда `/source`.

Данные пользователей (база данных) и секреты (`.env`) в репозиторий не входят.

| Компонент | Назначение | Лицензия |
|---|---|---|
| Swiss Ephemeris (Astrodienst AG) | астрономические расчёты | AGPL-3.0 или Swiss Ephemeris Professional License |
| pyswisseph | Python-обёртка Swiss Ephemeris | AGPL-3.0 |
| GeoNames (`data/cities.tsv.gz`) | названия и координаты городов | CC BY 4.0, https://www.geonames.org |
| aiogram | Telegram Bot API | MIT |
| asyncpg | PostgreSQL | Apache-2.0 |
| timezonefinder | часовой пояс по координатам | MIT |
| Pillow | картинка натальной карты | MIT-CMU (HPND) |
| reportlab | PDF-отчёты | BSD |
| DejaVu Fonts (на сервере, пакет fonts-dejavu-core) | шрифт с кириллицей | Bitstream Vera / DejaVu License |

Тексты трактовок, словаря и отчётов написаны для проекта Kai Tara и распространяются вместе с кодом
по AGPL-3.0.
