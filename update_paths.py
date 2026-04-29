from shop.models import Product

# Update product image paths
products = Product.objects.filter(image__startswith='products/2025/08/06/')
updated_count = 0

for product in products:
    if product.image:
        # Extract just the filename
        filename = product.image.name.split('/')[-1]
        # Update to new path
        product.image.name = f'products/{filename}'
        product.save()
        updated_count += 1
        print(f'Updated {product.name}: {product.image.name}')

print(f'\nTotal updated: {updated_count} products')
