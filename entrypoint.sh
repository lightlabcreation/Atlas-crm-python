#!/bin/bash
set -e

# Wait for PostgreSQL to be ready (if using PostgreSQL)
if [ "$DATABASE" = "postgres" ]; then
    echo "Waiting for postgres..."
    # Use Python to check PostgreSQL connection if nc is not available
    until python -c "import psycopg2; psycopg2.connect(dbname='${DB_NAME}', user='${DB_USER}', password='${DB_PASSWORD}', host='${DB_HOST}', port='${DB_PORT}')" 2>/dev/null; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 1
    done
    echo "PostgreSQL started"
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Make migrations
echo "Making migrations..."
python manage.py makemigrations || true

# Apply migrations
echo "Applying migrations..."
python manage.py migrate --noinput

echo "Applying Roles&Permitions..."
python manage.py create_default_permissions
python manage.py create_default_roles

# Create superuser (only if it doesn't exist)
echo "Creating superuser (if needed)..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        email='admin@devm7md.xyz',
        username='admin',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print('Superuser created')
else:
    print('Superuser already exists')
EOF

# Execute command
exec "$@"

