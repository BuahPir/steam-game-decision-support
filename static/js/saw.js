let criteria = [];
let weights = [];
let games = [];
let criteriaTypes = [];
let steamGamesData = {};

window.onload = function() {
    const storedWeights = localStorage.getItem('ahp_weights');
    const storedCriteria = localStorage.getItem('ahp_criteria');
    
    if (storedWeights && storedCriteria) {
        weights = JSON.parse(storedWeights);
        criteria = JSON.parse(storedCriteria);
        criteriaTypes = criteria.map(() => 'benefit');
        displayWeights();
    } else {
        document.getElementById('weightsContainer').innerHTML = `
            <div class="no-weights">
                No weights found. Please complete <a href="/ahp">AHP Weighting</a> first.
            </div>
        `;
    }
    updateGameList();
};

async function uploadAndParseExcel() {
    const fileInput = document.getElementById('excelFile');
    
    if (fileInput.files.length === 0) {
        alert('Please select an Excel file to upload.');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Uploading...';

    try {
        const response = await fetch('/upload_saw_data', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success === true) {
            if (JSON.stringify(data.criteria_from_file) !== JSON.stringify(criteria)) {
                alert(
                    "Import Error: The criteria in your Excel file do not match the criteria from the AHP step.\n\n" +
                    "AHP Criteria: " + criteria.join(', ') + "\n" +
                    "Excel Criteria: " + data.criteria_from_file.join(', ') + "\n\n" +
                    "Please ensure your Excel columns (from B onwards) are in the same order as your AHP criteria."
                );
                return;
            }

            games = [];
            steamGamesData = {};
            games = data.alternatives;
            updateGameList();
            
            alert(`Successfully imported ${games.length} alternatives. Generating matrix...`);
            
            generateDecisionMatrix();
            
            data.decision_matrix.forEach((row, i) => {
                row.forEach((value, j) => {
                    const inputElement = document.getElementById(`value_${i}_${j}`);
                    if (inputElement) {
                        inputElement.value = value;
                    }
                });
            });

        } else {
            alert('Error parsing file: ' + data.error);
        }
    } catch (error) {
        alert('An error occurred during upload: ' + error);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Upload and Populate';
        fileInput.value = '';
    }
}

async function fetchSteamGames() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Fetching from Steam...';
    
    try {
        const response = await fetch('/get_steam_games', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success === true) {
            games = [];
            steamGamesData = {};
            
            data.games.forEach(game => {
                if (game.name) {
                    games.push(game.name);
                    steamGamesData[game.name] = game;
                }
            });
            
            updateGameList();
            alert(`Successfully loaded ${games.length} games from Steam!`);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error fetching Steam games: ' + error);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Fetch Default Games List';
    }
}

async function searchByAppID() {
    const input = document.getElementById('steamAppID');
    const appid = input.value.trim();
    
    if (!appid) {
        alert('Please enter a Steam AppID.');
        return;
    }

    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Searching...';

    try {
        const response = await fetch(`/search_steam_game/${appid}`);
        const data = await response.json();

        if (data.success === true) {
            const game = data.game;

            if (games.includes(game.name)) {
                alert(`'${game.name}' is already in the list.`);
            } else {
                games.push(game.name);
                steamGamesData[game.name] = game;
                updateGameList();
                input.value = '';
            }
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('An error occurred during search: ' + error);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Add Game by ID';
    }
}

function displayWeights() {
    const container = document.getElementById('weightsContainer');
    let html = '<div class="weight-badges">';
    
    criteria.forEach((criterion, index) => {
        const weight = (weights[index] * 100).toFixed(2);
        html += `<div class="weight-badge">${criterion}: ${weight}%</div>`;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function addGame() {
    const input = document.getElementById('newGame');
    const game = input.value.trim();
    
    if (game && !games.includes(game)) {
        games.push(game);
        updateGameList();
        input.value = '';
    }
}

function removeGame(button) {
    const tag = button.parentElement;
    const game = tag.querySelector('span').textContent.trim();
    games = games.filter(g => g !== game);
    updateGameList();
}

function updateGameList() {
    const list = document.getElementById('gameList');
    list.innerHTML = games.map(g => 
        `<div class="game-tag">
            <span>${g}</span>
            <button onclick="removeGame(this)">Remove</button>
        </div>`
    ).join('');
}

function generateDecisionMatrix() {
    if (games.length < 2) {
        alert('Please add at least 2 games');
        return;
    }
    
    if (criteria.length === 0) {
        alert('Please complete AHP weighting first');
        return;
    }
    
    let html = '<h3>Decision Matrix</h3>';
    html += '<p class="subtitle">Values will be auto-filled from Steam data if available, or from your uploaded file.</p>';
    html += '<table><thead><tr><th>Game</th>';
    
    criteria.forEach(c => {
        html += `<th>${c}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    games.forEach((game, i) => {
        html += `<tr><th>${game}</th>`;
        criteria.forEach((criterion, j) => {
            let defaultValue = 0;
            
            if (steamGamesData[game]) {
                const gameData = steamGamesData[game];
                const criterionLower = criterion.toLowerCase();
                
                if (criterionLower.includes('tahun') || criterionLower.includes('year')) {
                    defaultValue = gameData.release_year_score || 0;
                } else if (criterionLower.includes('cpu')) {
                    defaultValue = gameData.cpu_mark_score || 0;
                } else if (criterionLower.includes('price') || criterionLower.includes('harga')) {
                    defaultValue = (gameData.price_numeric / 100) || 0;
                } else if (criterionLower.includes('gpu') || criterionLower.includes('grafis')) {
                    defaultValue = gameData.gpu_g3d_score || 0;
                } else if (criterionLower.includes('rating')) {
                    defaultValue = gameData.rating_score || 0;
                } else if (criterionLower.includes('ram')) {
                    defaultValue = gameData.min_ram_gb || 0;
                } else if (criterionLower.includes('recommendations') || criterionLower.includes('reviews')) {
                    defaultValue = gameData.total_reviews || 0;
                } else if (criterionLower.includes('avg') && criterionLower.includes('player')) {
                    defaultValue = gameData.steamcharts_avg_30d || 0;
                } else if (criterionLower.includes('current') && criterionLower.includes('player')) {
                    defaultValue = gameData.steamcharts_current || 0;
                }
            }
            
            html += `<td><input type="number" id="value_${i}_${j}" value="${defaultValue}" step="0.01"></td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    
    document.getElementById('matrixContainer').innerHTML = html;
    
    let typeHtml = '';
    criteria.forEach((criterion, index) => {
        const criterionLower = criterion.toLowerCase();
        let defaultType = 'benefit';
        
        if (criterionLower.includes('harga') || criterionLower.includes('price') || 
            criterionLower.includes('cost') || criterionLower.includes('biaya')) {
            defaultType = 'cost';
        }
        
        if (criterionLower.includes('ram')) {
            defaultType = 'benefit';
        }

        typeHtml += `
            <div class="type-item">
                <label>${criterion}:</label>
                <select id="type_${index}">
                    <option value="benefit" ${defaultType === 'benefit' ? 'selected' : ''}>Benefit</option>
                    <option value="cost" ${defaultType === 'cost' ? 'selected' : ''}>Cost</option>
                </select>
            </div>
        `;
    });
    document.getElementById('typeSelector').innerHTML = typeHtml;
    
    document.getElementById('decisionMatrix').style.display = 'block';
}

function getDecisionMatrix() {
    const matrix = [];
    
    games.forEach((game, i) => {
        matrix[i] = [];
        criteria.forEach((_, j) => {
            const value = parseFloat(document.getElementById(`value_${i}_${j}`).value);
            matrix[i][j] = isNaN(value) ? 0 : value;
        });
    });
    
    return matrix;
}

function getCriteriaTypes() {
    const types = [];
    criteria.forEach((_, index) => {
        const select = document.getElementById(`type_${index}`);
        types.push(select.value);
    });
    return types;
}

async function calculateRanking() {
    const matrix = getDecisionMatrix();
    const types = getCriteriaTypes();
    
    try {
        const response = await fetch('/calculate_saw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                alternatives: games,
                criteria: criteria,
                weights: weights,
                decision_matrix: matrix,
                criteria_types: types
            })
        });
        
        const data = await response.json();
        
        if (data.success === true) {
            displayResults(data);
        } else if (data.success === false) {
            alert('Error: ' + data.error);
        } else {
            alert('Unexpected response format');
        }
    } catch (error) {
        alert('Error calculating ranking: ' + error);
    }
}

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    
    let html = '<h3>Final Ranking</h3>';
    
    data.ranking.forEach(item => {
        const rankClass = `rank-${item.rank}`;
        
        html += `
            <div class="ranking-item ${item.rank <= 3 ? rankClass : ''}">
                <div class="rank-badge">${item.rank}</div>
                <div class="game-name">${item.alternative}</div>
                <div class="game-score">${item.score.toFixed(4)}</div>
            </div>
        `;
    });
    
    html += '<div class="normalized-matrix">';
    html += '<h4>Normalized Decision Matrix</h4>';
    html += '<table><thead><tr><th>Game</th>';
    
    criteria.forEach(c => {
        html += `<th>${c}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    games.forEach((game, i) => {
        html += `<tr><th>${game}</th>`;
        criteria.forEach((_, j) => {
            html += `<td>${data.normalized_matrix[i][j].toFixed(4)}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}