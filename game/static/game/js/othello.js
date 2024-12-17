document.addEventListener("DOMContentLoaded", () => {
    const boardElement = document.getElementById("othello-board");
    const currentTurnElement = document.getElementById("current-turn");
    const winnerElement = document.getElementById("winner");

    // API リクエストの共通関数
    function apiRequest(endpoint, method = "GET", body = null) {
        const options = { method };
        if (body) {
            options.headers = { "Content-Type": "application/json" };
            options.body = JSON.stringify(body);
        }
        return fetch(endpoint, options).then(response => response.json());
    }

    // ボードデータの取得と更新
    function fetchBoard() {
        apiRequest("/game/get_board/")
            .then(data => {
                console.log("Board data received:", data); // デバッグ用
                updateBoard(data.board, data.placeable_positions); // 設置可能なマスを渡す
                updateCurrentTurn(data.current_turn);
                updateWinner(data.winner); // 勝者の表示を更新
            })
            .catch(error => console.error("Error fetching board:", error));
    }

    // ボードを更新
    function updateBoard(board, placeablePositions) {
        // 既存の行を削除する
        while (boardElement.firstChild) {
            boardElement.removeChild(boardElement.firstChild);
        }
    
        // ボードを生成
        const tableElement = document.createElement("table");
    
        board.forEach((row, rowIndex) => {
            const rowElement = document.createElement("tr");
    
            row.forEach((cell, colIndex) => {
                const cellElement = document.createElement("td");
                cellElement.id = `cell-${rowIndex}-${colIndex}`;
                cellElement.className = "cell";
    
                if (cell === "black") {
                    cellElement.classList.add("black");
                } else if (cell === "white") {
                    cellElement.classList.add("white");
                } else if (placeablePositions.some(([x, y]) => x === rowIndex && y === colIndex)) {
                    // 設置可能なマスのサイン
                    cellElement.classList.add("placeable");
                    cellElement.addEventListener("click", () => {
                        placeDisc(rowIndex, colIndex);
                    });
                } else {
                    cellElement.textContent = " "; // 空白
                }
    
                rowElement.appendChild(cellElement);
            });
    
            tableElement.appendChild(rowElement);
        });
    
        boardElement.appendChild(tableElement);
    }
    
    // 現在のターンを更新
    function updateCurrentTurn(turn) {
        currentTurnElement.textContent = `Current Turn: ${turn}`;
    }

    function updateWinner(winner) {
        if (winner) {
            const message =
                winner === "black"
                    ? "Game Over! Black wins!"
                    : winner === "white"
                    ? "Game Over! White wins!"
                    : "Game Over! It's a tie!";
            winnerElement.textContent = message; // 結果を表示
        } else {
            winnerElement.textContent = ""; // ゲーム継続中なら空にする
        }
    }

    // 駒を置くリクエスト
    function placeDisc(row, col) {
        apiRequest(`/game/place_disc/${row}/${col}/`)
            .then(data => {
                if (data.success) {
                    fetchBoard();
                } else {
                    alert(data.message); // 無効な移動の場合にメッセージを表示
                }
            })
            .catch(error => console.error("Error placing disc:", error));
    }

    // 初期ロード時にボードを取得
    fetchBoard();
});
