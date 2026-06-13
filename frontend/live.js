// Live predikcije - TEST VERZIJA

const API_URL = 'http://localhost:5000/api';

const matchesGrid = document.getElementById('matchesGrid');
const refreshBtn = document.getElementById('refreshBtn');
const themeToggle = document.getElementById('themeToggle');
const lastUpdateSpan = document.getElementById('lastUpdate');
const loadingOverlay = document.getElementById('loadingOverlay');

let currentTheme = localStorage.getItem('theme') || 'light';
let selectedDate = 'today';
let autoRefreshInterval = null;

// Tema
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
}

function showLoading() { if (loadingOverlay) loadingOverlay.style.display = 'flex'; }
function hideLoading() { if (loadingOverlay) loadingOverlay.style.display = 'none'; }

function updateTimestamp() {
    const now = new Date();
    lastUpdateSpan.textContent = `Zadnje ažuriranje: ${now.toLocaleTimeString()}`;
}

// Dohvatanje podataka sa API-ja
async function loadLiveMatches() {
    showLoading();
    
    try {
        console.log('📡 Dohvatam podatke sa:', `${API_URL}/live-matches`);
        
        const response = await fetch(`${API_URL}/live-matches`);
        const data = await response.json();
        
        console.log('📊 Dobijeni podaci:', data);
        
        if (!data.matches || data.matches.length === 0) {
            matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-info-circle"></i><p>Nema dostupnih utakmica</p></div>`;
            hideLoading();
            return;
        }
        
        // Prikaži utakmice
        matchesGrid.innerHTML = '';
        
        for (const match of data.matches) {
            const statusText = match.status === 'finished' ? '✅ Završeno' : (match.status === 'live' ? '🔴 UŽIVO' : '📅 Ususret');
            const statusColor = match.status === 'finished' ? '#10b981' : (match.status === 'live' ? '#ef4444' : '#f59e0b');
            
            // Prikaz rezultata
            let scoreDisplay = '';
            if (match.status === 'finished' && match.home_goals !== undefined) {
                scoreDisplay = `
                    <div class="teams">
                        <div class="team">
                            <div class="team-name">${match.team1}</div>
                            <div class="team-score" style="font-size: 2rem; font-weight: 800;">${match.home_goals}</div>
                        </div>
                        <div class="vs">VS</div>
                        <div class="team">
                            <div class="team-name">${match.team2}</div>
                            <div class="team-score" style="font-size: 2rem; font-weight: 800;">${match.away_goals}</div>
                        </div>
                    </div>
                `;
            } else {
                scoreDisplay = `
                    <div class="teams">
                        <div class="team">
                            <div class="team-name">${match.team1}</div>
                            <div class="team-score">-</div>
                        </div>
                        <div class="vs">VS</div>
                        <div class="team">
                            <div class="team-name">${match.team2}</div>
                            <div class="team-score">-</div>
                        </div>
                    </div>
                `;
            }
            
            const matchCard = document.createElement('div');
            matchCard.className = 'match-card';
            matchCard.innerHTML = `
                <div class="match-header">
                    <span><i class="fas fa-calendar-alt"></i> ${match.date} | ${match.time || '--:--'}</span>
                    <span><i class="fas fa-users"></i> Grupa ${match.group || '?'}</span>
                </div>
                <div class="match-body">
                    <div class="match-status">
                        <span style="color: ${statusColor}">${statusText}</span>
                    </div>
                    ${scoreDisplay}
                    <div class="prediction-box" style="margin-top: 1rem; padding: 0.5rem; background: rgba(102,126,234,0.1); border-radius: 8px; text-align: center;">
                        <div class="prediction-text">
                            🤖 AI predviđa: <span class="prediction-winner">${match.winner || match.team1}</span>
                        </div>
                    </div>
                </div>
            `;
            matchesGrid.appendChild(matchCard);
        }
        
        updateTimestamp();
        
    } catch (error) {
        console.error('❌ Greška:', error);
        matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-exclamation-triangle"></i><p>Greška pri učitavanju: ${error.message}</p><button onclick="location.reload()" style="margin-top:1rem;padding:0.5rem 1rem;">Pokušaj ponovo</button></div>`;
    } finally {
        hideLoading();
    }
}

// Event listeneri
function setupEventListeners() {
    if (refreshBtn) refreshBtn.addEventListener('click', () => loadLiveMatches());
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
    
    const dateBtns = document.querySelectorAll('.date-btn');
    dateBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            dateBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedDate = btn.dataset.date;
            loadLiveMatches();
        });
    });
}

// Inicijalizacija
function init() {
    console.log('🚀 Live stranica inicijalizovana');
    loadTheme();
    setupEventListeners();
    loadLiveMatches();
    setInterval(() => loadLiveMatches(), 60000); // refresh svakih 60 sekundi
}

document.addEventListener('DOMContentLoaded', init);