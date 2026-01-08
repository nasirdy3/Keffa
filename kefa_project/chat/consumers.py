import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from kefa_project.matches.models import FriendlyMatch

# --- Volatile In-Memory Locking (Single Instance) ---
# This set acts as a mutex for friendly match IDs currently being processed
# to prevent race conditions where two users click "Accept" simultaneously.
MATCH_LOCKS = set()

# --- Content Governance Service ---
class ModerationService:
    # Basic list of regex patterns for moderation
    # In production, these should be loaded from a more extensive library or DB
    BLOCKED_PATTERNS = [
        r'(?i)(fuck|shit|bitch|bastard|dick|pussy|whore|cunt|asshole)', # Profanity
        r'(?i)(nigger|faggot|retard|spic|chink|kike)', # Hate Speech
        r'(?i)(kill yourself|kys|suicide)', # Violence/Self-harm
        r'(?i)(sex|nude|porn)', # Explicit
    ]

    @classmethod
    def filter_message(cls, message):
        """
        Returns (is_allowed, processed_message, error_msg)
        """
        if not message:
            return False, "", "Empty message"
            
        # Check for hate speech/abuse (Strict Block)
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, message):
                return False, message, "Message blocked: Content violates KEFA community guidelines."
        
        return True, message, None

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user', AnonymousUser())
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        try:
            # Cache player identity in the socket instance
            player = await self.get_player_profile(self.user)
            self.username = player.full_name
            self.user_id = self.user.id
            self.team_name = player.team.team_name if hasattr(player, 'team') else 'No Team'
            self.team_id = player.team.id if hasattr(player, 'team') else None
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
        """
        Routes incoming JSON payloads to specific handlers based on 'type'
        """
        try:
            data = json.loads(text_data)
            msg_type = data.get('type', 'chat_message')
            
            if msg_type == 'chat_message':
                await self.handle_chat_message(data)
            elif msg_type == 'announce_match':
                await self.handle_announce_match(data)
            elif msg_type == 'claim_match':
                await self.handle_claim_match(data)
                
        except json.JSONDecodeError:
            pass
        except Exception as e:
            # Log error internally, don't crash connection
            print(f"WS Error: {e}")

    # --- Handlers ---

    async def handle_chat_message(self, data):
        message_content = data.get('message', '').strip()
        
        # 1. Content Governance
        is_allowed, _, error_msg = ModerationService.filter_message(message_content)
        
        if not is_allowed:
            # Send warning ONLY to the sender
            await self.send(text_data=json.dumps({
                'type': 'system_warning',
                'message': error_msg
            }))
            return

        # 2. Broadcast Valid Message
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_broadcast',
                'message': message_content,
                'username': self.username,
                'team_name': self.team_name,
                'user_id': self.user_id
            }
        )

    async def handle_announce_match(self, data):
        """
        Triggered when a user creates a friendly. 
        Broadcasts a card with HIDDEN code.
        """
        match_id = data.get('match_id')
        if not match_id:
            return

        match_data = await self.get_match_data(match_id)
        if not match_data:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'match_announcement_broadcast',
                'match_id': match_id,
                'creator_team': match_data['creator_team'],
                'creator_id': match_data['creator_id']
            }
        )

    async def handle_claim_match(self, data):
        """
        Atomic Logic:
        1. Check memory lock.
        2. If locked, reject.
        3. If free, lock it -> Update DB -> Broadcast "Taken" -> Reveal code to participants.
        """
        match_id = data.get('match_id')
        if not match_id or not self.team_id:
            return

        # 1. Check Global Memory Lock
        if match_id in MATCH_LOCKS:
            await self.send_error("This match is currently being processed by another user.")
            return

        MATCH_LOCKS.add(match_id)
        
        try:
            # 2. Attempt DB Claim
            result = await self.claim_friendly_match_db(match_id, self.team_id)
            
            if result['success']:
                # 3. Broadcast to EVERYONE that match is taken (Updates UI, removes button)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'match_taken_broadcast',
                        'match_id': match_id,
                        'opponent_team': self.team_name
                    }
                )
                
                # 4. Reveal Code (Only to Challenger) - The sender
                await self.send(text_data=json.dumps({
                    'type': 'match_details',
                    'match_id': match_id,
                    'game_code': result['game_code'],
                    'is_creator': False
                }))
                
                # Note: The Creator won't get the code via WS automatically unless we identify them 
                # in the group_send, but for simplicity, the Creator usually already knows the code
                # or can refresh their dashboard. 
                # Optimization: We could send a specific message if we tracked channel_names by user_id.
                
            else:
                await self.send_error(result['error'])
                
        finally:
            # Release lock immediately after processing
            if match_id in MATCH_LOCKS:
                MATCH_LOCKS.remove(match_id)

    # --- Channel Layer Event Receivers ---

    async def chat_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'team_name': event['team_name'],
            'is_me': event['user_id'] == self.user_id
        }))

    async def match_announcement_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'challenge_announcement',
            'match_id': event['match_id'],
            'creator_team': event['creator_team'],
            'is_creator': event['creator_id'] == self.user_id
        }))

    async def match_taken_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'challenge_taken',
            'match_id': event['match_id'],
            'opponent_team': event['opponent_team']
        }))

    # --- Helpers ---

    async def send_error(self, message):
        await self.send(text_data=json.dumps({
            'type': 'system_error',
            'message': message
        }))

    @database_sync_to_async
    def get_player_profile(self, user):
        return user.player_profile

    @database_sync_to_async
    def get_match_data(self, match_id):
        try:
            match = FriendlyMatch.objects.get(id=match_id)
            return {
                'creator_team': match.created_by_team.team_name,
                'creator_id': match.created_by_team.player_set.first().user.id, # Assumes 1 player per team for this logic
                'status': match.status
            }
        except FriendlyMatch.DoesNotExist:
            return None

    @database_sync_to_async
    def claim_friendly_match_db(self, match_id, team_id):
        try:
            match = FriendlyMatch.objects.get(id=match_id)
            
            # DB Double Check (in case lock failed or server restarted)
            if match.status != 'open':
                return {'success': False, 'error': 'Match already taken or cancelled.'}
            
            if match.created_by_team.id == team_id:
                return {'success': False, 'error': 'You cannot accept your own match.'}

            # Update Match
            from kefa_project.teams.models import Team
            opponent = Team.objects.get(id=team_id)
            
            match.opponent_team = opponent
            match.status = 'accepted'
            match.accepted_at = timezone.now()
            match.save()
            
            return {'success': True, 'game_code': match.game_code}
            
        except FriendlyMatch.DoesNotExist:
            return {'success': False, 'error': 'Match not found.'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

