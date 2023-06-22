from django.urls import path
from django.contrib.auth import views as auth_views

from .views import *

urlpatterns = [
    path('<int:user_id>', profile, name='profile'),
    path('edit/', edit_profile, name='edit'),
    path('edit/change_password', change_password, name='change_password'),
    path('login/', log_in, name='login'),
    path('logout/', log_out, name='logout'),
    path('register/', register, name='register'),
    path('reset-password/', auth_views.PasswordResetView.as_view(template_name='account/password_reset.html'),
         name="reset_password"),
    path('reset-password-sent/', auth_views.PasswordResetDoneView.as_view(template_name='account/reset_done.html'),
         name="password_reset_done"),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='account/reset_new_password.html'),
         name="password_reset_confirm"),
    path('reset-password-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='account/reset_complete.html'),
         name="password_reset_complete"),
]