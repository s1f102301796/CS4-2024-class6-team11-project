from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .models import Othello, MatchmakingQueue

waiting_players = []

@login_required
def index(request):
    # ロビー画面を表示
    return render(request, "game/index.html")


@csrf_exempt
def join_queue(request):
    global waiting_players
    player = request.user.username if request.user.is_authenticated else 'Guest'

    if player not in waiting_players:
        waiting_players.append(player)

    # プレイヤーが2人揃った場合に部屋を作成
    if len(waiting_players) >= 2:
        player1 = waiting_players.pop(0)
        player2 = waiting_players.pop(0)
        room_name = f"{player1}_vs_{player2}"  # 部屋名を生成

        # 必要に応じて部屋情報を保存する処理を追加可能
        return JsonResponse({'success': True, 'room_name': room_name})
    else:
        return JsonResponse({'success': False, 'message': 'Waiting for another player.'})


@login_required
def othello_game(request):
    # ユーザー情報を取得
    user = request.user
    game, created = Othello.objects.get_or_create(id=1)
    if created:
        game.initialize_board()

    # ボードデータと現在のターン情報
    board = game.board
    current_turn = 'Black' if game.current_turn == 'black' else 'White'

    # プレイヤー情報
    player_black = game.player_black
    player_white = game.player_white

    context = {
        'board': board,
        'current_turn': current_turn,
        'player_black': player_black,
        'player_white': player_white,
        'current_user': user,
        'winner': game.winner,
    }
    return render(request, 'game/othello.html', context)


def othello_room(request, room_name):
    # ルーム名を渡してゲーム画面を表示
    return render(request, 'game/othello.html', {'room_name': room_name})


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
        'board': game.board,
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
