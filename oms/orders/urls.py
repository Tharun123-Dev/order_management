from django.urls import path
from . import views

urlpatterns = [

    #  CUSTOMER (ALL METHODS)
    path('customer/', views.customer_api),
    path('customer/<int:customer_id>/', views.customer_api),

    #  PRODUCT (ALL METHODS)
    path('product/', views.product_api),
    path('product/<int:product_id>/', views.product_api),

    #  CART
    path('cart/add/', views.add_to_cart),
    path('cart/<int:customer_id>/', views.view_cart),

    #  ORDER (ALL METHODS)
    path('order/', views.order_api),
    path('order/<int:customer_id>/', views.order_api),   # POST, GET
    path('order/update/<int:order_id>/', views.order_api),  # PUT, PATCH, DELETE

    #  DASHBOARD
    path('dashboard/', views.dashboard),

    #status
    path('order/status/<int:order_id>/', views.order_status),
]