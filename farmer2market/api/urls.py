from django.urls import path
from .views import (
    ProductListCreate, ProductDetail, RegisterView,
    MyTokenObtainPairView, ProfileView, PasswordResetView,
    MessageListCreate, MessageCountView, ClearDatabaseView,
    ProductIncrementView, AdminDashboardView, AdminDeleteUserView, MyProductList,
    ConversationListView, MessageListView, MarkReadView, ConversationDetailView, PingView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', MyTokenObtainPairView.as_view()),
    path('reset-password/', PasswordResetView.as_view()),
    path('refresh/', TokenRefreshView.as_view()),
    path('profile/', ProfileView.as_view()),
    path('products/', ProductListCreate.as_view()),
    path('products/<int:pk>/', ProductDetail.as_view()),
    path('messages/', MessageListCreate.as_view()),
    path('messages/count/', MessageCountView.as_view()),
    path('products/<int:pk>/view/', ProductIncrementView.as_view()),
    path('admin/dashboard/', AdminDashboardView.as_view()),
    path('admin/users/<int:pk>/', AdminDeleteUserView.as_view()),
    path('clear-db/', ClearDatabaseView.as_view()),
    path('products/my/', MyProductList.as_view()),
    path('conversations/', ConversationListView.as_view()),
    path('messages/history/', MessageListView.as_view()),
    path('conversations/<int:pk>/read/', MarkReadView.as_view()),
    path('conversations/<int:pk>/', ConversationDetailView.as_view()),
    path('ping/', PingView.as_view(), name='ping'),
]
