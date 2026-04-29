from django.db import models
from django.db.models import Q
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, User, Message, Conversation
from .serializers import ProductSerializer, UserSerializer, RegisterSerializer, MessageSerializer, ConversationSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        phone = request.data.get('phone_number')
        new_username = request.data.get('new_username')
        new_password = request.data.get('new_password')
        user = User.objects.filter(phone_number=phone).first()
        if user:
            # Protect default admin account from being reset via public phone reset
            if user.username == '!admin' or user.role == 'Admin' or user.is_superuser:
                return Response({'error': 'Admin password can only be changed from the profile page.'}, status=status.HTTP_403_FORBIDDEN)
            
            if new_username:
                user.username = new_username
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password and username reset successful'})
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class ProfileView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.is_superuser or user.role == 'Admin':
            return Response({'error': 'Admin cannot be deleted'}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

class ClearDatabaseView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        # Keep the admin account if it exists, otherwise recreate it after clear
        User.objects.exclude(username='!admin').delete()
        Product.objects.all().delete()
        Message.objects.all().delete()
        Conversation.objects.all().delete()
        
        # Ensure !admin exists
        if not User.objects.filter(username='!admin').exists():
            admin = User.objects.create_superuser(
                username='!admin',
                password='!admin1234',
                full_name='System Admin',
                phone_number='0000000000',
                role='Admin'
            )
            admin.save()
            
        return Response({'message': 'System reset: Data deleted, Admin preserved.'})

# Products
class ProductListCreate(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Product.objects.all().order_by('-created_at')

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(location__icontains=search) | 
                Q(owner__farm_name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

# Messaging
class MessageListCreate(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Return in ascending order for chat flow (oldest first)
        return Message.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('timestamp')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method in ['DELETE', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_destroy(self, instance):
        if instance.owner == self.request.user or self.request.user.role == 'Admin' or self.request.user.is_superuser:
            instance.delete()
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to delete this product.")


class ProductIncrementView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, pk):
        product = Product.objects.filter(pk=pk).first()
        if product:
            product.views += 1
            product.save()
            return Response({'views': product.views})
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

class MessageCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return Response({'unread_count': count})

class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        total_farmers = User.objects.filter(role='Farmer').count()
        total_buyers = User.objects.filter(role='Buyer').count()
        total_products = Product.objects.all().count()
        
        users = User.objects.all().order_by('-date_joined')
        user_list = UserSerializer(users, many=True).data
        
        return Response({
            'stats': {
                'farmers': total_farmers,
                'buyers': total_buyers,
                'products': total_products
            },
            'users': user_list
        })

class AdminDeleteUserView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def delete(self, request, pk):
        user = User.objects.filter(pk=pk).first()
        if user:
            if user.is_superuser or user.role == 'Admin':
                return Response({'error': 'Cannot delete an admin account.'}, status=status.HTTP_403_FORBIDDEN)
            user.delete()
            return Response({'message': 'User deleted'})
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class MyProductList(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        owner_id = self.request.query_params.get('owner_id')
        if owner_id and (self.request.user.role == 'Admin' or self.request.user.is_superuser):
            return Product.objects.filter(owner_id=owner_id).order_by('-created_at')
        return Product.objects.filter(owner=self.request.user).order_by('-created_at')

class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(Q(buyer=user) | Q(farmer=user)).order_by('-updated_at')

class ConversationDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(Q(buyer=user) | Q(farmer=user))

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation_id')
        if conversation_id:
            return Message.objects.filter(conversation_id=conversation_id).order_by('timestamp')
        
        # Fallback for old messaging style
        receiver_id = self.request.query_params.get('receiver_id')
        product_id = self.request.query_params.get('product_id')
        user = self.request.user
        return Message.objects.filter(
            (Q(sender=user) & Q(receiver_id=receiver_id)) |
            (Q(sender_id=receiver_id) & Q(receiver=user)),
            product_id=product_id
        ).order_by('timestamp')

class MarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        Message.objects.filter(conversation_id=pk, receiver=request.user).update(is_read=True, status='read')
        return Response({'status': 'ok'})

class PingView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        # Ensure !admin exists
        if not User.objects.filter(username='!admin').exists():
            admin = User.objects.create_superuser(
                username='!admin',
                password='!admin1234',
                full_name='System Admin',
                phone_number='0000000000',
                role='Admin'
            )
            admin.save()
        return Response({'status': 'online', 'message': 'Pinger active and System Admin verified'})
