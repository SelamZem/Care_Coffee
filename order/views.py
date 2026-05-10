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
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem


logger = logging.getLogger(__name__)


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
        initial_data = {
            'first_name': request.user.profile.first_name,
            'last_name': request.user.profile.last_name,
            'email': request.user.email,
        }
        form = OrderCreateForm(initial=initial_data)

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

    # Generate transaction reference if missing
    if not order.chapa_tx_ref:
        order.chapa_tx_ref = f"tx-{order.id}-{uuid.uuid4().hex[:10]}"
        order.save(update_fields=['chapa_tx_ref'])

    callback_url = settings.CHAPA_CALLBACK_URL
    return_url = settings.CHAPA_RETURN_URL.format(order_id=order_id)
    failure_url = settings.CHAPA_FAILURE_RETURN_URL.format(order_id=order_id)
    
    print(f"Chapa return URL: {return_url}")
    print(f"Chapa failure URL: {failure_url}")
    print(f"Chapa callback URL: {callback_url}")

    data = {
        "amount": str(float(order.get_total_cost())),
        "currency": "ETB",
        "email": order.email,
        "first_name": order.first_name,
        "last_name": order.last_name,
        "tx_ref": order.chapa_tx_ref,
        "callback_url": callback_url,
        "return_url": return_url,
        "customization[title]": "Care Coffee Shop",
        "customization[description]": f"Payment for Order #{order.id}",
        "customization[logo]": f"{settings.BASE_URL}/static/logos/logo.jpg"
    }

    headers = {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(
            "https://api.chapa.co/v1/transaction/initialize/",
            json=data,
            headers=headers,
            timeout=15
        ).json()

        checkout_url = res.get('data', {}).get('checkout_url')
        if res.get('status') == 'success' and checkout_url:
            return redirect(checkout_url)
        else:
            # Log the error response from Chapa
            print(f"Chapa error: {res}")
            messages.error(request, f"Payment failed: {res.get('message', 'Unknown error')}")

    except requests.RequestException as e:
        print(f"Payment request error: {e}")
        messages.error(request, "Network error. Please check your connection and try again.")
    except Exception as e:
        print(f"Payment initialization error: {e}")
        messages.error(request, "Payment initialization failed. Please try again.")

    return redirect('order:payment_failed', order_id=order.id)


@csrf_exempt
@require_http_methods(["POST"])
def chapa_callback(request):
    try:
 
        payload = json.loads(request.body)
        print("Webhook payload received:", payload)
    except json.JSONDecodeError as e:
        print("Invalid JSON:", e)
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    tx_ref = payload.get('tx_ref')
    if not tx_ref:
        print("Transaction reference missing in payload")
        return JsonResponse({"status": "error", "message": "Transaction reference missing"}, status=400)

    print("Processing transaction:", tx_ref)

    try:
        order = Order.objects.get(chapa_tx_ref=tx_ref)
        print(f"Found order: {order.id}, paid status: {order.paid}")
    except Order.DoesNotExist:
        print(f"Order not found for tx_ref: {tx_ref}")
        return JsonResponse({"status": "error", "message": "Order not found"}, status=404)

    headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
    try:
        response = requests.get(
            f"https://api.chapa.co/v1/transaction/verify/{tx_ref}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        verification_data = response.json()
        print("Chapa verification response:", verification_data)
    except requests.RequestException as e:
        print("Error verifying payment with Chapa:", e)
        return JsonResponse({"status": "error", "message": "Payment verification failed"}, status=500)

    # Check for success - Chapa can return different status values
    top_status = verification_data.get('status')
    data_status = verification_data.get('data', {}).get('status') if verification_data.get('data') else None
    
    print(f"Verification status - top: {top_status}, data: {data_status}")
    
    if top_status == 'success' and data_status in ['success', 'completed', 'paid']:
        if not order.paid:
            order.paid = True
            order.payment_status = 'paid'
            order.save()
            print(f"Order {order.id} marked as paid via webhook")
        return JsonResponse({"status": "success", "message": "Payment verified"}, status=200)
    
    # Payment failed/cancelled - update status
    elif data_status in ['failed', 'cancelled', 'declined']:
        order.payment_status = data_status
        order.save()
        print(f"Order {order.id} marked as {data_status} via webhook")
        return JsonResponse({"status": "success", "message": f"Payment {data_status} recorded"}, status=200)

    print(f"Payment verification failed for order {order.id}. Status: {data_status}")
    return JsonResponse({"status": "error", "message": "Payment verification failed"}, status=400)

@login_required(login_url='account:login')
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # If already paid, show receipt
    if order.paid:
        chapa_receipt = f"https://checkout.chapa.co/receipt/{order.chapa_tx_ref}"
        return render(request, 'orders/order_receipt.html', {
            'order': order,
            'chapa_receipt': chapa_receipt,
            'order_items': order.items.all()
        })
    
    # Check if payment failed/cancelled via webhook
    if order.payment_status in ['failed', 'cancelled']:
        return render(request, 'orders/order_receipt.html', {
            'order': order,
            'payment_failed': True,
            'failure_reason': order.payment_status,
            'order_items': order.items.all()
        })
    
    # Verify payment with Chapa
    if order.chapa_tx_ref:
        headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
        try:
            response = requests.get(
                f"https://api.chapa.co/v1/transaction/verify/{order.chapa_tx_ref}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            verification_data = response.json()
            
            print(f"=== CHAPA VERIFY RESPONSE ===")
            print(f"Response data: {verification_data}")
            
            # Check Chapa response status
            chapa_status = verification_data.get('data', {}).get('status') if verification_data.get('data') else None
            
            print(f"Chapa status: {chapa_status}")
            print(f"=== END RESPONSE ===")
            
            # SUCCESS - payment completed
            if chapa_status in ['success', 'completed', 'paid']:
                order.paid = True
                order.payment_status = 'paid'
                order.save()
                chapa_receipt = f"https://checkout.chapa.co/receipt/{order.chapa_tx_ref}"
                return render(request, 'orders/order_receipt.html', {
                    'order': order,
                    'chapa_receipt': chapa_receipt,
                    'order_items': order.items.all()
                })
            
            # FAILURE - payment failed/cancelled
            elif chapa_status in ['failed', 'cancelled', 'declined']:
                order.payment_status = chapa_status
                order.save()
                return render(request, 'orders/order_receipt.html', {
                    'order': order,
                    'payment_failed': True,
                    'failure_reason': chapa_status,
                    'order_items': order.items.all()
                })
            
            # Unknown status - check again later
            else:
                return render(request, 'orders/order_receipt.html', {
                    'order': order,
                    'payment_pending': True,
                    'order_items': order.items.all()
                })
                
        except Exception:
            # Error verifying
            return render(request, 'orders/order_receipt.html', {
                'order': order,
                'payment_failed': True,
                'failure_reason': 'error',
                'order_items': order.items.all()
            })
    
    # No transaction reference - payment was not attempted
    return render(request, 'orders/order_receipt.html', {
        'order': order,
        'payment_failed': True,
        'failure_reason': 'not_attempted',
        'order_items': order.items.all()
    })

@login_required(login_url='account:login')
def receipt_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order_receipt_pdf.html', {
        'order': order,
        'order_items': order.items.all()
    })
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=receipt_{order.id}.pdf'
    weasyprint.HTML(string=html).write_pdf(
        response,
        stylesheets=[weasyprint.CSS(string='''
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
            }
            .receipt-header {
                text-align: center;
                margin-bottom: 2rem;
                border-bottom: 2px solid #d4a574;
                padding-bottom: 1rem;
            }
            .receipt-section {
                margin-bottom: 1.5rem;
            }
            .receipt-section h3 {
                color: #2c1810;
                border-bottom: 1px solid #e9ecef;
                padding-bottom: 0.5rem;
            }
            .info-item {
                display: flex;
                justify-content: space-between;
                padding: 0.5rem;
                background: #f8f9fa;
                margin-bottom: 0.5rem;
            }
            .items-table {
                width: 100%;
                border-collapse: collapse;
            }
            .items-table th, .items-table td {
                border: 1px solid #dee2e6;
                padding: 0.5rem;
                text-align: left;
            }
            .items-table th {
                background: #d4a574;
                color: white;
            }
            .summary-item {
                display: flex;
                justify-content: space-between;
                padding: 0.5rem;
                margin-bottom: 0.5rem;
            }
            .summary-item.total {
                font-weight: bold;
                font-size: 1.2rem;
                border-top: 2px solid #d4a574;
                padding-top: 1rem;
            }
        ''')]
    )
    return response

