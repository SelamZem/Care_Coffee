#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create media directory if it doesn't exist
mkdir -p media

# Collect static files with clear flag to avoid conflicts
python manage.py collectstatic --noinput --clear

# Copy media files to staticfiles so WhiteNoise can serve them
if [ -d "media" ]; then
    cp -r media/* staticfiles/ 2>/dev/null || true
fi

# Run database migrations
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@carecoffee.com', 'admin123')" | python manage.py shell
