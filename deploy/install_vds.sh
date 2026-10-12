#!/usr/bin/env bash
# Установка/обновление астробота на Debian/Ubuntu VDS.
# Запуск из распакованной папки проекта:  sudo bash deploy/install_vds.sh
# Повторный запуск = обновление кода; .env, ключ и база не трогаются.
set -euo pipefail

APP_USER=astro
APP_DIR=/opt/astro
DB_NAME=astro
DB_USER=astro
SERVICE=astro-bot
SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"

[[ $EUID -eq 0 ]] || { echo "Запустите через sudo"; exit 1; }
say() { echo -e "\n\033[1;36m==> $*\033[0m"; }
cd /   # иначе sudo -u postgres ругается «could not change directory to /root»

say "Системные пакеты"
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-dev build-essential rsync fonts-dejavu-core >/dev/null
if ! command -v psql >/dev/null; then
    say "PostgreSQL не найден — устанавливаю"
    apt-get install -y -qq postgresql >/dev/null
fi
if ! sudo -u postgres psql -tAc "SELECT 1" &>/dev/null; then
    say "Запускаю PostgreSQL"
    if [[ -d /run/systemd/system ]]; then systemctl enable --now postgresql; else service postgresql start; fi
    sleep 2
fi

say "Пользователь $APP_USER и папка $APP_DIR"
id "$APP_USER" &>/dev/null || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
mkdir -p "$APP_DIR"
rsync -a --delete \
    --exclude '.env' --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
    --exclude 'forecast.json' --exclude 'forecast.md' \
    --exclude '.git' --exclude 'tests' --exclude '.pytest_cache' \
    "$SRC_DIR"/ "$APP_DIR"/

say "Python-окружение"
[[ -d "$APP_DIR/.venv" ]] || python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -q --upgrade pip setuptools wheel
"$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
"$APP_DIR/.venv/bin/python" -c "import swisseph, aiogram, asyncpg; print('  библиотеки OK, swisseph', swisseph.version)"

ENV_FILE="$APP_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    say "Первичная настройка .env"
    DB_PASS="$(openssl rand -hex 16)"
    while :; do
        read -rp "  BOT_TOKEN (от @BotFather): " BOT_TOKEN
        [[ "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]{30,}$ ]] && break
        echo "  формат токена: 123456789:AA... — попробуйте ещё раз"
    done
    while :; do
        read -rp "  ADMIN_IDS (числовой Telegram ID через запятую, можно пусто; узнать — @userinfobot): " ADMIN_IDS
        [[ "$ADMIN_IDS" =~ ^(-?[0-9]+(,-?[0-9]+)*)?$ ]] && break
        echo "  нужны цифры, не @username"
    done
    umask 077
    cat > "$ENV_FILE" <<EOF
BOT_TOKEN=$BOT_TOKEN
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
ADMIN_IDS=$ADMIN_IDS
EOF
    NEW_DB_PASS="$DB_PASS"
else
    say ".env уже есть — оставляю как есть"
    NEW_DB_PASS=""
fi
chown "$APP_USER:$APP_USER" "$ENV_FILE"; chmod 600 "$ENV_FILE"

say "База данных $DB_NAME"
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    [[ -n "$NEW_DB_PASS" ]] || { echo "  Роль $DB_USER отсутствует, а .env уже существует — задайте пароль вручную"; exit 1; }
    sudo -u postgres psql -qc "CREATE ROLE $DB_USER LOGIN PASSWORD '$NEW_DB_PASS';"
elif [[ -n "$NEW_DB_PASS" ]]; then
    sudo -u postgres psql -qc "ALTER ROLE $DB_USER PASSWORD '$NEW_DB_PASS';"
fi
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
    sudo -u postgres psql -qc "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
fi
# закрыть чужим доступ к базе (на сервере есть другие проекты)
sudo -u postgres psql -qc "REVOKE ALL ON DATABASE $DB_NAME FROM PUBLIC;"
DB_URL="$(grep '^DATABASE_URL=' "$ENV_FILE" | cut -d= -f2-)"
if [[ "$(psql "$DB_URL" -tAc "SELECT to_regclass('public.users') IS NOT NULL")" != "t" ]]; then
    psql "$DB_URL" -q -f "$APP_DIR/schema.sql"
    echo "  схема создана"
else
    echo "  схема уже есть"
fi

chown -R "$APP_USER:$APP_USER" "$APP_DIR"

say "Проверка расчётов"
sudo -u "$APP_USER" bash -c "cd $APP_DIR && .venv/bin/python run_forecast.py --out /tmp/astro_check >/dev/null && head -3 /tmp/astro_check.md && rm -f /tmp/astro_check.*"

if [[ -d /run/systemd/system ]]; then
    say "Сервис $SERVICE"
    cp "$APP_DIR/deploy/astro-bot.service" "/etc/systemd/system/$SERVICE.service"
    systemctl daemon-reload
    systemctl enable -q "$SERVICE"
    if grep -q '^BOT_TOKEN=.\+' "$ENV_FILE"; then
        systemctl restart "$SERVICE"
        sleep 4
        systemctl --no-pager --lines=8 status "$SERVICE" || true
    else
        echo "  BOT_TOKEN пуст — впишите его в $ENV_FILE и выполните: systemctl restart $SERVICE"
    fi
else
    echo "systemd недоступен — сервис не установлен"
fi

say "Готово"
echo "  Логи:        journalctl -u $SERVICE -f"
echo "  Перезапуск:  systemctl restart $SERVICE"
