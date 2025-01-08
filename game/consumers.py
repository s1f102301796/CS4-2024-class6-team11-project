from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json

class OthelloConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"game_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        print(f"WebSocket connected to room: {self.room_name}")

        # 接続時にボードの初期状態を送信
        from .models import Othello
        othello_game = await sync_to_async(Othello.objects.get)()

        await self.send(text_data=json.dumps({
            "type": "update",
            "board": othello_game.board,
            "current_turn": othello_game.current_turn,
            "winner": othello_game.winner,
            "placeable_positions": othello_game.placeable_positions
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("type")

        if action == "place_disc":
            row = data.get("row")
            col = data.get("col")

            from .models import Othello
            othello_game = await sync_to_async(Othello.objects.first)()

            # 駒を置く処理
            success_message = await sync_to_async(othello_game.place_disc)(row, col)

            # 状態更新を全クライアントに通知
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "update_board",
                    "board": othello_game.board,
                    "current_turn": othello_game.current_turn,
                    "winner": othello_game.winner,
                }
            )

    async def update_board(self, event):
        await self.send(text_data=json.dumps({
        "type": "update",
        "board": event["board"],
        "current_turn": event["current_turn"],
        "winner": event["winner"],
    }))
