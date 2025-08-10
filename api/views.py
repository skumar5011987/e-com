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
    )
from .models import User, Order, Product, Category


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