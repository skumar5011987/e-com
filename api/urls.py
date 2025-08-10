from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegisterView, 
    UserLoginView, 
    GetUpdateUserView, 
    CategoryViewSet, 
    ProductViewSet,
    UserCartView,
)


router = DefaultRouter()
router.register(r"products", ProductViewSet)
router.register(r"category", CategoryViewSet)


urlpatterns = [
    
    path("auth/register/", UserRegisterView.as_view(), name="user_register"),
    path("auth/login/", UserLoginView.as_view(), name="user_login"),
    path("users/", GetUpdateUserView.as_view(), name="get_or_update_user"),
    path("cart/", UserCartView.as_view(), name="user_cart"),
] + router.urls