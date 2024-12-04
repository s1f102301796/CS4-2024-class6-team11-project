from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Othello

# Create your views here.

def index(request):
    # 初回アクセス時にゲームを初期化
    game, created = Othello.objects.get_or_create(id=1)
    if created:
        game.initialize_board()
    return render(request, 'game/index.html', {'board': game.board})

def othello_game(request):
    # ゲーム画面のビュー
    return render(request, 'othello.html')

def place_disc(request, row, col):
    game = get_object_or_404(Othello, id=1)
    row, col = int(row), int(col)
    result = game.place_disc(row, col)
    return JsonResponse({'success': result == "Disc placed successfully.", 'message': result})

def get_board(request):
    # 最新のゲームデータを取得
    game = Othello.objects.latest('created_at')
    return JsonResponse({'board': game.board, 'current_turn': game.current_turn})

