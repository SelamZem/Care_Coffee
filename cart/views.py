from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart


# Create your views here.

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1)
    return redirect('cart:cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect("cart:cart_detail")


def cart_detail(request):
    cart = Cart(request)
    return render(request,
                  'cart/cart_detail.html',
                  {'cart':cart})


@require_POST
def cart_update_quantities(request):
    cart = Cart(request)
    for key, value in request.POST.items():
        if key.startswith('quantity_'):
            product_id = key.split('_')[1]            
            quantity = int(value)
            if 1 <= quantity <= 20:
                product = get_object_or_404(Product, id=product_id)
                cart.add(product=product, quantity=quantity, override_quantity=True)

    return redirect('cart:cart_detail')