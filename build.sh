#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create media directory if it doesn't exist
mkdir -p media
chmod 755 media

# Collect static files with clear flag to avoid conflicts
python manage.py collectstatic --noinput --clear

# Ensure media directory exists in staticfiles for WhiteNoise
mkdir -p staticfiles/media
chmod 755 staticfiles/media

# Copy any existing media files to staticfiles/media
if [ -d "media" ] && [ "$(ls -A media 2>/dev/null)" ]; then
    cp -r media/* staticfiles/media/ 2>/dev/null || true
fi

# Run database migrations
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@carecoffee.com', 'admin123')" | python manage.py shell
