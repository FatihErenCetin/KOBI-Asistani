#!/usr/bin/env bash
# Postgres'te ana DB'yi drop edip yeniden olusturur, migration uygular, seed yapar.
set -euo pipefail

docker compose exec -T postgres psql -U kobi -d postgres -c "DROP DATABASE IF EXISTS kobi_db WITH (FORCE);"
docker compose exec -T postgres psql -U kobi -d postgres -c "CREATE DATABASE kobi_db;"
alembic upgrade head
python -m app.db.seed --demo-fixtures
echo "DB reset complete with demo fixtures."
