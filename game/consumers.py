from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from datetime import datetime, timedelta
import json
import asyncio
import random
import string

class OthelloConsumer(AsyncWebsocketConsumer):
    players = {}  # プレイヤーごとの色を管理
    disconnect_timers = {}
    
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"game_{self.room_name}"

        from .models import Othello
        self.othello_game, created = await sync_to_async(Othello.objects.get_or_create)(room_name=self.room_name)
        
        if created:
            await sync_to_async(self.othello_game.initialize_board)()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # プレイヤーの色を割り当て
        if len(self.players) == 0:
            self.players[self.channel_name] = "black"
            await sync_to_async(setattr)(self.othello_game, 'player_black', self.scope["user"])
            await sync_to_async(self.othello_game.save)()
        elif len(self.players) == 1:
            existing_color = list(self.players.values())[0]
            self.players[self.channel_name] = "white" if existing_color == "black" else "black"
            await sync_to_async(setattr)(self.othello_game, 'player_white', self.scope["user"])
            await sync_to_async(self.othello_game.save)()
        else:
            await self.close()
            return

        self.player_color = self.players[self.channel_name]

        if self.player_color in self.disconnect_timers:
            self.disconnect_timers[self.player_color].cancel()
            del self.disconnect_timers[self.player_color]

        await self.send(text_data=json.dumps({
            "type": "player_color",
            "player_color": self.player_color,
        }))

        # 初期ボード状態を送信
        othello_game = await sync_to_async(Othello.objects.select_related('player_black', 'player_white').get)(room_name=self.room_name)

        opponent_user = othello_game.player_white if self.player_color == "black" else othello_game.player_black

        opponent_info = {
            "username": opponent_user.username if opponent_user else None,
        }

        await self.send(text_data=json.dumps({
            "type": "update",
            "board": othello_game.board,
            "current_turn": othello_game.current_turn,
            "winner": othello_game.winner,
            "placeable_positions": othello_game.placeable_positions,
            "opponent": opponent_info
        }))

    async def disconnect(self, close_code):
        if self.channel_name in self.players:
            disconnected_color = self.players[self.channel_name]
            
            # 30秒のタイマーを設定
            import asyncio
            self.disconnect_timers[disconnected_color] = asyncio.create_task(self.handle_timeout(disconnected_color))
            
            del self.players[self.channel_name]
            
            # 他のプレイヤーに切断を通知
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "player_disconnected",
                    "message": f"{disconnected_color} player has disconnected. Game will end in 30 seconds if they don't return.",
                }
            )

            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


    async def handle_timeout(self, disconnected_color):
        # 30秒待機
        await asyncio.sleep(30)
        
        # タイムアウト後の処理
        from .models import Othello
        othello_game = await sync_to_async(Othello.objects.get)(room_name=self.room_name)
        
        # ゲームを終了状態に
        await sync_to_async(setattr)(othello_game, 'winner', 'white' if disconnected_color == 'black' else 'black')
        await sync_to_async(othello_game.save)()
        
        # 残りのプレイヤーに通知
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_ended",
                "message": f"Game ended due to {disconnected_color} player's inactivity",
                "winner": othello_game.winner
            }
        )


    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("type")

        if action == "place_disc":
            row = data.get("row")
            col = data.get("col")

            from .models import Othello
            othello_game = await sync_to_async(Othello.objects.select_related('player_black', 'player_white').get)(room_name=self.room_name)

            if self.player_color != othello_game.current_turn:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "It's not your turn!"
                }))
                return

            success_message = await sync_to_async(othello_game.place_disc)(row, col)

            opponent_user = othello_game.player_white if self.player_color == "black" else othello_game.player_black

            opponent_info = {
            "username": opponent_user.username if opponent_user else None,
            }


            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "update_board",
                    "board": othello_game.board,
                    "current_turn": othello_game.current_turn,
                    "winner": othello_game.winner,
                    "placeable_positions": othello_game.placeable_positions,
                    "opponent": opponent_info,
                }
            )

        elif action == "message_send":
            message = data.get("message")
            if message:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": message,
                        "username": self.scope["user"].username,
                        "player_color": self.player_color
                    }
                )


    async def update_board(self, event):
        await self.send(text_data=json.dumps({
            "type": "update",
            "board": event["board"],
            "current_turn": event["current_turn"],
            "winner": event["winner"],
            "placeable_positions": event["placeable_positions"],
            "opponent": event["opponent"],
        }))

    
    async def player_disconnected(self, event):
        await self.send(text_data=json.dumps({
            "type": "player_disconnected",
            "message": event["message"]
        }))


    async def game_ended(self, event):
        await self.send(text_data=json.dumps({
            "type": "game_ended",
            "message": event["message"],
            "winner": event["winner"]
        }))


    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": event["message"],
            "username": event["username"],
            "player_color": event["player_color"]
        }))

        
class MatchmakingConsumer(AsyncWebsocketConsumer):
    waiting_players = {}  # マッチング待機中のプレイヤーを管理
    
    async def connect(self):
        print("Connection attempt received") 
        await self.accept()
        print("Connection accepted")

    async def disconnect(self, close_code):
        if hasattr(self, 'user_id'):
            if self.user_id in self.waiting_players:
                del self.waiting_players[self.user_id]

    async def receive(self, text_data):
        print(f"Received message: {text_data}")
        data = json.loads(text_data)
        action = data.get("type")

        if action == "search_random_match":
            self.user_id = str(self.scope["user"].id)
            await self.add_to_waiting_players()
            asyncio.create_task(self.find_match())
            
        elif action == "cancel_match":
            if hasattr(self, 'user_id'):
                if self.user_id in self.waiting_players:
                    del self.waiting_players[self.user_id]
                await self.send(json.dumps({
                    "type": "match_cancelled"
                }))

    async def add_to_waiting_players(self):
        self.waiting_players[self.user_id] = {
            'user': self.scope["user"],
            'channel_name': self.channel_name,
            'timestamp': datetime.now().timestamp()
        }

    async def find_match(self):
        timeout = datetime.now() + timedelta(seconds=30)
        
        while datetime.now() < timeout:
            # 自分以外の待機プレイヤーを探す
            other_players = {
                user_id: data for user_id, data in self.waiting_players.items()
                if user_id != self.user_id
            }
            
            if other_players:
                # 最も長く待機しているプレイヤーとマッチング
                opponent_id, opponent_data = sorted(
                    other_players.items(),
                    key=lambda x: x[1]['timestamp']
                )[0]

                # 両プレイヤーを待機リストから削除
                if self.user_id in self.waiting_players:
                    del self.waiting_players[self.user_id]
                if opponent_id in self.waiting_players:
                    del self.waiting_players[opponent_id]

                chars = string.ascii_lowercase + string.digits
                length = 10

                # ランダムなroom_nameを生成
                room_name = ''.join(random.choice(chars) for _ in range(length))

                # マッチが成立したことを両プレイヤーに通知
                await self.send(json.dumps({
                    "type": "match_found",
                    "room_name": room_name,
                }))

                await self.channel_layer.send(
                    opponent_data['channel_name'],
                    {
                        "type": "send.match.found",
                        "room_name": room_name,
                    }
                )
                return
                
            await asyncio.sleep(1)
            
        # タイムアウト処理
        if self.user_id in self.waiting_players:
            del self.waiting_players[self.user_id]
        await self.send(json.dumps({
            "type": "match_timeout"
        }))

    async def send_match_found(self, event):
        await self.send(json.dumps({
            "type": "match_found",
            "room_name": event["room_name"],
        }))