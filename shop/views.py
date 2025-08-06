from django.shortcuts import render
from .models import Category, Product
# Create your views here.

def product_list(request):
    
    categories = Category.objects.all()
    selected_categories = request.GET.getlist('category')
    
    products = Product.objects.filter(available=True)
    if selected_categories:
        products = products.filter(category__slug__in=selected_categories)
    
    
    return render(request,
                  'shop/product/product_list.html',
                  {'categories': categories,
                   'products':products,
                   'selected_categories':selected_categories,
                   })


def product_detail(request):
    pass