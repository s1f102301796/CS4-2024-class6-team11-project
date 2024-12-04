document.addEventListener("DOMContentLoaded", function () {
    const boardContainer = document.getElementById("board-container");
    const currentTurn = document.getElementById("current-turn");
    const gameStatus = document.getElementById("game-status");
    const restartButton = document.getElementById("restart-button");

    // 初期化処理
    function initializeBoard() {
        boardContainer.innerHTML = ""; // ボードのリセット
        for (let i = 0; i < 8; i++) {
            for (let j = 0; j < 8; j++) {
                const cell = document.createElement("div");
                cell.dataset.row = i;
                cell.dataset.col = j;
                cell.addEventListener("click", handleCellClick);
                boardContainer.appendChild(cell);
            }
        }
        updateTurnDisplay("Black");
    }

    function handleCellClick(event) {
        const row = event.target.dataset.row;
        const col = event.target.dataset.col;
        console.log(`Cell clicked at: (${row}, ${col})`);
        // Djangoとの通信（駒を置く処理）
    }

    function updateTurnDisplay(turn) {
        currentTurn.textContent = turn;
    }

    restartButton.addEventListener("click", initializeBoard);

    // ゲームの初期化
    initializeBoard();
});

document.addEventListener("DOMContentLoaded", () => {
    fetch('/game/get_board/')
        .then(response => response.json())
        .then(data => {
            drawBoard(data.board, data.current_turn);
        })
        .catch(error => console.error('Error fetching board:', error));
});

function drawBoard(board, currentTurn) {
    const boardElement = document.getElementById('game-board');
    boardElement.innerHTML = ''; // 一旦クリア

    board.forEach((row, x) => {
        const rowElement = document.createElement('div');
        rowElement.classList.add('row');
        row.forEach((cell, y) => {
            const cellElement = document.createElement('div');
            cellElement.classList.add('cell');
            cellElement.dataset.x = x;
            cellElement.dataset.y = y;

            if (cell === 'black') {
                cellElement.classList.add('black-disc');
            } else if (cell === 'white') {
                cellElement.classList.add('white-disc');
            }

            rowElement.appendChild(cellElement);
        });
        boardElement.appendChild(rowElement);
    });

    document.getElementById('current-turn').textContent = `Current Turn: ${currentTurn}`;
}

