from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings


handler404 = "tutorsfinder.views.notfound"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('catalogue.urls'), name='home'),
    path('profile/', include('account.urls'), name='profile'),
    path('chats/', include('chat.urls')),
    path('select2/', include('django_select2.urls')),  # dropdown в создании объявления при выборе предметов
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
