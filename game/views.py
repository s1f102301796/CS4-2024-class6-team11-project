from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
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

@csrf_exempt 
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

@ensure_csrf_cookie
def get_board(request):
    # 最新のゲームデータを取得
    game = Othello.objects.latest('created_at')
    placeable_positions = game.get_placeable_positions()
    # None を null に変換
    board = [[cell if cell in ["black", "white"] else None for cell in row] for row in game.board]
    return JsonResponse({'board': board, 'current_turn': game.current_turn, "placeable_positions": placeable_positions,'winner': game.winner})

def othello_game_view(request, game_id):
    game = get_object_or_404(Othello, id=game_id)
    placeable_positions = game.get_placeable_positions()

    # デバッグ用ログ出力
    print(f"Current Turn: {game.current_turn}")
    print(f"Winner: {game.winner}")

    context = {
        "board": game.board,
        "current_turn": game.current_turn,
        "placeable_positions": placeable_positions,
        "winner": game.winner,
    }
    return render(request, "othello.html", context)
