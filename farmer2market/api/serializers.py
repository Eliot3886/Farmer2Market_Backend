from rest_framework import serializers
from .models import User, Product, Message, Conversation

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'phone_number', 'location', 'role', 
                  'farm_name', 'profile_picture', 'email', 'date_joined']

class ConversationSerializer(serializers.ModelSerializer):
    buyer_details = UserSerializer(source='buyer', read_only=True)
    farmer_details = UserSerializer(source='farmer', read_only=True)
    product_details = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = '__all__'

    def get_product_details(self, obj):
        from .serializers import ProductSerializer
        return ProductSerializer(obj.product).data

    def get_last_message(self, obj):
        msg = obj.messages.all().order_by('-timestamp').first()
        if msg:
            return MessageSerializer(msg).data
        return None

    def get_unread_count(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user:
            return obj.messages.filter(receiver=user, is_read=False).count()
        return 0

class MessageSerializer(serializers.ModelSerializer):
    sender_details = UserSerializer(source='sender', read_only=True)
    receiver_details = UserSerializer(source='receiver', read_only=True)
    class Meta:
        model = Message
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'full_name', 'phone_number', 
                  'location', 'role', 'farm_name', 'email']

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
            
        role = attrs.get('role')
        if role == 'Farmer':
            if User.objects.filter(role='Farmer').count() >= 10:
                raise serializers.ValidationError("Maximum number of farmers (10) reached.")
        elif role == 'Buyer':
            if User.objects.filter(role='Farmer').count() == 0:
                raise serializers.ValidationError("No farmers registered yet. Buyers cannot register.")
            if User.objects.filter(role='Buyer').count() >= 10:
                raise serializers.ValidationError("Maximum number of buyers (10) reached.")
                
        phone_number = attrs.get('phone_number')
        if phone_number and len(phone_number) != 10:
            raise serializers.ValidationError({"phone_number": "Phone number must be 10 digits."})
            
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user

class ProductSerializer(serializers.ModelSerializer):
    owner_details = UserSerializer(source='owner', read_only=True)
    class Meta:
        model = Product
        fields = '__all__'