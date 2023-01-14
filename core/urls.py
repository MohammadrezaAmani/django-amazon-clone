from django.contrib import admin
from django.urls import path, include
from .views import item_list, loginDef, checkout, register

app_name = 'core'

urlpatterns = [
    path('item_list/', item_list, name='item_list'),
    path('login/', loginDef, name='login'),
    path('checkout/', checkout, name='checkout'),
    path('register/', register, name='register'),
]
