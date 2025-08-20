from django.db import models

# Create your models here.

class Order(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    email = models.EmailField()

    chapa_tx_ref = models.CharField(max_length=100, unique=True, blank=True, null=True)
    paid = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['paid','created']),
        ]
        ordering = ['-created']

    def __str__(self):
        return f'Order {self.id} - {self.first_name} {self.last_name}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_chapa_url(self):
        if not self.chapa_tx_ref:
            return ''
        
    
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        'shop.Product',
        related_name="order_items",
        on_delete=models.CASCADE
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.product} ({self.quantity})'

    def get_cost(self):
        return self.price * self.quantity