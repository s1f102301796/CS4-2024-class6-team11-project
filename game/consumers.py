from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json
import random

class OthelloConsumer(AsyncWebsocketConsumer):
    players = {}  # プレイヤーごとの色を管理
    
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"game_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # プレイヤーの色を割り当て
        if len(self.players) == 0:
            self.players[self.channel_name] = "black"
        elif len(self.players) == 1:
            existing_color = list(self.players.values())[0]
            self.players[self.channel_name] = "white" if existing_color == "black" else "black"
        else:
            # 2人以上接続できないようにする
            await self.close()
            return

        self.player_color = self.players[self.channel_name]

        # 割り当てられた色を送信
        await self.send(text_data=json.dumps({
            "type": "player_color",
            "player_color": self.player_color,
        }))

        print(f"WebSocket connected: {self.channel_name}, Color: {self.player_color}")

        # 初期ボード状態を送信
        from .models import Othello
        othello_game = await sync_to_async(Othello.objects.get)()
        
        # デバッグ: 初期状態の確認
        print(f"Initial board: {othello_game.board}")
        print(f"Initial current turn: {othello_game.current_turn}")
        print(f"Initial placeable positions: {othello_game.placeable_positions}")

        await self.send(text_data=json.dumps({
            "type": "update",
            "board": othello_game.board,
            "current_turn": othello_game.current_turn,
            "winner": othello_game.winner,
            "placeable_positions": othello_game.placeable_positions
        }))

    async def disconnect(self, close_code):
        # プレイヤー情報を削除
        if self.channel_name in self.players:
            del self.players[self.channel_name]

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("type")

        print(f"Received data from client: {data}")

        if action == "place_disc":
            row = data.get("row")
            col = data.get("col")

            from .models import Othello
            othello_game = await sync_to_async(Othello.objects.first)()

            # プレイヤーの色が現在のターンと一致するかを確認
            if self.player_color != othello_game.current_turn:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "It's not your turn!"
                }))
                return

            # 駒を置く処理
            success_message = await sync_to_async(othello_game.place_disc)(row, col)

            print(f"Board after move: {othello_game.board}")
            print(f"Next turn: {othello_game.current_turn}")
            print(f"Placeable positions after move: {othello_game.placeable_positions}")

            # 状態更新を全クライアントに通知
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "update_board",
                    "board": othello_game.board,
                    "current_turn": othello_game.current_turn,
                    "winner": othello_game.winner,
                    "placeable_positions": othello_game.placeable_positions,
                }
            )

    async def update_board(self, event):
        print(f"update_board event data: {event}")

        await self.send(text_data=json.dumps({
            "type": "update",
            "board": event["board"],
            "current_turn": event["current_turn"],
            "winner": event["winner"],
            "placeable_positions": event["placeable_positions"],
        }))
