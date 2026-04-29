import os
import django
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Care_Coffee.settings')
django.setup()

from shop.models import Product

# Update product image paths
products = Product.objects.all()
updated_count = 0

for product in products:
    if product.image and 'products/2025/08/06/' in product.image.name:
        # Extract just the filename
        filename = product.image.name.split('/')[-1]
        # Update to new path
        product.image.name = f'products/{filename}'
        product.save()
        updated_count += 1
        print(f'Updated {product.name}: {product.image.name}')

print(f'\nTotal updated: {updated_count} products')
