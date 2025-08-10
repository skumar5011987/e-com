from rest_framework import generics, views, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import ( 
    UserSerializer,
    UserRegisterSerializer, 
    UserLoginSerializer, 
    UserUpdateSerializer,
    CategorySerializer,
    ProductSerializer,
    OrderSerializer,
    UserCartSerializer,
    )
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Case, F, Sum, PositiveIntegerField, When
from .models import User, Cart, Order, Product, Category, CartItem, OrderItem



class UserRegisterView(generics.CreateAPIView):
    users = User.objects.all()
    serializer_class = UserRegisterSerializer

class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user=user)
        r_token = str(refresh)
        access = str(refresh.access_token)

        return Response({
            "refresh": r_token,
            "access": access,
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)

class GetUpdateUserView(generics.RetrieveUpdateAPIView):
    
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated,]

    def get_object(self):
        return self.request.user

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

class UserCartView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserCartSerializer

    
    def get(self, request):
        """List items in the user's cart."""
        cart = request.user.cart
        serializer = UserCartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response(self.get_serializer(cart_item).data, status=status.HTTP_201_CREATED)
    
    def delete(self, request):
        product_id = request.data.get("product_id")
        cart_item = get_object_or_404(CartItem, cart=self.request.user.cart, product_id=product_id)
        cart_item.delete()
        return Response({"detail": "Item removed from cart"}, status=status.HTTP_204_NO_CONTENT)

class UserOrderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        cart_items = Cart.objects.select_related("product").filter(user=request.user).select_for_update()

        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Build product_id → (product, quantity) mapping
        product_map = {item.product.id: item for item in cart_items}

        # Stock check
        for p in product_map.values():
            if p.product.stock < p.quantity:
                return Response(
                    {"error": f"Insufficient stock for product {p.product.name}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Calculate total price
        total_price = Sum(p.product.price * p.quantity for p in product_map.values())
        order = Order.objects.create(user=request.user, total_price=total_price)
        
        # Create order items in one query
        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product=p.product,
                quantity=p.quantity,
                price=p.product.price
            )
            for p in product_map.values()
        ])

        # Bulk stock update in one query
        Product.objects.filter(id__in=product_map.keys()).update(
            stock=Case(
                *[
                    When(id=pid, then=F('stock') - item.quantity)
                    for pid, item in product_map.items()
                ],
                output_field=PositiveIntegerField()
            )
        )

        # Clear User cart
        cart_items.delete()

        return Response({"message": "Order placed successfully", "order_id": str(order.order_id)})
