from django.shortcuts import render
from .models import Order, OrderItem, Item, Slider
from .forms import PaymentForm, LoginForm, SignUpForm
from django.views.generic import View
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
# import message
from django.contrib import messages


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
                login(request, form.login(),
                      backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'You have successfully logged in')
                return redirect('core:home')
            return redirect('core:login')
        else:
            messages.error(request, 'Invalid credentials')
            raise ValidationError('Invalid form')
    form = LoginForm()
    return render(request=request, template_name='login.html', context={'form': form})


def checkout(request):
    if request.method == 'POST':
        print(request.POST)
        form = PaymentForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            messages.success(request, 'You have successfully ordered')
            return redirect('core:home')
        messages.error(request, 'Invalid credentials')
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
            user = form.save()
            if user:
                login(request, user,
                      backend='django.contrib.auth.backends.ModelBackend')

                messages.success(
                    request, 'You have successfully registered')
                return redirect('core:home')
            else:
                messages.error(request, 'Invalid credentials')
                print('User is None')
        else:
            print('Form is not valid')
            print(form.errors)
            messages.error(request, 'Invalid credentials')
            raise ValidationError('Invalid form')
    form = SignUpForm()
    return render(request=request, template_name='register.html', context={'form': form})


def home(request):
    context = {
        'sliders': Slider.objects.all()
    }
    return render(request=request, template_name='home_image_slider.html', context=context)


def add_new_address(request):
    return render(request=request, template_name='add_new_address.html')


def add_new_product(request):
    return render(request=request, template_name='add_new_product.html')


def change_password(request):
    return render(request=request, template_name='change_password.html')


def footer(request):
    return render(request=request, template_name='footer.html')


def navbar(request):
    return render(request=request, template_name='navbar.html')


def new_change_password(request):
    return render(request=request, template_name='new_change_password.html')


def product_main_page(request):
    return render(request=request, template_name='product_main_page.html')


def product_review_form(request):
    return render(request=request, template_name='product_review_form.html')


def product_search_page(request):
    return render(request=request, template_name='product_search_page.html')


def review_order(request):
    return render(request=request, template_name='review_order.html')


def scripts(request):
    return render(request=request, template_name='scripts.html')


def select_address(request):
    return render(request=request, template_name='select_address.html')


def select_payment_method(request):
    return render(request=request, template_name='select_payment_method.html')


def seller_account_intro(request):
    return render(request=request, template_name='seller_account_intro.html')


def seller_account_register(request):
    return render(request=request, template_name='seller_account_register.html')


def seller_profle(request):
    return render(request=request, template_name='seller_profle.html')


def seller_review_form(request):
    return render(request=request, template_name='seller_review_form.html')


def shopping_cart(request):
    return render(request=request, template_name='shopping_cart.html')


def template(request):
    return render(request=request, template_name='template.html')


def your_account(request):
    return render(request=request, template_name='your_account.html')


def your_addresses(request):
    return render(request=request, template_name='your_addresses.html')


def your_orders(request):
    return render(request=request, template_name='your_orders.html')


def your_seller_account(request):
    return render(request=request, template_name='your_seller_account.html')


def logout_view(request):
    logout(request)
    return redirect('core:home')
