import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone


def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


@dataclass
class Config:
    bot_token: str
    dsn: str
    fernet_key: str
    admin_ids: set[int] = field(default_factory=set)
    check_interval_sec: int = 600       # как часто проверять лунации
    send_window_hours: float = 6        # рассылаем, если лунация была не позже N часов назад
    price_premium: int = 199            # ⭐ за 30 дней подписки
    price_compat: int = 99              # ⭐ за одну проверку совместимости
    price_report: int = 149             # ⭐ за PDF-разбор натальной карты
    trial_days: int = 3
    ref_bonus_days: int = 7
    daily_hour: int = 7                 # час утренней рассылки по местному времени
    free_until: date | None = None      # промо: до этой даты включительно Премиум бесплатен всем
    free_mode: bool = False             # бесплатный продукт без срока: оплата выключена полностью
    source_url: str = ""                # публичный репозиторий кода (AGPL-3.0): команда /source

    @property
    def promo_active(self) -> bool:
        """Бесплатный режим или промо до конца дня free_until по Москве."""
        if self.free_mode:
            return True
        if not self.free_until:
            return False
        return datetime.now(timezone(timedelta(hours=3))).date() <= self.free_until


def _parse_admin_ids(raw: str) -> set[int]:
    ids = set()
    for x in raw.split(","):
        x = x.strip()
        if not x:
            continue
        if x.lstrip("-").isdigit():
            ids.add(int(x))
        else:
            logging.warning("ADMIN_IDS: '%s' пропущен — нужен числовой Telegram ID, не @username", x)
    return ids


def load() -> Config:
    _load_dotenv()
    return Config(
        bot_token=os.environ["BOT_TOKEN"],
        dsn=os.environ.get("DATABASE_URL", "postgresql://astro:astro@localhost/astro"),
        fernet_key=os.environ.get("FERNET_KEY", ""),
        admin_ids=_parse_admin_ids(os.environ.get("ADMIN_IDS", "")),
        price_premium=int(os.environ.get("PRICE_PREMIUM", 199)),
        price_compat=int(os.environ.get("PRICE_COMPAT", 99)),
        price_report=int(os.environ.get("PRICE_REPORT", 149)),
        trial_days=int(os.environ.get("TRIAL_DAYS", 3)),
        ref_bonus_days=int(os.environ.get("REF_BONUS_DAYS", 7)),
        daily_hour=int(os.environ.get("DAILY_HOUR", 7)),
        free_until=date.fromisoformat(os.environ["FREE_UNTIL"]) if os.environ.get("FREE_UNTIL") else None,
        free_mode=os.environ.get("FREE_MODE", "").strip().lower() in ("1", "true", "yes", "on"),
        source_url=os.environ.get("SOURCE_URL", "").strip(),
    )
