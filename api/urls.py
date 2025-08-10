from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserRegisterView, UserLoginView, GetUpdateUserView, CategoryViewSet, ProductViewSet


router = DefaultRouter()
router.register(r"products", ProductViewSet)
router.register(r"category", CategoryViewSet)


urlpatterns = [
    
    path("auth/register/", UserRegisterView.as_view(), name="user register"),
    path("auth/login/", UserLoginView.as_view(), name="user login"),

    path("users/", GetUpdateUserView.as_view(), name="get or update user"),
] + router.urls