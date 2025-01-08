document.addEventListener("DOMContentLoaded", () => {
    const boardElement = document.getElementById("othello-board");
    const currentTurnElement = document.getElementById("current-turn");
    const winnerElement = document.getElementById("winner");
    const roomName = "example_room"; // WebSocketルーム名（適宜変更）

    let gameSocket = null;

    // WebSocketの初期化関数
    function initializeWebSocket() {
        gameSocket = new WebSocket(`ws://${window.location.host}/ws/game/${roomName}/`);

        // WebSocket接続時
        gameSocket.onopen = () => {
            console.log("WebSocket connection established.");
        };

        // WebSocketメッセージ受信時
        gameSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("WebSocket message received:", data);

            if (data.type === "update") {
                updateBoard(data.board, data.placeable_positions);
                updateCurrentTurn(data.current_turn);
                updateWinner(data.winner);
            }
        };

        // WebSocketエラー時
        gameSocket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        // WebSocket切断時
        gameSocket.onclose = (event) => {
            console.warn("WebSocket connection closed, attempting to reconnect...");
            setTimeout(initializeWebSocket, 1000); // 1秒後に再接続を試みる
        };
    }

    // WebSocket経由で駒を置くデータを送信
    function placeDisc(row, col) {
        if (gameSocket.readyState === WebSocket.OPEN) {
            gameSocket.send(JSON.stringify({
                type: "place_disc",
                row: row,
                col: col,
            }));
        } else {
            console.error("Cannot place disc, WebSocket is not open.");
        }
    }

    // API リクエストの共通関数
    async function apiRequest(endpoint, method = "GET", body = null) {
        const csrfToken = document.querySelector("meta[name='csrf-token']").getAttribute("content");
        const options = {
            method,
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
            },
        };
        if (body) {
            options.body = JSON.stringify(body);
        }
        try {
            const response = await fetch(endpoint, options);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error with API request to ${endpoint}:`, error);
            throw error;
        }
    }

    // ボードデータの取得と更新
    async function fetchBoard() {
        try {
            const data = await apiRequest("/game/get_board/");
            console.log("Board data received:", data);
            updateBoard(data.board, data.placeable_positions);
            updateCurrentTurn(data.current_turn);
            updateWinner(data.winner);
        } catch (error) {
            console.error("Error fetching board:", error);
            alert("Failed to fetch the board. Please try again.");
        }
    }

    // ボードを更新
    function updateBoard(board, placeablePositions) {
        boardElement.innerHTML = ""; // 既存のボードをクリア

        const tableElement = document.createElement("table");

        board.forEach((row, rowIndex) => {
            const rowElement = document.createElement("tr");

            row.forEach((cell, colIndex) => {
                const cellElement = createBoardCell(cell, rowIndex, colIndex, placeablePositions);
                rowElement.appendChild(cellElement);
            });

            tableElement.appendChild(rowElement);
        });

        boardElement.appendChild(tableElement);
    }

    // セルを生成
    function createBoardCell(cell, rowIndex, colIndex, placeablePositions) {
        const cellElement = document.createElement("td");
        cellElement.id = `cell-${rowIndex}-${colIndex}`;
        cellElement.className = "cell";

        if (cell === "black") {
            cellElement.classList.add("black");
        } else if (cell === "white") {
            cellElement.classList.add("white");
        } else if (isPlaceable(rowIndex, colIndex, placeablePositions)) {
            cellElement.classList.add("placeable");
            cellElement.addEventListener("click", () => placeDisc(rowIndex, colIndex));
        } else {
            cellElement.textContent = ""; // 空白
        }

        return cellElement;
    }

    // 設置可能なマスかどうか確認
    function isPlaceable(row, col, placeablePositions) {
        return placeablePositions.some(([x, y]) => x === row && y === col);
    }

    // 現在のターンを更新
    function updateCurrentTurn(turn) {
        currentTurnElement.textContent = `Current Turn: ${turn}`;
    }

    // 勝者の表示を更新
    function updateWinner(winner) {
        if (winner) {
            const message =
                winner === "black"
                    ? "Game Over! Black wins!"
                    : winner === "white"
                    ? "Game Over! White wins!"
                    : "Game Over! It's a tie!";
            winnerElement.textContent = message;
        } else {
            winnerElement.textContent = ""; // ゲーム継続中ならクリア
        }
    }

    // 初期ロード時にボードを取得
    fetchBoard();

    // WebSocketを初期化
    initializeWebSocket();
});
