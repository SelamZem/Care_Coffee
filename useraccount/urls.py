from django.urls import path
from . import views

app_name="account"

urlpatterns = [
    path('register/', views.register_view, name="register"), 
    path('login/', views.login_view, name="login"),
    path('edit_profile/', views.edit_profile, name="edit_profile"),
    path('profile/', views.profile_detail, name='profile_detail'),
    path('home', views.home_view, name='home'),


    path('request-password-reset/', views.request_password_reset, name='request-password-reset'),
    path('reset-password/<int:user_id>/', views.reset_password, name='reset-password'),
    path('update-password/', views.update_password, name="update-password"),

]