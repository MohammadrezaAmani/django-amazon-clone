from django.shortcuts import render
from .models import Order, OrderItem, Item
from .forms import PaymentForm, LoginForm, SignUpForm
from django.views.generic import View
from django.shortcuts import redirect
from django.core.exceptions import ValidationError


def item_list(request):
    return render(request=request, template_name='base.html', context={'items': Item.objects.all()})


def order_list(request):
    return render(request=request, template_name='base.html', context={'orders': Order.objects.all()})


def login(request):
    if request.method == 'POST':
        # print(request.POST)
        form = LoginForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:checkout')
        else:
            raise ValidationError('Invalid form')
    form = LoginForm()
    return render(request=request, template_name='login.html', context={'form': form})


def register(request):
    return render(request=request, template_name='register.html', context={})


def checkout(request):
    if request.method == 'POST':
        print(request.POST)
        form = PaymentForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            return redirect('core:checkout')
        return redirect('core:checkout')

    form = PaymentForm()
    context = {
        'form': form,
    }
    return render(request=request, template_name='test.html', context=context)


def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:checkout')
        else:
            raise ValidationError('Invalid form')
    form = SignUpForm()
    return render(request=request, template_name='register.html', context={'form': form})
