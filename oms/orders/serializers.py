from rest_framework import serializers
from .models import *

# CUSTOMER
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

    # Email unique validation
    def validate_email(self, value):
        if Customer.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    # Name + Email combination validation (optional)
    def validate(self, data):
        name = data.get("name")
        email = data.get("email")

        if Customer.objects.filter(name=name, email=email).exists():
            raise serializers.ValidationError("Customer already exists with same name and email")

        return data


# PRODUCT
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


# CART ITEM
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'quantity']


# ORDER ITEM
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'quantity', 'price']


# ORDER
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'