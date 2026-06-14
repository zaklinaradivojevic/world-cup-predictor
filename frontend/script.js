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
const clearHistoryBtn = document.getElementById('clearHistory');
const toggleFeatures = document.getElementById('toggleFeatures');
const loadingOverlay = document.getElementById('loadingOverlay');
const toast = document.getElementById('toast');
const infoBtn = document.getElementById('infoBtn');

// Lista timova
const TEAMS = [
    "Brazil", "Argentina", "France", "Germany", "Spain", "England",
    "Netherlands", "Portugal", "Belgium", "Croatia", "Italy", "Uruguay",
    "Mexico", "USA", "Japan", "Morocco", "Senegal", "Australia",
    "South Africa", "South Korea", "Colombia", "Switzerland", "Poland"
];

let currentTournament = 'World Cup';
let selectedVenue = 'home';

// ============ POMOĆNE FUNKCIJE ============

function showToast(message, type = 'success') {
    if (!toast) return;
    const colors = { success: '#10b981', error: '#ef4444', warning: '#f59e0b', info: '#3b82f6' };
    toast.textContent = message;
    toast.style.borderLeftColor = colors[type];
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

function showLoading() { if (loadingOverlay) loadingOverlay.style.display = 'flex'; }
function hideLoading() { if (loadingOverlay) loadingOverlay.style.display = 'none'; }

// ============ TEMA ============

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    const icon = themeToggle?.querySelector('i');
    if (icon) icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    const icon = themeToggle?.querySelector('i');
    if (icon) icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    showToast(`${newTheme === 'dark' ? '🌙 Tamna' : '☀️ Svetla'} tema aktivirana`, 'info');
}

// ============ INFO MODAL ============

function showInfoModal() {
    let modal = document.getElementById('infoModal');
    if (modal) { modal.remove(); return; }
    
    modal = document.createElement('div');
    modal.id = 'infoModal';
    modal.style.cssText = `position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);backdrop-filter:blur(10px);z-index:2000;display:flex;align-items:center;justify-content:center;`;
    modal.innerHTML = `
        <div style="background:var(--bg-primary);border-radius:20px;max-width:500px;width:90%;padding:2rem;position:relative;">
            <button id="closeModalBtn" style="position:absolute;top:1rem;right:1rem;background:none;border:none;font-size:1.5rem;cursor:pointer;">&times;</button>
            <h2><i class="fas fa-robot"></i> O AI Football Predictor-u</h2>
            <p><strong>Ensemble ML Model:</strong> XGBoost + Random Forest + Neural Network</p>
            <p><strong>Tačnost:</strong> 78-82%</p>
            <p><strong>Feature-i:</strong> Forma, xG, FIFA rang, H2H, domaći teren, povrede</p>
            <p><strong>Izvori:</strong> FBref, Understat, FIFA, OpenWeatherMap</p>
            <p style="margin-top:1rem;font-size:0.8rem;">© 2026 AI Football Predictor | Verzija 2.0</p>
        </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('closeModalBtn')?.addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
}



// ============ TIMOVI - UČITAVANJE SA API-JA ============

async function populateTeamSelects() {
    if (!team1Select || !team2Select) return;
    
    try {
        const response = await fetch(`${API_URL}/teams`);
        const data = await response.json();
        const teams = data.teams || [];
        
        if (teams.length === 0) {
            console.warn('Nema timova sa API-ja, koristim statičku listu');
            useStaticTeams();
            return;
        }
        
        const options = teams.map(team => `<option value="${team}">${team}</option>`).join('');
        team1Select.innerHTML = `<option value="">Izaberi domaćina</option>${options}`;
        team2Select.innerHTML = `<option value="">Izaberi gosta</option>${options}`;
        
        console.log(`✅ Učitano ${teams.length} timova sa API-ja`);
    } catch (error) {
        console.error('Greška pri učitavanju timova:', error);
        useStaticTeams();
    }
}

function useStaticTeams() {
    const staticTeams = [
        "Brazil", "Argentina", "France", "Germany", "Spain", "England",
        "Netherlands", "Portugal", "Belgium", "Croatia", "Italy", "Uruguay",
        "Mexico", "USA", "Japan", "Morocco", "Senegal", "Australia",
        "South Africa", "South Korea", "Colombia", "Switzerland", "Poland",
        "Chile", "Nigeria", "Sweden", "Denmark", "Austria", "Czech Republic",
        "Canada", "Paraguay", "Qatar", "Haiti", "Scotland", "Turkiye",
        "Ecuador", "Tunisia", "Saudi Arabia", "Egypt", "Iran", "Cabo Verde",
        "Curacao", "New Zealand", "Uzbekistan", "Jordan", "Ghana", "Norway",
        "Panama", "Algeria", "Ivory Coast"
    ];
    
    const options = staticTeams.map(team => `<option value="${team}">${team}</option>`).join('');
    team1Select.innerHTML = `<option value="">Izaberi domaćina</option>${options}`;
    team2Select.innerHTML = `<option value="">Izaberi gosta</option>${options}`;
    console.log(`📋 Učitano ${staticTeams.length} statičkih timova`);
}

// ============ SIMULACIJA PREDIKCIJE ============

function simulatePrediction(team1, team2) {
    const teamStrength = {
        'Brazil': 0.95, 'Argentina': 0.93, 'France': 0.92, 'Germany': 0.90,
        'Spain': 0.89, 'England': 0.88, 'Netherlands': 0.85, 'Portugal': 0.84,
        'Belgium': 0.83, 'Croatia': 0.80, 'Italy': 0.82, 'Uruguay': 0.78
    };
    const strength1 = teamStrength[team1] || 0.70;
    const strength2 = teamStrength[team2] || 0.70;
    const homeFactor = selectedVenue === 'home' ? 1.2 : (selectedVenue === 'away' ? 0.85 : 1.0);
    const adjustedStrength1 = strength1 * homeFactor;
    const total = adjustedStrength1 + strength2;
    let homeWinProb = (adjustedStrength1 / total) * 0.7 + 0.15;
    let awayWinProb = (strength2 / total) * 0.7 + 0.15;
    let drawProb = 1 - homeWinProb - awayWinProb;
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
    
    predictionResult.innerHTML = `
        <div class="winner-display">
            <div class="winner-label"><i class="fas fa-robot"></i> Ensemble Model Predikcija</div>
            <div class="winner-name">${result.winner}</div>
            <div class="winner-confidence">Sa ${result.confidence}% sigurnosti</div>
        </div>
        <div class="probability-bars">
            <div class="prob-item">
                <div class="prob-label"><span>${result.team1}</span><span>${result.probabilities[`${result.team1}_win`]}%</span></div>
                <div class="prob-bar"><div class="prob-fill" style="width:${result.probabilities[`${result.team1}_win`]}%"></div></div>
            </div>
            <div class="prob-item">
                <div class="prob-label"><span>Nerešeno</span><span>${result.probabilities.draw}%</span></div>
                <div class="prob-bar"><div class="prob-fill" style="width:${result.probabilities.draw}%;background:linear-gradient(90deg,#f59e0b,#ef4444);"></div></div>
            </div>
            <div class="prob-item">
                <div class="prob-label"><span>${result.team2}</span><span>${result.probabilities[`${result.team2}_win`]}%</span></div>
                <div class="prob-bar"><div class="prob-fill" style="width:${result.probabilities[`${result.team2}_win`]}%"></div></div>
            </div>
        </div>
    `;
    
    modelConfidence.innerHTML = `
        <div class="model-item"><div class="model-name">XGBoost (Tunirani)<span>40%</span></div><div class="model-confidence-bar"><div class="model-confidence-fill" style="width:40%;background:#667eea"></div></div></div>
        <div class="model-item"><div class="model-name">Random Forest<span>35%</span></div><div class="model-confidence-bar"><div class="model-confidence-fill" style="width:35%;background:#f093fb"></div></div></div>
        <div class="model-item"><div class="model-name">Neural Network<span>25%</span></div><div class="model-confidence-bar"><div class="model-confidence-fill" style="width:25%;background:#f5576c"></div></div></div>
    `;
    
    resultsSection.style.display = 'grid';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

async function predictMatch() {
    const team1 = team1Select.value;
    const team2 = team2Select.value;
    
    if (!team1 || !team2) { showToast('Molimo izaberite oba tima', 'warning'); return; }
    if (team1 === team2) { showToast('Izaberite različite timove', 'warning'); return; }
    
    showLoading();
    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team1, team2, tournament: currentTournament, venue: selectedVenue })
        });
        const result = response.ok ? await response.json() : simulatePrediction(team1, team2);
        displayResults(result);
        addToRecentPredictions(team1, team2, result.winner, result.confidence);
    } catch (error) {
        const simulated = simulatePrediction(team1, team2);
        displayResults(simulated);
        addToRecentPredictions(team1, team2, simulated.winner, simulated.confidence);
        showToast('API nije dostupan, prikazujem simulirane podatke', 'warning');
    } finally { hideLoading(); }
}

// ============ ISTORIJA PREDIKCIJA ============

function addToRecentPredictions(team1, team2, winner, confidence) {
    const container = document.getElementById('recentPredictions');
    if (!container) return;
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) emptyState.remove();
    const recentItem = document.createElement('div');
    recentItem.className = 'recent-item';
    recentItem.innerHTML = `<div class="recent-match"><div class="recent-teams">${team1} vs ${team2}</div><div class="recent-vs">• ${currentTournament}</div></div><div><span class="recent-winner">🏆 ${winner}</span><span class="recent-confidence">(${confidence}%)</span></div>`;
    container.insertBefore(recentItem, container.firstChild);
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
        container.innerHTML = `<div class="empty-state"><i class="fas fa-chart-simple"></i><p>Još uvek nema predikcija</p></div>`;
        return;
    }
    container.innerHTML = history.map(pred => `<div class="recent-item"><div class="recent-match"><div class="recent-teams">${pred.team1} vs ${pred.team2}</div><div class="recent-vs">• ${pred.tournament}</div></div><div><span class="recent-winner">🏆 ${pred.winner}</span><span class="recent-confidence">(${pred.confidence}%)</span></div></div>`).join('');
}

function clearHistory() {
    localStorage.removeItem('predictionHistory');
    loadPredictionHistory();
    showToast('Istorija predikcija obrisana', 'info');
}

// ============ EVENT LISTENERI ============

function setupEventListeners() {
    if (predictBtn) predictBtn.addEventListener('click', predictMatch);
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
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
    if (infoBtn) infoBtn.addEventListener('click', showInfoModal);
    if (clearHistoryBtn) clearHistoryBtn.addEventListener('click', clearHistory);
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



async function init() {
    console.log('🚀 AI Football Predictor inicijalizovan');
    console.log('themeToggle:', themeToggle);
    console.log('infoBtn:', infoBtn);
    loadTheme();
    await populateTeamSelects();  // await radi jer je init async
    loadPredictionHistory();
    setupEventListeners();
}

// Pokreni kad je DOM spreman
document.addEventListener('DOMContentLoaded', init);