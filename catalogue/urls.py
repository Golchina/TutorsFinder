from django.urls import path
from .views import index, about, ad, create_ad, edit_ad, delete_ad, catalogue


urlpatterns = [
    path('', index, name='main'),
    path('about', about, name='about'),
    path('ad/create', create_ad, name='create_ad'),
    path('ad/<int:ad_id>/', ad, name='ad'),
    path('ad/edit/<int:ad_id>/', edit_ad, name='edit_ad'),
    path('ad/delete/<int:ad_id>/', delete_ad, name='delete_ad'),
    path('catalogue/', catalogue, name='catalogue')
]