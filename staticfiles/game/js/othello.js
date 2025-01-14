document.addEventListener("DOMContentLoaded", () => {
    const boardElement = document.getElementById("othello-board");
    const currentTurnElement = document.getElementById("current-turn");

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
                updateBoard(data.board);
                updateCurrentTurn(data.current_turn);
            })
            .catch(error => console.error("Error fetching board:", error));
    }

    // ボードを更新
    function updateBoard(board) {
        // 既存の行を削除する
        while (boardElement.firstChild) {
            boardElement.removeChild(boardElement.firstChild);
        }
    
        board.forEach((row, rowIndex) => {
            const rowElement = document.createElement("div");
            rowElement.className = "board-row";
    
            row.forEach((cell, colIndex) => {
                const cellElement = document.createElement("div");
                cellElement.className = "board-cell";
    
                if (cell === "black") {
                    cellElement.classList.add("disc-black");
                } else if (cell === "white") {
                    cellElement.classList.add("disc-white");
                }
    
                // セルクリックイベント
                cellElement.addEventListener("click", () => {
                    if (!cell) placeDisc(rowIndex, colIndex); // 空白セルのみクリック可能
                });
    
                rowElement.appendChild(cellElement);
            });
    
            boardElement.appendChild(rowElement);
        });
    }

    // 現在のターンを更新
    function updateCurrentTurn(turn) {
        currentTurnElement.textContent = `Current Turn: ${turn}`;
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
