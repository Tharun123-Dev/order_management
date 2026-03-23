from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
from .serializers import *


# CUSTOMER API
@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def customer_api(request, customer_id=None):
    try:

        if request.method == "POST":
            serializer = CustomerSerializer(data=request.data)
            if serializer.is_valid():
                customer = serializer.save()
                Cart.objects.create(customer=customer)
                return Response({"message": "Customer created"})
            return Response(serializer.errors)

        if request.method == "GET" and customer_id is None:
            customers = Customer.objects.all()
            serializer = CustomerSerializer(customers, many=True)
            return Response(serializer.data)

        if request.method == "GET" and customer_id:
            customer = Customer.objects.get(id=customer_id)
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)

        if request.method in ["PUT", "PATCH"]:
            customer = Customer.objects.get(id=customer_id)
            serializer = CustomerSerializer(customer, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Customer updated"})
            return Response(serializer.errors)

        if request.method == "DELETE":
            customer = Customer.objects.get(id=customer_id)
            customer.delete()
            return Response({"message": "Customer deleted"})

    except Exception as e:
        return Response({"error": str(e)})


# PRODUCT API
@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def product_api(request, product_id=None):
    try:

        # CREATE PRODUCT
        if request.method == "POST":
            data = request.data
            stock = data.get("stock", 0)

            product = Product.objects.create(
                name=data["name"],
                price=data["price"],
                stock=stock,
                initial_stock=stock
            )

            return Response({
                "message": "Product created",
                "stock": product.stock
            })

        # GET ALL PRODUCTS
        if request.method == "GET" and product_id is None:
            products = Product.objects.all()
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)

        # GET SINGLE PRODUCT
        if request.method == "GET" and product_id:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"})

            serializer = ProductSerializer(product)
            return Response(serializer.data)

        # UPDATE PRODUCT (STOCK SAFE)
        if request.method in ["PUT", "PATCH"]:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"})

            data = request.data

            product.name = data.get("name", product.name)
            product.price = data.get("price", product.price)

            new_stock = data.get("stock")

            # STOCK UPDATE LOGIC
            if new_stock is not None:
                if new_stock < 0:
                    return Response({"error": "Stock cannot be negative"})

                diff = new_stock - product.stock
                product.stock = new_stock
                product.initial_stock += diff

            product.save()

            return Response({
                "message": "Product updated",
                "stock": product.stock
            })

        # DELETE PRODUCT
        if request.method == "DELETE":
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"})

            product.delete()
            return Response({"message": "Product deleted"})

    except Exception as e:
        return Response({"error": str(e)})
# CART
@api_view(['POST'])
def add_to_cart(request):
    try:
        data = request.data

        customer = Customer.objects.get(id=data["customer_id"])
        product = Product.objects.get(id=data["product_id"])
        quantity = data["quantity"]

        cart = Cart.objects.get(customer=customer)

        if product.stock < quantity:
            return Response({
                "error": f"{product.name} stock not available",
                "available_stock": product.stock,
                "requested_quantity": quantity,
                "status":"Cancelled"
            })

        existing = CartItem.objects.filter(cart=cart, product=product).first()

        if existing:
            existing.quantity += quantity
            existing.save()
        else:
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity
            )

        return Response({
            "message": f"{product.name} added to cart"
        })

    except Exception as e:
        return Response({"error": str(e)})


# VIEW CART
@api_view(['GET'])
def view_cart(request, customer_id):
    try:
        cart = Cart.objects.get(customer_id=customer_id)

        items = []
        total = 0

        for item in cart.items.all():
            amount = item.product.price * item.quantity
            total += amount

            items.append({
                "product": item.product.name,
                "quantity": item.quantity,
                "price": item.product.price,
                "amount": amount
            })

        return Response({
            "status": "PENDING",
            "items": items,
            "total_amount": total
        })

    except Exception as e:
        return Response({"error": str(e)})


# ORDER API
@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def order_api(request, customer_id=None, order_id=None):
    try:

        #  CREATE ORDER
        if request.method == "POST" and customer_id:
            customer = Customer.objects.get(id=customer_id)
            cart = Cart.objects.get(customer=customer)

            total = 0
            order = Order.objects.create(customer=customer, status='PENDING')

            for item in cart.items.all():
                if item.product.stock < item.quantity:
                    order.status = "CANCELLED"
                    order.save()

                    return Response({
                        "message": f"{item.product.name} out of stock",
                        "status": "CANCELLED"
                    })

            for item in cart.items.all():
                product = item.product

                product.stock -= item.quantity
                product.save()

                amount = product.price * item.quantity
                total += amount

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price
                )

            order.total_amount = total
            order.status = "COMPLETED"
            order.save()

            cart.items.all().delete()

            return Response({
                "message": "Order placed successfully",
                "status": order.status,
                "total": total
            })
        # GET ALL ORDERS (NEW API)
        if request.method == "GET" and customer_id is None and order_id is None:
          orders = Order.objects.all()
          serializer = OrderSerializer(orders, many=True)
          return Response(serializer.data)

        # GET ORDERS (Serializer Used)
        if request.method == "GET" and customer_id:
            orders = Order.objects.filter(customer_id=customer_id)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)

        # UPDATE ORDER (Serializer + Your Logic)
        if request.method in ["PUT", "PATCH"] and order_id:
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"})

            data = request.data
            new_status = data.get("status")
                # Prevent duplicate cancel (very important)
            if order.status == "CANCELLED":
               return Response({"error": "Order already cancelled"})
    # Restore stock ONLY when changing to CANCELLED
            if new_status == "CANCELLED":
               for item in order.items.all():
                 product = item.product
                 product.stock += item.quantity
                 product.save()

            #serializer update
            serializer = OrderSerializer(order, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Order updated"})
            return Response(serializer.errors)

        # DELETE ORDER (same logic + safe)
        if request.method == "DELETE" and order_id:
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"})

            for item in order.items.all():
                product = item.product
                product.stock += item.quantity
                product.save()

            order.delete()
            return Response({"message": "Order deleted"})

    except Exception as e:
        return Response({"error": str(e)})
# DASHBOARD
@api_view(['GET'])
def dashboard(request):
    try:
        total_customers = Customer.objects.count()
        total_orders = Order.objects.count()
        total_revenue = sum(order.total_amount for order in Order.objects.all())

        products = Product.objects.all()
        product_data = []

        for product in products:
            sold = sum(item.quantity for item in OrderItem.objects.filter(product=product))
            remaining = product.stock

            product_data.append({
                "product_name": product.name,
                "price": product.price,
                "initial_stock": product.initial_stock,
                "sold_quantity": sold,
                "remaining_stock": remaining,
                "low_stock": remaining < 5
            })

        return Response({
            "total_customers": total_customers,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "products": product_data
        })

    except Exception as e:
        return Response({"error": str(e)})
    
#status
@api_view(['GET'])
def order_status(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"})

    return Response({
        "order_id": order.id,
        "status": order.status
    })