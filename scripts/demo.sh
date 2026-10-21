#!/usr/bin/env bash
# One-command demo: creates .env if missing, starts the stack, seeds it and prints the login.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v docker >/dev/null || { echo "Docker is required" >&2; exit 1; }

random() { openssl rand -hex "$1"; }

if [[ ! -f .env ]]; then
  password="$(random 8)"
  db_password="$(random 12)"
  sed -e "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$db_password/" \
      -e "s#^DATABASE_URL=.*#DATABASE_URL=postgresql+psycopg://hakiki:$db_password@127.0.0.1:5433/hakiki#" \
      -e "s/^HMAC_KEY=.*/HMAC_KEY=$(random 32)/" \
      -e "s/^DEMO_USER_PASSWORD=.*/DEMO_USER_PASSWORD=$password/" \
      .env.example > .env
  echo "Created .env with fresh secrets"
fi

set -a
source <(grep -E '^(API_PORT|DASHBOARD_PORT|DEMO_USER_EMAIL|DEMO_USER_PASSWORD)=' .env)
set +a

docker compose up --build -d --wait
docker compose exec -T api python -m scripts.seed

cat <<EOF

Hakiki is running.
  Dashboard  http://localhost:${DASHBOARD_PORT:-8080}
  API docs   http://localhost:${API_PORT:-8000}/docs
  Login      ${DEMO_USER_EMAIL}
  Password   ${DEMO_USER_PASSWORD}

Stop it with: docker compose down
EOF
