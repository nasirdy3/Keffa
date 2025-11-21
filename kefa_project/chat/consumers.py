import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user', AnonymousUser())
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        try:
            player = await self.get_player_profile(self.user)
            self.username = player.full_name
            self.team_name = player.team.team_name if hasattr(player, 'team') else 'No Team'
        except Exception:
            await self.close()
            return
        
        self.room_group_name = 'community_chat'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '').strip()
        
        if not message:
            return
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': self.username,
                'team_name': self.team_name
            }
        )
    
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        team_name = event.get('team_name', '')
        
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'team_name': team_name
        }))
    
    @database_sync_to_async
    def get_player_profile(self, user):
        return user.player_profile
