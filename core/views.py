from django.shortcuts import render
from .models import Order, OrderItem, Item
from .forms import PaymentForm, LoginForm, SignUpForm
from django.views.generic import View
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout


def item_list(request):
    return render(request=request, template_name='base.html', context={'items': Item.objects.all()})


def order_list(request):
    return render(request=request, template_name='base.html', context={'orders': Order.objects.all()})


def loginDef(request):
    if request.method == 'POST':
        # print(request.POST)
        form = LoginForm(request.POST)
        if form.is_valid():
            form.save()
            if form.login() is not None:
                login(request, form.login())
                return redirect('core:checkout')
            return redirect('core:checkout')
        else:
            raise ValidationError('Invalid form')
    form = LoginForm()
    return render(request=request, template_name='login.html', context={'form': form})


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
            user = authenticate(
                email=form.cleaned_data['email'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                return redirect('core:checkout')
            else:
                print('User is None')
        else:
            raise ValidationError('Invalid form')
    form = SignUpForm()
    return render(request=request, template_name='register.html', context={'form': form})
