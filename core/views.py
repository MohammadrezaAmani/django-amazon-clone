from django.shortcuts import render
from .models import Order, OrderItem, Item
# Create your views here.

def item_list(request):
    return render(request=request, template_name='base.html',context={'items':Item.objects.all()})
