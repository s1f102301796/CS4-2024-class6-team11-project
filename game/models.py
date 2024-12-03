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

    def can_place(self, x, y):
        # 指定された座標 (x, y) に駒を置けるかどうかを判定する。
        if self.board[x][y] is not None:
            return False  # すでに駒が置かれている場合

        opponent = "black" if self.current_turn == "white" else "white"
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            found_opponent = False

            # 隣接するマスが相手の駒であることを確認
            while 0 <= nx < 8 and 0 <= ny < 8:
                if self.board[nx][ny] == opponent:
                    found_opponent = True
                elif self.board[nx][ny] == self.current_turn:
                    if found_opponent:
                        return True  # 自分の駒に到達した場合
                    break
                else:
                    break
                nx += dx
                ny += dy

        return False
    
    def flip_discs(self, x, y):
        # 指定された座標 (x, y) に駒を置いた後、裏返す駒を処理する。
        opponent = "black" if self.current_turn == "white" else "white"
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        flipped = []  # 裏返した駒の座標を記録

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            discs_to_flip = []

            # 相手の駒が連続している方向を探す
            while 0 <= nx < 8 and 0 <= ny < 8:
                if self.board[nx][ny] == opponent:
                    discs_to_flip.append((nx, ny))
                elif self.board[nx][ny] == self.current_turn:
                    # 自分の駒が見つかったら裏返し処理を確定
                    flipped.extend(discs_to_flip)
                    break
                else:
                    break
                nx += dx
                ny += dy

        # 裏返す
        for fx, fy in flipped:
            self.board[fx][fy] = self.current_turn

        # 現在の座標にも駒を置く
        self.board[x][y] = self.current_turn
        self.save()

        return flipped
    
    def check_game_over(self):
        # ゲームが終了しているかを判定し、終了している場合は勝敗を返す。
        black_count = sum(row.count("black") for row in self.board)
        white_count = sum(row.count("white") for row in self.board)

        # 全てのマスが埋まった場合
        if black_count + white_count == 64:
            return self.determine_winner(black_count, white_count)

        # 両プレイヤーが駒を置けない場合
        if not self.can_any_player_move():
            return self.determine_winner(black_count, white_count)

        return None  # ゲーム継続中

    def can_any_player_move(self):
        # どちらかのプレイヤーが駒を置けるかを確認。
        for x in range(8):
            for y in range(8):
                if self.can_place(x, y):
                    return True
        return False

    def determine_winner(self, black_count, white_count):
        # 勝敗を決定する。
        if black_count > white_count:
            return "Black wins!"
        elif white_count > black_count:
            return "White wins!"
        else:
            return "Draw!"
        
    def switch_turn(self):
        # ターンを切り替える。現在のプレイヤーが駒を置けない場合はスキップ。
        self.current_turn = "white" if self.current_turn == "black" else "black"

        # 次のプレイヤーが駒を置けない場合、再度切り替え
        if not self.can_any_player_move_for_current_turn():
            self.current_turn = "white" if self.current_turn == "black" else "black"

        # 両プレイヤーが駒を置けない場合、ゲーム終了
        if not self.can_any_player_move_for_current_turn():
            return self.check_game_over()

    def can_any_player_move_for_current_turn(self):
        # 現在のターンのプレイヤーが駒を置けるか確認。
        for x in range(8):
            for y in range(8):
                if self.can_place(x, y):
                    return True
        return False
    
    def check_game_over(self):
        # ボード上の駒を数え、結果を判定する。
        black_count = sum(row.count("black") for row in self.board)
        white_count = sum(row.count("white") for row in self.board)

        if black_count > white_count:
            return "Black wins!"
        elif white_count > black_count:
            return "White wins!"
        else:
            return "Draw!"
        
    def __str__(self):
        return f"Othello Game - Current Turn: {self.current_turn}"

