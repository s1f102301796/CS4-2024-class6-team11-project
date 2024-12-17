from django.db import models


class Othello(models.Model):
    # 8x8のボード状態をJSONで管理
    board = models.JSONField(default=list)
    # 現在のターン
    current_turn = models.CharField(
        max_length=5,
        choices=[("black", "Black"), ("white", "White")],
        default="black",
    )
    # 勝者
    winner = models.CharField(
        max_length=5,
        choices=[("black", "Black"), ("white", "White")],
        null=True,
        blank=True,
    )
    # 作成・更新日時
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # オセロの移動方向リスト（共通化）
    DIRECTIONS = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)
    ]

    def initialize_board(self):
        # オセロの初期盤面設定
        self.board = [[None] * 8 for _ in range(8)]
        self.board[3][3] = self.board[4][4] = "white"
        self.board[3][4] = self.board[4][3] = "black"
        self.current_turn = "black"
        self.winner = None  # 勝者データもリセット
        self.save()


    def is_valid_position(self, x, y):
        # ボード内の有効な座標か判定
        return 0 <= x < 8 and 0 <= y < 8


    def can_place(self, x, y):
        # 指定位置に駒を置けるか判定
        if self.board[x][y] is not None:
            return False

        opponent = "black" if self.current_turn == "white" else "white"
        for dx, dy in self.DIRECTIONS:
            nx, ny = x + dx, y + dy
            found_opponent = False

            while self.is_valid_position(nx, ny) and self.board[nx][ny] == opponent:
                found_opponent = True
                nx += dx
                ny += dy

            if found_opponent and self.is_valid_position(nx, ny) and self.board[nx][ny] == self.current_turn:
                return True

        return False


    def flip_discs(self, x, y):
        # 指定位置で駒を裏返す
        opponent = "black" if self.current_turn == "white" else "white"

        for dx, dy in self.DIRECTIONS:
            nx, ny = x + dx, y + dy
            discs_to_flip = []

            while self.is_valid_position(nx, ny) and self.board[nx][ny] == opponent:
                discs_to_flip.append((nx, ny))
                nx += dx
                ny += dy

            if self.is_valid_position(nx, ny) and self.board[nx][ny] == self.current_turn:
                for fx, fy in discs_to_flip:
                    self.board[fx][fy] = self.current_turn

        self.board[x][y] = self.current_turn
        self.save()


    def switch_turn(self):
        # 現在のプレイヤーのターンを切り替える
        self.current_turn = "white" if self.current_turn == "black" else "black"

        # 次のプレイヤーが駒を置けない場合、さらにターンを切り替える
        if not self.can_any_player_move():
            print(f"No valid moves for {self.current_turn}. Switching turn again.")
            self.current_turn = "white" if self.current_turn == "black" else "black"

            # 両プレイヤーが置けない場合はゲーム終了
            if not self.can_any_player_move():
                print("No valid moves for both players. Ending the game.")
                self.check_game_over()
                return
        
        print(f"Next turn: {self.current_turn}") # デバッグ用


    def can_any_player_move(self):
        # 現在のターンで駒を置ける位置があるか確認
        for x in range(8):
            for y in range(8):
                if self.can_place(x, y):
                    print(f"Player {self.current_turn} can place at ({x}, {y})")
                    return True
        print(f"Player {self.current_turn} has no valid moves.")
        return False
    

    def can_any_player_move_for(self, player_color):
        # 現在のターンを一時的に指定のプレイヤーに変更して判定
        original_turn = self.current_turn
        self.current_turn = player_color
        can_move = any(
            self.can_place(row, col) for row in range(8) for col in range(8)
        )
        self.current_turn = original_turn  # 元のターンに戻す
        return can_move
    

    def get_placeable_positions(self):
        # 設置可能なマスのリストを返す [(x, y), ...] の形式
        placeable_positions = []
        for x in range(8):
            for y in range(8):
                if self.can_place(x, y):
                    placeable_positions.append((x, y))
        return placeable_positions


    def check_game_over(self):
        # 黒と白の駒の数をカウント
        black_count = sum(row.count("black") for row in self.board)
        white_count = sum(row.count("white") for row in self.board)

        print(f"Black count: {black_count}, White count: {white_count}")

        # すべてのマスが埋まった場合
        board_full = black_count + white_count == 64

        # 両プレイヤーが駒を置けない場合
        no_moves_for_black = not self.can_any_player_move_for("black")
        no_moves_for_white = not self.can_any_player_move_for("white")
        both_cannot_move = no_moves_for_black and no_moves_for_white

        # 終了条件
        if board_full or both_cannot_move:
            if black_count > white_count:
                self.winner = "black"
            elif white_count > black_count:
                self.winner = "white"
            else:
                self.winner = None  # 引き分け

            self.save()  # 結果を保存
            print(f"Game over. Winner: {self.winner}")
        else:
            print("Game not over yet.")


    def place_disc(self, x, y):
        # 指定位置に駒を置く
        if not self.is_valid_position(x, y):
            return "Invalid position!"
        if self.board[x][y] is not None:
            return "Invalid position! Cell already occupied."
        if not self.can_place(x, y):
            return "Invalid move! Cannot place here."

        self.flip_discs(x, y)
        self.switch_turn()
        self.save()  # 状態を保存
        return "Disc placed successfully."


    def __str__(self):
        return f"Othello Game - Current Turn: {self.current_turn}"
