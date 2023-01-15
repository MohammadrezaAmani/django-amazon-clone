from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    home,
    add_new_address,
    add_new_product,
    change_password,
    footer,
    navbar,
    new_change_password,
    product_main_page,
    product_review_form,
    product_search_page,
    review_order,
    scripts,
    select_address,
    select_payment_method,
    seller_account_intro,
    seller_account_register,
    seller_profle,
    seller_review_form,
    shopping_cart,
    template,
    your_account,
    your_addresses,
    your_orders,
    your_seller_account,
    logout_view,
    item_list,
    loginDef,
    checkout,
    register,
)


app_name = 'core'


urlpatterns = [
    path('item_list/', item_list, name='item_list'),
    path('login/', loginDef, name='login'),
    path('checkout/', checkout, name='checkout'),
    path('register/', register, name='register'),
    path('', home, name='home'),
    path('add_new_address/', add_new_address, name='add_new_address'),
    path('add_new_product/', add_new_product, name='add_new_product'),
    path('change_password/', change_password, name='change_password'),
    path('footer/', footer, name='footer'),
    path('navbar/', navbar, name='navbar'),
    path('new_change_password/', new_change_password, name='new_change_password'),
    path('product_main_page/', product_main_page, name='product_main_page'),
    path('product_review_form/', product_review_form, name='product_review_form'),
    path('product_search_page/', product_search_page, name='product_search_page'),
    path('review_order/', review_order, name='review_order'),
    path('scripts/', scripts, name='scripts'),
    path('select_address/', select_address, name='select_address'),
    path('select_payment_method/', select_payment_method,
         name='select_payment_method'),
    path('seller_account_intro/', seller_account_intro,
         name='seller_account_intro'),
    path('seller_account_register/', seller_account_register,
         name='seller_account_register'),
    path('seller_profle/', seller_profle, name='seller_profle'),
    path('seller_review_form/', seller_review_form, name='seller_review_form'),
    path('shopping_cart/', shopping_cart, name='shopping_cart'),
    path('template/', template, name='template'),
    path('your_account/', your_account, name='your_account'),
    path('your_addresses/', your_addresses, name='your_addresses'),
    path('your_orders/', your_orders, name='your_orders'),
    path('your_seller_account/', your_seller_account, name='your_seller_account'),
    path('logout/', logout_view, name='logout'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
