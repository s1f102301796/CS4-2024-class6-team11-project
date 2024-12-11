from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Othello
import json

def index(request):
    # メニュー画面のビュー
    return render(request, 'game/index.html')

def othello_game(request):
    # ゲーム画面のビュー
    game, created = Othello.objects.get_or_create(id=1)
    if created:
        game.initialize_board()

    # ボードデータと現在のターン
    board = game.board
    current_turn = 'Black' if game.current_turn == 'black' else 'White'

    # デバッグ用
    print("Board data passed to template:", board)

    return render(request, 'game/othello.html', {
        'board': board,
        'current_turn': current_turn,
    })



def place_disc(request, row, col):
    game = get_object_or_404(Othello, id=1)
    row, col = int(row), int(col)

    print(f"Placing disc at ({row}, {col})")  # デバッグログ
    result = game.place_disc(row, col)  # Othello モデル内のロジックを実行
    print(f"Result: {result}")  # 処理結果を確認

    success = result == "Disc placed successfully."
    return JsonResponse({
        'success': success,
        'message': result,
        'board': game.board,  # 必要なら更新後のボードも返す
        'current_turn': game.current_turn
    })

def get_board(request):
    # 最新のゲームデータを取得
    game = Othello.objects.latest('created_at')
    # None を null に変換
    board = [[cell if cell is not None else None for cell in row] for row in game.board]
    return JsonResponse({'board': board, 'current_turn': game.current_turn})
