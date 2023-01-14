from django.contrib import admin
from django.urls import path, include
from .views import item_list

app_name = 'core'

urlpatterns = [
    path('item_list/', item_list),
]