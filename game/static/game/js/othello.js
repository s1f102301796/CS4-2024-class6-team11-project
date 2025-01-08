document.addEventListener("DOMContentLoaded", () => {
    const boardElement = document.getElementById("othello-board");
    const currentTurnElement = document.getElementById("current-turn");
    const winnerElement = document.getElementById("winner");
    const roomName = "default_room"; // またはURLから取得するロジックを追加

    let gameSocket = null;

    // WebSocketの初期化
    function initializeWebSocket() {
        gameSocket = new WebSocket(`ws://${window.location.host}/ws/game/${roomName}/`);

        gameSocket.onopen = () => {
            console.log("WebSocket connection established.");
        };

        gameSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("WebSocket message received:", data);
        
            if (data.type === "update") {
                const placeablePositions = data.placeable_positions || [];
                console.log("Placeable positions received:", placeablePositions);
        
                if (placeablePositions.length === 0) {
                    console.error("No placeable positions! Backend may not be calculating them correctly.");
                }
        
                updateBoard(data.board, placeablePositions);
            }
        };
        
        gameSocket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        gameSocket.onclose = (event) => {
            console.warn("WebSocket connection closed, attempting to reconnect...");
            setTimeout(initializeWebSocket, 1000); // 再接続
        };
    }
      

    // 駒を置く処理
    function placeDisc(row, col) {
        if (gameSocket && gameSocket.readyState === WebSocket.OPEN) {
            gameSocket.send(JSON.stringify({
                type: "place_disc",
                row: row,
                col: col,
            }));
        } else {
            console.error("WebSocket is not open.");
        }
    }

    function updateBoard(board, placeablePositions) {
        console.log("Updating board with data:", board, "Placeable positions:", placeablePositions);
    
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

    function createBoardCell(cell, rowIndex, colIndex, placeablePositions) {
        const cellElement = document.createElement("td");
        cellElement.id = `cell-${rowIndex}-${colIndex}`;
        cellElement.className = "cell";
    
        if (cell === "black") {
            cellElement.classList.add("black");
        } else if (cell === "white") {
            cellElement.classList.add("white");
        } else if (isPlaceable(rowIndex, colIndex, placeablePositions)) {
            console.log(`Cell (${rowIndex}, ${colIndex}) is placeable.`);
            cellElement.classList.add("placeable");
            cellElement.addEventListener("click", () => placeDisc(rowIndex, colIndex));
        } else {
            cellElement.textContent = ""; // 空白
        }
    
        return cellElement;
    }

    function isPlaceable(row, col, placeablePositions) {
        // placeablePositions が存在しない場合は空配列扱い
        if (!Array.isArray(placeablePositions)) {
            console.warn("placeablePositions is not an array:", placeablePositions);
            return false;
        }
    
        // 設置可能な位置をチェック
        return placeablePositions.some(([x, y]) => x === row && y === col);
    }
    

    // 現在のターンを更新
    function updateCurrentTurn(turn) {
        currentTurnElement.textContent = `Current Turn: ${turn}`;
    }


    // 初期化
    initializeWebSocket();
});
