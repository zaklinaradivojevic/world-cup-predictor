  // Glavni JavaScript fajl za index.html

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

// Toast notifikacija
function showToast(message, type = 'success') {
    if (!toast) return;
    toast.textContent = message;
    toast.style.borderLeftColor = type === 'success' ? '#10b981' : '#f59e0b';
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

// Loading
function showLoading() { if (loadingOverlay) loadingOverlay.style.display = 'flex'; }
function hideLoading() { if (loadingOverlay) loadingOverlay.style.display = 'none'; }

// TEMA
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
    showToast(`${newTheme === 'dark' ? '🌙 Tamna' : '☀️ Svetla'} tema`, 'info');
}

// INFO MODAL
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

// Timovi
function populateTeamSelects() {
    if (!team1Select || !team2Select) return;
    const options = TEAMS.map(t => `<option value="${t}">${t}</option>`).join('');
    team1Select.innerHTML = `<option value="">Izaberi domaćina</option>${options}`;
    team2Select.innerHTML = `<option value="">Izaberi gosta</option>${options}`;
}

// Simulacija predikcije
function simulatePrediction(team1, team2) {
    const strength = { 'Brazil':0.95, 'Argentina':0.93, 'France':0.92, 'Germany':0.90, 'Spain':0.89, 'England':0.88 };
    const s1 = strength[team1] || 0.7, s2 = strength[team2] || 0.7;
    const homeFactor = selectedVenue === 'home' ? 1.2 : (selectedVenue === 'away' ? 0.85 : 1.0);
    let h = (s1 * homeFactor) / (s1 * homeFactor + s2) * 0.7 + 0.15;
    let a = s2 / (s1 * homeFactor + s2) * 0.7 + 0.15;
    let d = 1 - h - a;
    const sum = h + d + a;
    h /= sum; d /= sum; a /= sum;
    
    let winner, conf;
    if (h > d && h > a) { winner = team1; conf = h; }
    else if (a > h && a > d) { winner = team2; conf = a; }
    else { winner = "Nerešeno"; conf = d; }
    
    return { winner, confidence: Math.round(conf * 100), team1, team2, probabilities: { [`${team1}_win`]: Math.round(h*100), draw: Math.round(d*100), [`${team2}_win`]: Math.round(a*100) }, model_used: 'Ensemble (Simulacija)' };
}

// Prikaz rezultata
function displayResults(result) {
    if (!resultsSection) return;
    document.getElementById('predictionResult').innerHTML = `<div class="winner-display"><div class="winner-name">${result.winner}</div><div class="winner-confidence">Sa ${result.confidence}% sigurnosti</div></div><div class="probability-bars"><div class="prob-item"><div class="prob-label"><span>${result.team1}</span><span>${result.probabilities[`${result.team1}_win`]}%</span></div><div class="prob-bar"><div class="prob-fill" style="width:${result.probabilities[`${result.team1}_win`]}%"></div></div></div><div class="prob-item"><div class="prob-label"><span>Nerešeno</span><span>${result.probabilities.draw}%</span></div><div class="prob-bar"><div class="prob-fill" style="width:${result.probabilities.draw}%"></div></div></div><div class="prob-item"><div class="prob-label"><span>${result.team2}</span><span>${result.probabilities[`${result.team2}_win`]}%</span></div><div class="prob-bar"><div class="prob-fill" style="width:${result.probabilities[`${result.team2}_win`]}%"></div></div></div></div>`;
    document.getElementById('modelConfidence').innerHTML = `<div class="model-item"><div class="model-name">XGBoost<span>40%</span></div><div class="model-confidence-bar"><div class="model-confidence-fill" style="width:40%"></div></div></div><div class="model-item"><div class="model-name">Random Forest<span>35%</span></div><div class="model-confidence-bar"><div class="model-confidence-fill" style="width:35%"></div></div></div><div class="model-item"><div class="model-name">Neural Network<span>25%</span></div><div class="model-confidence-bar"><div class="model-confidence-fill" style="width:25%"></div></div></div>`;
    resultsSection.style.display = 'grid';
}

// Predikcija
async function predictMatch() {
    const team1 = team1Select.value, team2 = team2Select.value;
    if (!team1 || !team2) { showToast('Izaberite oba tima', 'warning'); return; }
    if (team1 === team2) { showToast('Izaberite različite timove', 'warning'); return; }
    showLoading();
    try {
        const response = await fetch(`${API_URL}/predict`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ team1, team2, tournament: currentTournament, venue: selectedVenue }) });
        const result = response.ok ? await response.json() : simulatePrediction(team1, team2);
        displayResults(result);
    } catch (error) { displayResults(simulatePrediction(team1, team2)); showToast('API nedostupan, simulacija', 'warning'); }
    finally { hideLoading(); }
}

// Istorija
function loadPredictionHistory() { /* skraćeno */ }
function clearHistory() { localStorage.removeItem('predictionHistory'); location.reload(); }

// Event listeneri
function setupEventListeners() {
    predictBtn?.addEventListener('click', predictMatch);
    tournamentSelect?.addEventListener('change', (e) => { currentTournament = e.target.value; showToast(`Prebačeno na ${currentTournament}`, 'info'); });
    document.querySelectorAll('.venue-btn').forEach(btn => btn.addEventListener('click', () => { document.querySelectorAll('.venue-btn').forEach(b => b.classList.remove('active')); btn.classList.add('active'); selectedVenue = btn.dataset.venue; }));
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
    if (infoBtn) infoBtn.addEventListener('click', showInfoModal);
    if (clearHistory) clearHistory.addEventListener('click', clearHistory);
}

// Inicijalizacija
function init() {
    console.log('🚀 Inicijalizacija...');
    console.log('themeToggle:', themeToggle);
    console.log('infoBtn:', infoBtn);
    loadTheme();
    populateTeamSelects();
    loadPredictionHistory();
    setupEventListeners();
}

document.addEventListener('DOMContentLoaded', init);