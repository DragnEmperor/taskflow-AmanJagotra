#!/bin/sh
set -e

# Auto-generate Django secret key if not provided
if [ -z "$DJANGO_SECRET_KEY" ]; then
    echo "Generating Django secret key..."
    DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    export DJANGO_SECRET_KEY
    echo "Django secret key generated."
fi

# Auto-generate JWT RS256 keys if not provided
if [ -z "$JWT_SIGNING_KEY" ] || [ -z "$JWT_VERIFICATION_KEY" ]; then
    echo "Generating JWT RS256 key pair..."
    JWT_SIGNING_KEY=$(openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 2>/dev/null)
    JWT_VERIFICATION_KEY=$(echo "$JWT_SIGNING_KEY" | openssl pkey -pubout 2>/dev/null)
    export JWT_SIGNING_KEY JWT_VERIFICATION_KEY
    echo "JWT signing and verification keys generated."
fi

RDS_HOST=${RDS_HOST:-db}
RDS_PORT=${RDS_PORT:-5432}

echo "Waiting for PostgreSQL at ${RDS_HOST}:${RDS_PORT}..."
while ! python -c "
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('${RDS_HOST}', ${RDS_PORT}))
    s.close()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --noinput

if [ "$SEED_DB" = "true" ]; then
    echo "Seeding database..."
    python manage.py seed
fi

echo "Starting server..."
exec gunicorn greening.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
