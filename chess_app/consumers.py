# chess_app/consumers.py

import json
import chess
from channels.generic.websocket import AsyncWebsocketConsumer


# （※簡易的にPython側のグローバル変数として部屋を管理）
rooms = {
    # たとえば最初から "chess_game" 部屋を用意しておきたいならこんなイメージ
     "chess_game": {
         "board": chess.Board(),
         "turn": chess.WHITE,
         "players": []
     }
}

class ChessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "chess_game"

        if self.room_group_name not in rooms:
            rooms[self.room_group_name] = {
                "board": chess.Board(),
                "turn": chess.WHITE,  # True=白, False=黒
                "players": []
            }

        room_data = rooms[self.room_group_name]
        players = room_data["players"]

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        if len(players) < 2:
            if not players:
                # 1人目: 白
                players.append({"channel": self.channel_name, "color": chess.WHITE})
                self.player_color = chess.WHITE
            else:
                # 2人目: 黒
                players.append({"channel": self.channel_name, "color": chess.BLACK})
                self.player_color = chess.BLACK

            await self.accept()

            # 初期情報を送信
            await self.send(text_data=json.dumps({
                "message": f"You joined {self.room_group_name}.",
                "color": "white" if self.player_color == chess.WHITE else "black",
                "turn": "white" if room_data["turn"] == chess.WHITE else "black",
                "fen": room_data["board"].fen()
            }))
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        room_data = rooms.get(self.room_group_name)
        if room_data:
            room_data["players"] = [
                p for p in room_data["players"] if p["channel"] != self.channel_name
            ]
            if not room_data["players"]:
                del rooms[self.room_group_name]

    async def receive(self, text_data):
        data = json.loads(text_data)
        move_uci = data.get("move")
        if not move_uci:
            return

        room_data = rooms[self.room_group_name]
        board = room_data["board"]
        current_turn = room_data["turn"]  # True=白, False=黒

        my_color = self.player_color

        # UCIパース
        try:
            chess_move = chess.Move.from_uci(move_uci)
        except ValueError:
            await self.send(text_data=json.dumps({"error": "Invalid UCI notation"}))
            return

        # ターンチェック
        if current_turn != my_color:
            await self.send(text_data=json.dumps({"error": "Not your turn."}))
            return

        # 合法手チェック
        if chess_move not in board.legal_moves:
            await self.send(text_data=json.dumps({"error": "Illegal move."}))
            return

        # 盤面更新
        board.push(chess_move)
        room_data["turn"] = not current_turn  # ターン交代

        # -- ここからゲームの状態を判定 (チェック、チェックメイト、ステイルメイト など) --
        status_message = ""
        winner = None

        if board.is_game_over():
            # ゲーム終了
            if board.is_checkmate():
                # チェックメイト
                # 今pushした手で相手王手詰めが発生したので、指した側が勝者
                #   → "white" if my_color == True else "black"
                winner = "white" if my_color == chess.WHITE else "black"
                status_message = "Checkmate!"
            elif board.is_stalemate():
                # ステイルメイト(引き分け)
                winner = "draw"
                status_message = "Stalemate! Draw!"
            else:
                # 他にも is_insufficient_material, is_seventyfive_moves, etc. などあり
                winner = "draw"
                status_message = "Game Over (Draw)"
        else:
            # まだゲーム続行
            # もし相手がチェックに陥った場合は Check! と表示してあげる
            if board.is_check():
                status_message = "Check!"

        # 全クライアントに盤面更新を送信
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "update_board",
                "fen": board.fen(),
                "turn": "white" if room_data["turn"] == chess.WHITE else "black",
                "move": move_uci,
                "status": status_message,
                "winner": winner if winner else ""
            }
        )

    async def update_board(self, event):
        fen = event["fen"]
        turn = event["turn"]
        move = event["move"]
        status_msg = event["status"]  # "Check!", "Checkmate!", "Stalemate!", etc.
        winner = event["winner"]

        # 全クライアントに送信
        await self.send(text_data=json.dumps({
            "fen": fen,
            "turn": turn,
            "move": move,
            "status": status_msg,
            "winner": winner
        }))
