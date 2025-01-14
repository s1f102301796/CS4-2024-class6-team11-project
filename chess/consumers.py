# chess/consumers.py
import json
import chess
from channels.generic.websocket import AsyncWebsocketConsumer

class ChessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'chess_game'

        # 初期化: チェスゲームの状態を保存
        self.board = chess.Board()

        # WebSocket接続を受け入れる
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # チャンネルグループから削除
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # クライアントからのメッセージを受信
        data = json.loads(text_data)
        move = data.get('move')

        try:
            # チェスの合法手を確認して処理
            chess_move = chess.Move.from_uci(move)
            if chess_move in self.board.legal_moves:
                self.board.push(chess_move)

                # 全クライアントに盤面更新を通知
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'update_board',
                        'fen': self.board.fen(),  # 現在の盤面のFEN文字列
                        'move': move,
                    }
                )
            else:
                # 非合法な手をクライアントに通知
                await self.send(text_data=json.dumps({'error': 'Illegal move'}))
        except ValueError:
            # エラーをクライアントに通知
            await self.send(text_data=json.dumps({'error': 'Invalid move format'}))

    async def update_board(self, event):
        # クライアントに盤面更新を送信
        fen = event['fen']
        move = event['move']
        await self.send(text_data=json.dumps({
            'fen': fen,
            'move': move,
        }))
