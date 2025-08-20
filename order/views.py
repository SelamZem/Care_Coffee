from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
import uuid
import requests
from django.conf import settings
from django.urls import reverse
from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem


@login_required(login_url='account:login')
def order_create(request):
    cart = Cart(request)
    cart_items = []
    total = 0
    for item in cart:
        item_total = item['quantity'] * item['price']
        total += item_total
        cart_items.append({
            'product': item['product'],
            'quantity': item['quantity'],
            'price': item['price'],
            'total': item_total
        })

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.chapa_tx_ref = str(uuid.uuid4())
            order.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
            cart.clear()
            request.session['order_id'] = order.id
            return redirect('order:order_pay', order_id=order.id)
    else:
        form = OrderCreateForm()

    return render(request, 'orders/order_create.html', {
        'cart_items': cart_items,
        'cart_total': total,
        'form': form
    })


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/orders/order_detail.html', {'order': order})


@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order/pdf.html', {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=order_{order.id}.pdf'
    weasyprint.HTML(string=html).write_pdf(
        response,
        stylesheets=[weasyprint.CSS('css/pdf.css')]
    )
    return response


@login_required(login_url='account:login')
def order_pay(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not order.chapa_tx_ref:
        order.chapa_tx_ref = str(uuid.uuid4())
        order.save()

    data = {
        "amount": float(order.get_total_cost()),
        "email": order.email,
        "first_name": order.first_name,
        "last_name": order.last_name,
        "tx_ref": order.chapa_tx_ref,
        "callback_url": request.build_absolute_uri(reverse("order:chapa_callback")),
        "currency": "ETB"
    }

    headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
    response = requests.post(
        "https://api.chapa.co/v1/transaction/initialize/",
        json=data,
        headers=headers
    )
    res = response.json()

    if res.get('status') == 'success':
        return redirect(res['data']['checkout_url'])
    return redirect('order:payment_failed')


def chapa_callback(request):
    tx_ref = request.GET.get('tx_ref')
    if not tx_ref:
        return HttpResponse("Transaction reference missing", status=400)

    order = get_object_or_404(Order, chapa_tx_ref=tx_ref)
    headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
    response = requests.get(
        f"https://api.chapa.co/v1/transaction/verify/{tx_ref}/",
        headers=headers
    )
    res = response.json()

    if res.get('status') == 'success' and res['data']['status'] == 'success':
        order.paid = True
        order.save()
        return redirect('order:order_success', order_id=order.id)
    return redirect('order:payment_failed')


@login_required(login_url='account:login')
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    chapa_receipt = f"https://checkout.chapa.co/receipt/{order.chapa_tx_ref}" if order.paid else None
    return render(request, 'orders/order_success.html', {
        'order': order,
        'chapa_receipt': chapa_receipt
    })


@login_required(login_url='account:login')
def payment_failed(request):
    return render(request, 'orders/order_payment_failed.html')
