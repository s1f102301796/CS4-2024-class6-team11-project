document.addEventListener("DOMContentLoaded", () => {
    const boardElement = document.getElementById("othello-board");
    const currentTurnElement = document.getElementById("current-turn");
    const winnerElement = document.getElementById("winner");
    const playerColorElement = document.getElementById("player-color");

    let gameSocket = null;
    let playerColor = null;

    function initializeWebSocket() {
        gameSocket = new WebSocket(`ws://${window.location.host}/ws/game/${roomName}/`);

        gameSocket.onopen = () => {
            console.log("WebSocket connection established.");
        };

        gameSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === "player_color") {
                playerColor = data.player_color;
                updatePlayerColor(playerColor);
            }

            if (data.type === "update") {
                if (data.winner) {
                    winnerElement.textContent = `Player ${data.winner} WIN!`
                } else {
                    updateBoard(data.board, data.placeable_positions);
                    updateCurrentTurn(data.current_turn);
                }
            }

            if (data.type === "error") {
                alert(data.message);
            }
        };

        gameSocket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        gameSocket.onclose = (event) => {
            console.warn("WebSocket connection closed, attempting to reconnect...");
            setTimeout(initializeWebSocket, 1000);
        };
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

    initializeWebSocket();
});
