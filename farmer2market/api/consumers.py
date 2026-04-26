import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Conversation, User, Product
from .serializers import MessageSerializer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'chat_message')

        if message_type == 'chat_message':
            message = data['message']
            sender_id = data['sender_id']
            receiver_id = data['receiver_id']
            product_id = data['product_id']
            conversation_id = data.get('conversation_id')

            # Save message to DB
            saved_msg = await self.save_message(sender_id, receiver_id, product_id, message, conversation_id)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': saved_msg
                }
            )
        elif message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'sender_id': data['sender_id'],
                    'is_typing': data['is_typing']
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender_id': event['sender_id'],
            'is_typing': event['is_typing']
        }))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, product_id, text, conversation_id=None):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        product = Product.objects.get(id=product_id)
        
        if not conversation_id:
            # Find or create conversation
            # For simplicity, we define conversation by (buyer, farmer, product)
            # We need to determine who is buyer and who is farmer
            buyer = sender if sender.role == 'Buyer' else receiver
            farmer = receiver if sender.role == 'Buyer' else sender
            
            conversation, _ = Conversation.objects.get_or_create(
                buyer=buyer,
                farmer=farmer,
                product=product
            )
        else:
            conversation = Conversation.objects.get(id=conversation_id)

        msg = Message.objects.create(
            conversation=conversation,
            sender=sender,
            receiver=receiver,
            product=product,
            text=text
        )
        return MessageSerializer(msg).data
