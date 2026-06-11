// Tournament Simulator JavaScript
const API_URL = 'http://localhost:5000/api';

// DOM elementi
const simulateBtn = document.getElementById('simulateBtn');
const simulateGroupOnlyBtn = document.getElementById('simulateGroupOnlyBtn');
const numSimulationsInput = document.getElementById('numSimulations');
const loadingOverlay = document.getElementById('loadingOverlay');
const themeToggle = document.getElementById('themeToggle');

// Stanje
let currentTheme = localStorage.getItem('theme') || 'light';

// Inicijalizacija
function init() {
    loadTheme();
    setupEventListeners();
}

// Tema
function loadTheme() {
    document.documentElement.setAttribute('data-theme', currentTheme);
    const icon = themeToggle?.querySelector('i');
    if (icon) {
        icon.className = currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', currentTheme);
    loadTheme();
}

// Prikaz/sakrivanje loading-a
function showLoading() {
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// Prikazivanje rezultata grupne faze
function displayGroupStage(groups) {
    const container = document.getElementById('groupsGrid');
    container.innerHTML = '';
    
    for (const [groupName, groupData] of Object.entries(groups)) {
        const groupCard = document.createElement('div');
        groupCard.className = 'group-card';
        
        let tableHtml = `
            <div class="group-header">Grupa ${groupName}</div>
            <table class="group-table">
                <thead>
                    <tr><th>Tim</th><th>Uta</th><th>Pob</th><th>Ner</th><th>Izg</th><th>G+</th><th>G-</th><th>Bod</th></tr>
                </thead>
                <tbody>
        `;
        
        const sortedTeams = Object.entries(groupData.table || {})
            .sort((a, b) => b[1].points - a[1].points || b[1].gd - a[1].gd);
        
        for (const [team, stats] of sortedTeams) {
            const isQualified = groupData.qualified?.includes(team);
            tableHtml += `
                <tr class="${isQualified ? 'qualified' : ''}">
                    <td><strong>${team}</strong> ${isQualified ? '✅' : ''}</td>
                    <td>${stats.played || stats.wins + stats.draws + stats.losses || 0}</td>
                    <td>${stats.wins || 0}</td>
                    <td>${stats.draws || 0}</td>
                    <td>${stats.losses || 0}</td>
                    <td>${stats.gf || stats.goals_for || 0}</td>
                    <td>${stats.ga || stats.goals_against || 0}</td>
                    <td><strong>${stats.points || 0}</strong></td>
                </tr>
            `;
        }
        
        tableHtml += `</tbody></table>`;
        groupCard.innerHTML = tableHtml;
        container.appendChild(groupCard);
    }
    
    document.getElementById('groupStageSection').style.display = 'block';
}

// Prikazivanje šansi za titulu
function displayProbabilities(probabilities, totalSimulations) {
    const container = document.getElementById('probabilitiesList');
    container.innerHTML = '';
    
    const sorted = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);
    
    for (const [team, wins] of sorted.slice(0, 10)) {
        const percentage = (wins / totalSimulations * 100).toFixed(1);
        
        const probItem = document.createElement('div');
        probItem.className = 'prob-item';
        probItem.innerHTML = `
            <div class="prob-label">
                <span><strong>${team}</strong></span>
                <span>${percentage}%</span>
            </div>
            <div class="prob-bar">
                <div class="prob-fill" style="width: 0%; background: linear-gradient(90deg, #FFD700, #FFA500);">
                    ${percentage > 15 ? percentage + '%' : ''}
                </div>
            </div>
        `;
        container.appendChild(probItem);
        
        // Animacija
        setTimeout(() => {
            const fill = probItem.querySelector('.prob-fill');
            fill.style.width = percentage + '%';
        }, 100);
    }
    
    // Prikaži pobednika
    if (sorted.length > 0) {
        const champion = sorted[0][0];
        const championWins = sorted[0][1];
        const championProb = (championWins / totalSimulations * 100).toFixed(1);
        
        document.getElementById('championName').textContent = champion;
        document.getElementById('championProb').textContent = `Sa ${championProb}% šansi za titulu`;
        document.getElementById('championSection').style.display = 'block';
    }
    
    document.getElementById('probabilitiesSection').style.display = 'block';
}

// Prikazivanje statistike
function displayStats(totalSimulations, totalMatches, accuracy) {
    document.getElementById('totalSimulations').textContent = totalSimulations;
    document.getElementById('totalMatches').textContent = totalMatches || (totalSimulations * 63);
    document.getElementById('avgAccuracy').textContent = accuracy || '78%';
    document.getElementById('statsSummary').style.display = 'grid';
}

// Simulacija grupne faze
async function simulateGroupStage() {
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/simulate-group-stage`);
        const data = await response.json();
        
        displayGroupStage(data);
        
        // Sakrij sekcije koje nisu relevantne
        document.getElementById('probabilitiesSection').style.display = 'none';
        document.getElementById('championSection').style.display = 'none';
        document.getElementById('bracketSection').style.display = 'none';
        
    } catch (error) {
        console.error('Greška:', error);
        alert('Došlo je do greške pri simulaciji grupne faze. Proverite da li je API pokrenut.');
    } finally {
        hideLoading();
    }
}

// Kompletna turnirska simulacija
async function simulateTournament() {
    const numSimulations = parseInt(numSimulationsInput.value) || 100;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/simulate-tournament`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ num_simulations: numSimulations })
        });
        
        const data = await response.json();
        
        // Prikaži rezultate
        if (data.group_results) {
            displayGroupStage(data.group_results);
        }
        
        if (data.championship_probabilities) {
            displayProbabilities(data.championship_probabilities, numSimulations);
        }
        
        displayStats(numSimulations, data.total_matches, data.avg_accuracy);
        
        // Prikaži bracket ako postoji
        if (data.knockout_bracket) {
            displayBracket(data.knockout_bracket);
        }
        
    } catch (error) {
        console.error('Greška:', error);
        alert('Došlo je do greške pri simulaciji turnira. Proverite da li je API pokrenut.');
    } finally {
        hideLoading();
    }
}

// Prikazivanje bracket-a (nokaut faze)
function displayBracket(bracket) {
    const container = document.getElementById('bracketContainer');
    container.innerHTML = '';
    
    const rounds = ['Round of 32', 'Round of 16', 'Quarterfinals', 'Semifinals', 'Final'];
    
    for (const roundName of rounds) {
        const matches = bracket[roundName] || [];
        if (matches.length === 0) continue;
        
        const roundDiv = document.createElement('div');
        roundDiv.className = 'round';
        roundDiv.innerHTML = `<div class="round-title">${roundName}</div>`;
        
        for (const match of matches) {
            const matchDiv = document.createElement('div');
            matchDiv.className = 'match';
            matchDiv.innerHTML = `
                <div class="match-teams">
                    <span>${match.team1 || '???'}</span>
                    <span>vs</span>
                    <span>${match.team2 || '???'}</span>
                </div>
                <div class="match-winner">
                    🏆 Pobednik: ${match.winner || '???'}
                </div>
            `;
            roundDiv.appendChild(matchDiv);
        }
        
        container.appendChild(roundDiv);
    }
    
    document.getElementById('bracketSection').style.display = 'block';
}

// Event listeneri
function setupEventListeners() {
    if (simulateBtn) {
        simulateBtn.addEventListener('click', simulateTournament);
    }
    
    if (simulateGroupOnlyBtn) {
        simulateGroupOnlyBtn.addEventListener('click', simulateGroupStage);
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

// Pokreni inicijalizaciju
document.addEventListener('DOMContentLoaded', init);