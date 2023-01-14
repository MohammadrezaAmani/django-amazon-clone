from django.contrib import admin
from django.urls import path, include
from .views import item_list, loginDef, checkout, register, home
from django.conf import settings
from django.conf.urls.static import static
app_name = 'core'

urlpatterns = [
    path('item_list/', item_list, name='item_list'),
    path('login/', loginDef, name='login'),
    path('checkout/', checkout, name='checkout'),
    path('register/', register, name='register'),
    path('', home, name='home'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
