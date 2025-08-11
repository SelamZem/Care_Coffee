from django.shortcuts import render, get_object_or_404
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


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True) 
    
    return render(request,
                  'shop/product/product_detail.html',
                  {'product': product})
    