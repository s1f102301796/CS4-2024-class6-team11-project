from django.db import models

# Create your models here.

class Othello(models.Model):
    #8x8のボード状態をJSONで管理
    board = models.JSONField(default=list)
    #現在のターンを管理
    current_turn = models.CharField(
        max_length = 5,
        choices=[('black', 'Black'), ('white', 'White')],
        default='black'
    )
    #勝者を管理
    winner = models.CharField(
        max_length = 5,
        choices=[('black', 'Black'), ('white', 'White')],
        null = True,
        blank=True
    )
    #ゲームの作成・更新日時の記録
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def initialize_board(self):
        #オセロの初期盤面の設定
        self.board = [
            [None] * 8 for _ in range(8)
        ]
        #初期配置
        self.board[3][3] = 'white'
        self.board[3][4] = 'black'
        self.board[4][3] = 'black'
        self.board[4][4] = 'white'
        self.current_turn = 'black'
        self.save()

    def __str__(self):
        return f"Othello Game - Current Turn: {self.current_turn}"

