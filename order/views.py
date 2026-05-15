import json
import logging
import uuid
import requests
import weasyprint
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem

logger = logging.getLogger(__name__)


# ─── Order History ───────────────────────────────────────────────────────────

@login_required(login_url='account:login')
def order_history(request):
    orders = Order.objects.filter(user=request.user, paid=True).prefetch_related('items__product')
    return render(request, 'orders/order_history.html', {'orders': orders})


# ─── Order Create ────────────────────────────────────────────────────────────

@login_required(login_url='account:login')
def order_create(request):
    cart = Cart(request)
    cart_items = []
    total = 0
    for item in cart:
        item_total = item['quantity'] * item['price']
        total += item_total
        cart_items.append({
            'product':  item['product'],
            'quantity': item['quantity'],
            'price':    item['price'],
            'total':    item_total,
        })

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # Create order but don't save to DB yet
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            
            # Create order items
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
            
            # DON'T clear cart yet - wait until payment is successful
            # cart.clear()
            
            # Redirect to payment
            return redirect('order:order_pay', order_id=order.id)
    else:
        try:
            profile    = request.user.profile
            first_name = profile.first_name or request.user.first_name
            last_name  = profile.last_name  or request.user.last_name
        except Exception:
            first_name = request.user.first_name
            last_name  = request.user.last_name

        form = OrderCreateForm(initial={
            'first_name': first_name,
            'last_name':  last_name,
            'email':      request.user.email,
        })

    return render(request, 'orders/order_create.html', {
        'cart_items': cart_items,
        'cart_total': total,
        'form':       form,
    })


# ─── Admin ───────────────────────────────────────────────────────────────────

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
    weasyprint.HTML(string=html).write_pdf(response, stylesheets=[weasyprint.CSS('css/pdf.css')])
    return response


# ─── Payment ─────────────────────────────────────────────────────────────────

@login_required(login_url='account:login')
def order_pay(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if order.paid:
        return redirect('order:order_success', order_id=order.id)

    # Generate a fresh tx_ref every time
    order.chapa_tx_ref    = f"tx-{order.id}-{uuid.uuid4().hex[:12]}"
    order.payment_status  = 'pending'
    order.save(update_fields=['chapa_tx_ref', 'payment_status'])

    amount = round(float(order.get_total_cost()), 2)
    return_url = settings.CHAPA_RETURN_URL.format(order_id=order.id)
    
    data = {
        "amount":                     str(amount),
        "currency":                   "ETB",
        "email":                      order.email,
        "first_name":                 order.first_name,
        "last_name":                  order.last_name,
        "tx_ref":                     order.chapa_tx_ref,
        "callback_url":               settings.CHAPA_CALLBACK_URL,
        "return_url":                 return_url,
        "customization[title]":       "Care Coffee Shop",
        "customization[description]": f"Payment for Order #{order.id}",
    }
    headers = {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
        "Content-Type":  "application/json",
    }

    print(f"[order_pay] order={order.id} tx_ref={order.chapa_tx_ref} amount={amount}")
    print(f"[order_pay] return_url={return_url}")

    try:
        res = requests.post(
            "https://api.chapa.co/v1/transaction/initialize/",
            json=data, headers=headers, timeout=30,
        ).json()

        checkout_url = (res.get('data') or {}).get('checkout_url')
        if res.get('status') == 'success' and checkout_url:
            print(f"[order_pay] redirecting to Chapa: {checkout_url}")
            return redirect(checkout_url)

        print(f"[order_pay] Chapa init failed: {res.get('message')}")
        messages.error(request, res.get('message', 'Could not initialise payment.'))
        return redirect('order:order_create')

    except requests.Timeout:
        messages.error(request, "Payment gateway timed out. Please try again.")
        return redirect('order:order_pay', order_id=order.id)
    except Exception as e:
        logger.error(f"Chapa init error order {order.id}: {e}")
        messages.error(request, "Something went wrong. Please try again.")
        return redirect('order:order_create')


@login_required(login_url='account:login')
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Already confirmed paid — show receipt
    if order.paid:
        return render(request, 'orders/order_receipt.html', {
            'order': order, 'order_items': order.items.all(),
        })

    if not order.chapa_tx_ref:
        return redirect('shop:product-list')

    try:
        res = requests.get(
            f"https://api.chapa.co/v1/transaction/verify/{order.chapa_tx_ref}",
            headers={"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"},
            timeout=30,
        ).json()

        data_block = res.get('data') or {}
        status     = (data_block.get('status') or '').lower().strip()
        created_at = data_block.get('created_at', '')
        updated_at = data_block.get('updated_at', '')
        reference  = data_block.get('reference', '')
        method     = data_block.get('method', '')
        charge     = data_block.get('charge', 0)

        print(f"[order_success] ========================================")
        print(f"[order_success] order={order.id} tx_ref={order.chapa_tx_ref}")
        print(f"[order_success] status='{status}'")
        print(f"[order_success] created='{created_at}' updated='{updated_at}'")
        print(f"[order_success] reference='{reference}' method='{method}' charge={charge}")
        print(f"[order_success] full_data={data_block}")
        print(f"[order_success] ========================================")

        # Check if payment is successful
        # Multiple indicators of success:
        # 1. status == 'success' (obvious)
        # 2. created_at != updated_at (payment was processed)
        # 3. reference exists (Chapa assigned a reference)
        # 4. charge > 0 (Chapa charged a fee)
        # 5. method is 'test' (in test mode, this means payment went through)
        
        is_success = (
            status == 'success' or
            (created_at != updated_at and reference) or
            (charge and float(charge) > 0) or
            (method == 'test' and reference)
        )

        print(f"[order_success] is_success={is_success}")

        if is_success:
            print(f"[order_success] ✓ payment confirmed — marking as paid")
            order.paid           = True
            order.payment_status = 'paid'
            order.save(update_fields=['paid', 'payment_status'])
            
            # Clear cart only after successful payment
            cart = Cart(request)
            cart.clear()
            
            return render(request, 'orders/order_receipt.html', {
                'order': order, 'order_items': order.items.all(),
            })

        # Payment not successful - mark as cancelled but keep the order
        else:
            print(f"[order_success] ✗ payment not successful — marking as cancelled")
            order.payment_status = 'cancelled'
            order.save(update_fields=['payment_status'])
            messages.info(request, "Payment was not completed. Your order has been saved. You can try again from your order history.")
            return redirect('order:order_history')

    except requests.Timeout:
        print(f"[order_success] timeout — showing pending")
        return render(request, 'orders/order_receipt.html', {
            'order': order, 'order_items': order.items.all(),
            'payment_pending': True,
        })
    except Exception as e:
        logger.error(f"Chapa verify error order {order.id}: {e}")
        print(f"[order_success] exception: {e} — showing pending")
        return render(request, 'orders/order_receipt.html', {
            'order': order, 'order_items': order.items.all(),
            'payment_pending': True,
        })


@csrf_exempt
@require_http_methods(["POST"])
def chapa_callback(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    tx_ref = payload.get('tx_ref')
    if not tx_ref:
        return JsonResponse({"status": "error", "message": "tx_ref missing"}, status=400)

    try:
        order = Order.objects.get(chapa_tx_ref=tx_ref)
    except Order.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Order not found"}, status=404)

    try:
        res    = requests.get(
            f"https://api.chapa.co/v1/transaction/verify/{tx_ref}",
            headers={"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"},
            timeout=30,
        ).json()
        status = ((res.get('data') or {}).get('status') or '').lower()
        print(f"[webhook] order={order.id} status='{status}'")
        if status == 'success' and not order.paid:
            order.paid           = True
            order.payment_status = 'paid'
            order.save()
        return JsonResponse({"status": "success"}, status=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JsonResponse({"status": "error"}, status=500)


# ─── PDF Receipt ─────────────────────────────────────────────────────────────

@login_required(login_url='account:login')
def receipt_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html  = render_to_string('orders/order_receipt_pdf.html', {
        'order': order, 'order_items': order.items.all(),
    })
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=receipt_{order.id}.pdf'
    weasyprint.HTML(string=html).write_pdf(response, stylesheets=[weasyprint.CSS(string='''
        @page { size: A4; margin: 2cm; }
        body { font-family: Arial, sans-serif; font-size: 12px; }
        .receipt-header { text-align: center; margin-bottom: 2rem;
            border-bottom: 2px solid #d4a574; padding-bottom: 1rem; }
        .receipt-section { margin-bottom: 1.5rem; }
        .receipt-section h3 { color: #2c1810;
            border-bottom: 1px solid #e9ecef; padding-bottom: .5rem; }
        .info-item { display: flex; justify-content: space-between;
            padding: .5rem; background: #f8f9fa; margin-bottom: .5rem; }
        .items-table { width: 100%; border-collapse: collapse; }
        .items-table th, .items-table td {
            border: 1px solid #dee2e6; padding: .5rem; text-align: left; }
        .items-table th { background: #d4a574; color: white; }
        .summary-item { display: flex; justify-content: space-between;
            padding: .5rem; margin-bottom: .5rem; }
        .summary-item.total { font-weight: bold; font-size: 1.2rem;
            border-top: 2px solid #d4a574; padding-top: 1rem; }
    ''')])
    return response
