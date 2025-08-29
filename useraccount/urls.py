from django.urls import path
from . import views

app_name="account"

urlpatterns = [
    path('register/', views.register_view, name="register"), 
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),

    path('edit_profile/', views.edit_profile, name="edit_profile"),
    



    path('request-password-reset/', views.request_password_reset, name='request-password-reset'),
    path('reset-password/<int:user_id>/', views.reset_password, name='reset-password'),
    path('update-password/', views.update_password, name="update-password"),


    path('profile/show/', views.show_profile, name='show_profile'),

]