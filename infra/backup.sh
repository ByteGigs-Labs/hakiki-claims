#!/usr/bin/env bash
# Daily Postgres dump, kept for 14 days. Install with:
#   (crontab -l; echo "17 2 * * * /opt/hakiki/infra/backup.sh") | crontab -
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/hakiki}"
cd "$APP_DIR"
set -a; . ./.env; set +a

stamp="$(date +%Y%m%d-%H%M%S)"
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom > "backups/hakiki-$stamp.dump"
chmod 600 "backups/hakiki-$stamp.dump"
find backups -name 'hakiki-*.dump' -mtime +14 -delete
