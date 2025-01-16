document.addEventListener("DOMContentLoaded", () => {
    const boardElement = document.getElementById("othello-board");
    const currentTurnElement = document.getElementById("current-turn");
    const winnerElement = document.getElementById("winner");
    const playerColorElement = document.getElementById("player-color");
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");
    const statusMessage = document.createElement("div");
    statusMessage.id = "status-message";
    document.body.appendChild(statusMessage);

    let gameSocket = null;
    let playerColor = null;
    let reconnectTimer = null;

    function initializeWebSocket() {
        if (gameSocket) {
            gameSocket.close();
        }

        gameSocket = new WebSocket(`ws://${window.location.host}/ws/game/${roomName}/`);

        gameSocket.onopen = () => {
            console.log("WebSocket connection established.");
            clearStatus();
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
        };

        gameSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case "player_color":
                    playerColor = data.player_color;
                    console.log(playerColor);
                    updatePlayerColor(playerColor);
                    break;

                case "update":
                    if (data.winner) {
                        winnerElement.textContent = `Player ${data.winner} WIN!`;
                    } else {
                        updateBoard(data.board, data.placeable_positions);
                        updateCurrentTurn(data.current_turn);
                    }
                    break;

                case "error":
                    alert(data.message);
                    break;

                case "player_disconnected":
                    showStatus(data.message, "warning");
                    break;

                case "game_ended":
                    showStatus(data.message, "error");
                    winnerElement.textContent = `Player ${data.winner} WIN!`;
                    break;

                case "chat_message":
                    addChatMessage(data.message, data.username, data.player_color);
                    break;
            }
        };

        gameSocket.onerror = (error) => {
            console.error("WebSocket error:", error);
            showStatus("Connection error occurred", "error");
        };

        gameSocket.onclose = (event) => {
            console.warn("WebSocket connection closed, attempting to reconnect...");
            showStatus("Connection lost. Attempting to reconnect...", "warning");
            
            // 再接続を試みる
            reconnectTimer = setTimeout(initializeWebSocket, 1000);
        };
    }

    function showStatus(message, type = "info") {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.style.display = "block";
    }

    function clearStatus() {
        statusMessage.style.display = "none";
    }

    function placeDisc(row, col) {
        if (gameSocket && gameSocket.readyState === WebSocket.OPEN) {
            gameSocket.send(JSON.stringify({
                type: "place_disc",
                row: row,
                col: col,
            }));
        }
    }

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message && gameSocket && gameSocket.readyState === WebSocket.OPEN) {
            gameSocket.send(JSON.stringify({
                type: "message_send",
                message: message
            }));
            messageInput.value = "";
        }
    }

    function addChatMessage(message, username, messagePlayerColor) {
        // チャットログを表示する要素を取得
        const chatLog = document.querySelector(".chat-log");
        
        // チャットメッセージの要素を作成
        const messageElement = document.createElement("div");
        messageElement.className = "chat-message";
        
        // プレイヤーの色に応じてスタイルを適用
        if (messagePlayerColor === playerColor) {
            messageElement.classList.add("my-message");
        }
        
        // メッセージの内容をHTMLとして追加
        messageElement.innerHTML = `
            <span class="username ${messagePlayerColor}">${username}</span>
            <span class="message-content">${message}</span>
        `;
        
        // チャットログにメッセージを追加
        chatLog.appendChild(messageElement);
        
        // チャットログをスクロールして最新メッセージを表示
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    function updateBoard(board, placeablePositions) {
        boardElement.innerHTML = "";

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
            cellElement.classList.add("placeable");
            cellElement.addEventListener("click", () => placeDisc(rowIndex, colIndex));
        }

        return cellElement;
    }

    function isPlaceable(row, col, placeablePositions) {
        return placeablePositions.some(([x, y]) => x === row && y === col);
    }

    function updatePlayerColor(color) {
        playerColorElement.textContent = `Your Color: ${color}`;
    }

    function updateCurrentTurn(turn) {
        currentTurnElement.textContent = `Current Turn: ${turn}`;
        if (playerColor === turn) {
            currentTurnElement.textContent += " (Your turn)";
        }
    }

    if (sendButton) {
        sendButton.addEventListener("click", sendMessage);
    }

    if (messageInput) {
        messageInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                sendMessage();
            }
        });
    }

    initializeWebSocket();
});
