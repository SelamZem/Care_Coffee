from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('admin/order/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin/order/<int:order_id>/pdf/', views.admin_order_pdf, name='admin_order_pdf'),

    path('pay/<int:order_id>/', views.order_pay, name='order_pay'),
    path('chapa/callback/', views.chapa_callback, name='chapa_callback'),
    path('failed/', views.payment_failed, name='payment_failed'), 

]
