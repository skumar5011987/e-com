
from rest_framework import serializers
from .models import User, Product, Order, Category, Cart, CartItem
from django.contrib.auth import authenticate

class CartItemSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "total_price"]

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity

class UserCartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(source="items", many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "cart_items", "total_price"]
    
    def get_total_price(self, obj):
        return sum(
            item.product.price * item.quantity
            for item in obj.items.all()
        )

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "is_active", "phone")

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password", "phone", "is_active")
        extra_kwargs = {
            'password': {'write_only': True} 
        }
     
    def create(self, validated_data):

        if User.objects.filter(email=validated_data["email"]).exists():
            raise serializers.ValidationError({"email": "User with this email already exists."})

        user = User.objects.create_user(
            first_name = validated_data.get("first_name",""),
            last_name = validated_data.get("last_name",""),
            phone = validated_data.get("phone"),
            username=validated_data["email"],
            password=validated_data["password"],
            email = validated_data["email"],
            is_active = validated_data.get("is_active", True)
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        username = data.get('email')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled.")
                data['user'] = user  # Add user to validated data
            else:
                raise serializers.ValidationError("Invalid credentials.")
        else:
            raise serializers.ValidationError("Must include both email and password.")

        return data

class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "phone", "is_active")
        extra_kwargs = {
            "email":{"required":True}
        }

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

class OrderSerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(many=True, queryset=Product.objects.all())
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = (
            "order_id",
            "total_price",
            "status",
            "user",
            "products"
        )