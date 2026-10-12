#!/usr/bin/env bash
# Чистая публичная копия кода для репозитория с открытым исходным кодом (AGPL-3.0).
# Без истории коммитов и служебных файлов (CLAUDE.md с адресом сервера, исследования, черновики).
# Запуск из корня проекта: bash tools/export_public.sh ../astro-public
set -euo pipefail
OUT="${1:?укажите папку, например ../astro-public}"
EXCLUDE=(CLAUDE.md docs novolunie_2026-11-09.md)

rm -rf "$OUT.tmp" && mkdir -p "$OUT.tmp"
git archive HEAD | tar -x -C "$OUT.tmp"
for p in "${EXCLUDE[@]}"; do rm -rf "$OUT.tmp/$p"; done

# Проверка: в публичной копии не должно быть приватных данных. Общий шаблон — токен бота;
# личные шаблоны (IP сервера, ID админа и т.п.) — по строке в tools/.private_patterns (не в git).
PATTERNS="[0-9]{8,10}:AA[A-Za-z0-9_-]{30,}"
if [[ -f tools/.private_patterns ]]; then
    while IFS= read -r line; do [[ -n "$line" ]] && PATTERNS="$PATTERNS|$line"; done < tools/.private_patterns
else
    echo "Внимание: нет tools/.private_patterns — проверяю только токены" >&2
fi
if grep -rIlE "$PATTERNS" "$OUT.tmp"; then
    echo "СТОП: найдены приватные данные (см. файлы выше)" >&2
    exit 1
fi

if [[ -d "$OUT/.git" ]]; then             # обновление: сохраняем историю публичного репозитория
    mv "$OUT/.git" "$OUT.tmp/.git"
fi
rm -rf "$OUT" && mv "$OUT.tmp" "$OUT"
echo "Публичная копия: $OUT ($(find "$OUT" -type f -not -path '*/.git/*' | wc -l) файлов)"
