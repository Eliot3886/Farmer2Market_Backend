from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Farmer', 'Farmer'),
        ('Buyer', 'Buyer'),
        ('Admin', 'Admin'),
    ]
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, unique=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Buyer')
    
    # Farmer specific fields
    farm_name = models.CharField(max_length=200, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    REQUIRED_FIELDS = ['full_name', 'phone_number', 'role']

    def __str__(self):
        return f"{self.username} ({self.role})"

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Vegetables', 'Vegetables'),
        ('Fruits', 'Fruits'),
        ('Grains', 'Grains'),
        ('Livestock', 'Livestock'),
        ('Dairy', 'Dairy'),
        ('Fodder', 'Fodder'),
        ('Others', 'Others'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Vegetables')
    price = models.CharField(max_length=50) # e.g., "$10 / kg"
    quantity = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    contact = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    views = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Conversation(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_conversations')
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farmer_conversations')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('buyer', 'farmer', 'product')

    def __str__(self):
        return f"Chat between {self.buyer.username} and {self.farmer.username} about {self.product.name}"

class Message(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    voice_note = models.FileField(upload_to='voice_notes/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}"
