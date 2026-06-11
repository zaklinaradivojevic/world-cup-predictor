// Glavni JavaScript fajl za index.html

// API konfiguracija
const API_URL = 'http://localhost:5000/api';

// DOM elementi
const team1Select = document.getElementById('team1');
const team2Select = document.getElementById('team2');
const tournamentSelect = document.getElementById('tournamentSelect');
const predictBtn = document.getElementById('predictBtn');
const resultsSection = document.getElementById('resultsSection');
const themeToggle = document.getElementById('themeToggle');
const clearHistory = document.getElementById('clearHistory');
const toggleFeatures = document.getElementById('toggleFeatures');
const loadingOverlay = document.getElementById('loadingOverlay');
const toast = document.getElementById('toast');

// Lista timova (mock - za početak)
const TEAMS = [
    "Brazil", "Argentina", "France", "Germany", "Spain", "England",
    "Netherlands", "Portugal", "Belgium", "Croatia", "Italy", "Uruguay",
    "Mexico", "USA", "Japan", "Morocco", "Senegal", "Australia",
    "South Africa", "South Korea", "Colombia", "Switzerland", "Poland",
    "Netherlands", "Chile", "Nigeria", "Sweden", "Denmark"
];

let currentTournament = 'World Cup';
let selectedVenue = 'home';

// ============ POMOĆNE FUNKCIJE ============

function showToast(message, type = 'success') {
    if (!toast) return;
    
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    
    toast.textContent = message;
    toast.style.borderLeftColor = colors[type];
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

function showLoading() {
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
}

function hideLoading() {
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

// ============ TEMA ============

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    const icon = themeToggle?.querySelector('i');
    if (icon) {
        icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const icon = themeToggle.querySelector('i');
    icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    showToast(`${newTheme === 'dark' ? '🌙 Tamna' : '☀️ Svetla'} tema aktivirana`, 'info');
}

// ============ TIMOVI ============

function populateTeamSelects() {
    if (!team1Select || !team2Select) return;
    
    const options = TEAMS.map(team => `<option value="${team}">${team}</option>`).join('');
    
    team1Select.innerHTML = `<option value="">Izaberi domaćina</option>${options}`;
    team2Select.innerHTML = `<option value="">Izaberi gosta</option>${options}`;
}

// ============ PREDIKCIJA ============

async function predictMatch() {
    const team1 = team1Select.value;
    const team2 = team2Select.value;
    
    if (!team1 || !team2) {
        showToast('Molimo izaberite oba tima', 'warning');
        return;
    }
    
    if (team1 === team2) {
        showToast('Izaberite različite timove', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        // Pokušaj sa API-jem
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                team1, team2, 
                tournament: currentTournament, 
                venue: selectedVenue 
            })
        });
        
        let result;
        if (response.ok) {
            result = await response.json();
        } else {
            // Fallback: simulacija ako API ne radi
            result = simulatePrediction(team1, team2);
        }
        
        displayResults(result);
        addToRecentPredictions(team1, team2, result.winner, result.confidence);
        
    } catch (error) {
        console.error('Greška:', error);
        // Simulacija ako API ne radi
        const simulated = simulatePrediction(team1, team2);
        displayResults(simulated);
        addToRecentPredictions(team1, team2, simulated.winner, simulated.confidence);
        showToast('API nije dostupan, prikazujem simulirane podatke', 'warning');
    } finally {
        hideLoading();
    }
}

function simulatePrediction(team1, team2) {
    // Realistična simulacija na osnovu jačine timova
    const teamStrength = {
        'Brazil': 0.95, 'Argentina': 0.93, 'France': 0.92, 'Germany': 0.90,
        'Spain': 0.89, 'England': 0.88, 'Netherlands': 0.85, 'Portugal': 0.84,
        'Belgium': 0.83, 'Croatia': 0.80, 'Italy': 0.82, 'Uruguay': 0.78,
        'Mexico': 0.75, 'USA': 0.74, 'Japan': 0.72, 'Morocco': 0.70,
        'Senegal': 0.68, 'Australia': 0.65, 'South Africa': 0.60
    };
    
    const strength1 = teamStrength[team1] || 0.70;
    const strength2 = teamStrength[team2] || 0.70;
    
    // Faktor domaćeg terena
    const homeFactor = selectedVenue === 'home' ? 1.2 : (selectedVenue === 'away' ? 0.85 : 1.0);
    
    const adjustedStrength1 = strength1 * homeFactor;
    const total = adjustedStrength1 + strength2;
    
    let homeWinProb = (adjustedStrength1 / total) * 0.7 + 0.15;
    let awayWinProb = (strength2 / total) * 0.7 + 0.15;
    let drawProb = 1 - homeWinProb - awayWinProb;
    
    // Normalizacija
    const sum = homeWinProb + drawProb + awayWinProb;
    homeWinProb = homeWinProb / sum;
    drawProb = drawProb / sum;
    awayWinProb = awayWinProb / sum;
    
    let winner, confidence;
    if (homeWinProb > drawProb && homeWinProb > awayWinProb) {
        winner = team1;
        confidence = homeWinProb;
    } else if (awayWinProb > homeWinProb && awayWinProb > drawProb) {
        winner = team2;
        confidence = awayWinProb;
    } else {
        winner = "Nerešeno";
        confidence = drawProb;
    }
    
    return {
        winner: winner,
        confidence: Math.round(confidence * 100),
        team1: team1,
        team2: team2,
        probabilities: {
            [`${team1}_win`]: Math.round(homeWinProb * 100),
            draw: Math.round(drawProb * 100),
            [`${team2}_win`]: Math.round(awayWinProb * 100)
        },
        model_used: 'Ensemble (Simulacija)'
    };
}

function displayResults(result) {
    if (!resultsSection) return;
    
    const predictionResult = document.getElementById('predictionResult');
    const modelConfidence = document.getElementById('modelConfidence');
    
    // Prikaz pobednika
    predictionResult.innerHTML = `
        <div class="winner-display animate-scaleIn">
            <div class="winner-label">
                <i class="fas fa-robot"></i> Ensemble Model Predikcija
            </div>
            <div class="winner-name">${result.winner}</div>
            <div class="winner-confidence">
                Sa ${result.confidence}% sigurnosti
            </div>
            <div style="margin-top: 1rem; font-size: 0.85rem; color: var(--text-secondary);">
                <i class="fas fa-microchip"></i> Model: ${result.model_used || 'XGBoost+RF+NN'}
            </div>
        </div>
        
        <div class="probability-bars">
            <div class="prob-item animate-slideInLeft">
                <div class="prob-label">
                    <span><i class="fas fa-home"></i> ${result.team1}</span>
                    <span>${result.probabilities[`${result.team1}_win`]}%</span>
                </div>
                <div class="prob-bar">
                    <div class="prob-fill" style="width: 0%">
                        ${result.probabilities[`${result.team1}_win`] > 25 ? `${result.probabilities[`${result.team1}_win`]}%` : ''}
                    </div>
                </div>
            </div>
            
            <div class="prob-item animate-scaleIn">
                <div class="prob-label">
                    <span><i class="fas fa-handshake"></i> Nerešeno</span>
                    <span>${result.probabilities.draw}%</span>
                </div>
                <div class="prob-bar">
                    <div class="prob-fill" style="width: 0%; background: linear-gradient(90deg, #f59e0b, #ef4444);">
                        ${result.probabilities.draw > 25 ? `${result.probabilities.draw}%` : ''}
                    </div>
                </div>
            </div>
            
            <div class="prob-item animate-slideInRight">
                <div class="prob-label">
                    <span><i class="fas fa-plane-departure"></i> ${result.team2}</span>
                    <span>${result.probabilities[`${result.team2}_win`]}%</span>
                </div>
                <div class="prob-bar">
                    <div class="prob-fill" style="width: 0%">
                        ${result.probabilities[`${result.team2}_win`] > 25 ? `${result.probabilities[`${result.team2}_win`]}%` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Prikaz modela
    modelConfidence.innerHTML = `
        <div class="model-item animate-fadeInUp">
            <div class="model-name">
                <span><i class="fas fa-microchip"></i> XGBoost (Tunirani)</span>
                <span>40% težina</span>
            </div>
            <div class="model-confidence-bar">
                <div class="model-confidence-fill" style="width: 0%; background: #667eea">
                    Active
                </div>
            </div>
        </div>
        <div class="model-item animate-fadeInUp">
            <div class="model-name">
                <span><i class="fas fa-tree"></i> Random Forest</span>
                <span>35% težina</span>
            </div>
            <div class="model-confidence-bar">
                <div class="model-confidence-fill" style="width: 0%; background: #f093fb">
                    Active
                </div>
            </div>
        </div>
        <div class="model-item animate-fadeInUp">
            <div class="model-name">
                <span><i class="fas fa-brain"></i> Neural Network</span>
                <span>25% težina</span>
            </div>
            <div class="model-confidence-bar">
                <div class="model-confidence-fill" style="width: 0%; background: #f5576c">
                    Active
                </div>
            </div>
        </div>
    `;
    
    // Animacija progress bar-ova
    setTimeout(() => {
        const fills = document.querySelectorAll('.prob-fill');
        fills.forEach((fill, index) => {
            const targetWidth = fill.parentElement.parentElement.querySelector('.prob-label span:last-child').textContent;
            fill.style.width = targetWidth;
        });
        
        const modelFills = document.querySelectorAll('.model-confidence-fill');
        if (modelFills[0]) modelFills[0].style.width = '40%';
        if (modelFills[1]) modelFills[1].style.width = '35%';
        if (modelFills[2]) modelFills[2].style.width = '25%';
    }, 100);
    
    resultsSection.style.display = 'grid';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// ============ ISTORIJA PREDIKCIJA ============

function addToRecentPredictions(team1, team2, winner, confidence) {
    const container = document.getElementById('recentPredictions');
    if (!container) return;
    
    // Ukloni empty state
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) emptyState.remove();
    
    const recentItem = document.createElement('div');
    recentItem.className = 'recent-item animate-slideInLeft';
    recentItem.innerHTML = `
        <div class="recent-match">
            <div class="recent-teams">${team1} vs ${team2}</div>
            <div class="recent-vs">• ${currentTournament}</div>
        </div>
        <div>
            <span class="recent-winner">🏆 ${winner}</span>
            <span class="recent-confidence">(${confidence}%)</span>
        </div>
    `;
    
    container.insertBefore(recentItem, container.firstChild);
    
    // Sačuvaj u localStorage
    let history = JSON.parse(localStorage.getItem('predictionHistory') || '[]');
    history.unshift({ team1, team2, winner, confidence, tournament: currentTournament, timestamp: Date.now() });
    history = history.slice(0, 20);
    localStorage.setItem('predictionHistory', JSON.stringify(history));
}

function loadPredictionHistory() {
    const history = JSON.parse(localStorage.getItem('predictionHistory') || '[]');
    const container = document.getElementById('recentPredictions');
    if (!container) return;
    
    if (history.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-chart-simple"></i>
                <p>Još uvek nema predikcija</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = history.map(pred => `
        <div class="recent-item animate-fadeInUp">
            <div class="recent-match">
                <div class="recent-teams">${pred.team1} vs ${pred.team2}</div>
                <div class="recent-vs">• ${pred.tournament}</div>
            </div>
            <div>
                <span class="recent-winner">🏆 ${pred.winner}</span>
                <span class="recent-confidence">(${pred.confidence}%)</span>
            </div>
        </div>
    `).join('');
}

function clearHistory() {
    localStorage.removeItem('predictionHistory');
    loadPredictionHistory();
    showToast('Istorija predikcija obrisana', 'info');
}

// ============ EVENT LISTENERI ============

function setupEventListeners() {
    if (predictBtn) {
        predictBtn.addEventListener('click', predictMatch);
    }
    
    if (tournamentSelect) {
        tournamentSelect.addEventListener('change', (e) => {
            currentTournament = e.target.value;
            showToast(`Prebačeno na ${currentTournament}`, 'info');
        });
    }
    
    const venueBtns = document.querySelectorAll('.venue-btn');
    venueBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            venueBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedVenue = btn.dataset.venue;
        });
    });
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    if (clearHistory) {
        clearHistory.addEventListener('click', clearHistory);
    }
    
    if (toggleFeatures) {
        toggleFeatures.addEventListener('click', () => {
            const content = document.getElementById('featuresContent');
            const icon = toggleFeatures.querySelector('i');
            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            } else {
                content.style.display = 'none';
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            }
        });
    }
}

// ============ INICIJALIZACIJA ============

function init() {
    console.log('🚀 AI Football Predictor inicijalizovan');
    loadTheme();
    populateTeamSelects();
    loadPredictionHistory();
    setupEventListeners();
}

// Pokreni kad je DOM spreman
document.addEventListener('DOMContentLoaded', init);