// Live predikcije JavaScript
const API_URL = 'http://localhost:5000/api';

// DOM elementi
const matchesGrid = document.getElementById('matchesGrid');
const refreshBtn = document.getElementById('refreshBtn');
const themeToggle = document.getElementById('themeToggle');
const lastUpdateSpan = document.getElementById('lastUpdate');
const loadingOverlay = document.getElementById('loadingOverlay');

// Stanje
let currentTheme = localStorage.getItem('theme') || 'light';
let selectedDate = 'today';
let autoRefreshInterval = null;
let isUpdating = false;

// Lista timova (mock - u produkciji bi se učitavala sa API-ja)
const TEAMS = [
    "Brazil", "Argentina", "France", "Germany", "Spain", "England",
    "Netherlands", "Portugal", "Belgium", "Croatia", "Italy", "Uruguay",
    "Mexico", "USA", "Japan", "Morocco", "Senegal", "Australia",
    "South Africa", "South Korea", "Colombia", "Switzerland", "Poland"
];

// Datumi utakmica SP 2026
const MATCH_SCHEDULE = [
    { date: "2026-06-11", team1: "Mexico", team2: "South Africa", venue: "neutral", time: "18:00", group: "A" },
    { date: "2026-06-11", team1: "Germany", team2: "New Zealand", venue: "neutral", time: "21:00", group: "A" },
    { date: "2026-06-12", team1: "Brazil", team2: "Portugal", venue: "neutral", time: "18:00", group: "B" },
    { date: "2026-06-12", team1: "USA", team2: "Saudi Arabia", venue: "neutral", time: "21:00", group: "B" },
    { date: "2026-06-13", team1: "France", team2: "Denmark", venue: "neutral", time: "18:00", group: "C" },
    { date: "2026-06-13", team1: "Japan", team2: "Ecuador", venue: "neutral", time: "21:00", group: "C" },
    { date: "2026-06-14", team1: "Argentina", team2: "Croatia", venue: "neutral", time: "18:00", group: "D" },
    { date: "2026-06-14", team1: "Australia", team2: "Canada", venue: "neutral", time: "21:00", group: "D" }
];

// Inicijalizacija
function init() {
    loadTheme();
    setupEventListeners();
    loadLiveMatches();
    startAutoRefresh();
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

// Auto-refresh na 30 sekundi
function startAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    autoRefreshInterval = setInterval(() => {
        if (!isUpdating) {
            loadLiveMatches(true);
        }
    }, 30000);
}

// Prikaz/sakrivanje loading-a
function showLoading() {
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// Ažuriranje vremena
function updateTimestamp() {
    const now = new Date();
    lastUpdateSpan.textContent = `Zadnje ažuriranje: ${now.toLocaleTimeString()}`;
}

// Filtriranje utakmica po datumu
function filterMatchesByDate(matches) {
    const today = new Date().toISOString().split('T')[0];
    const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
    
    if (selectedDate === 'today') {
        return matches.filter(m => m.date === today);
    } else if (selectedDate === 'tomorrow') {
        return matches.filter(m => m.date === tomorrow);
    }
    return matches;
}

// Simulacija predikcije za utakmicu (dok API nije spreman)
async function getPredictionForMatch(team1, team2, venue) {
    // Pokušaj sa API-jem
    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team1, team2, venue, tournament: 'World Cup' })
        });
        
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.log('API nije dostupan, koristim simulaciju');
    }
    
    // Fallback: simulacija (dok API ne radi)
    const homeWinProb = 0.35 + Math.random() * 0.4;
    const drawProb = 0.2 + Math.random() * 0.2;
    const awayWinProb = 1 - homeWinProb - drawProb;
    
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
        probabilities: {
            [`${team1}_win`]: Math.round(homeWinProb * 100),
            draw: Math.round(drawProb * 100),
            [`${team2}_win`]: Math.round(awayWinProb * 100)
        }
    };
}

// Određivanje statusa utakmice
function getMatchStatus(matchDate, matchTime) {
    const now = new Date();
    const matchDateTime = new Date(`${matchDate}T${matchTime || '18:00'}:00`);
    const matchEnd = new Date(matchDateTime.getTime() + 2 * 60 * 60 * 1000); // +2h
    
    if (now < matchDateTime) return { status: 'upcoming', text: '📅 Ususret', color: '#f59e0b' };
    if (now >= matchDateTime && now <= matchEnd) return { status: 'live', text: '🔴 UŽIVO', color: '#ef4444' };
    return { status: 'finished', text: '✅ Završeno', color: '#10b981' };
}

// Prikazivanje utakmica
async function displayMatches(matches, silent = false) {
    if (!silent) showLoading();
    
    const filteredMatches = filterMatchesByDate(matches);
    
    if (filteredMatches.length === 0) {
        matchesGrid.innerHTML = `
            <div class="no-matches">
                <i class="fas fa-calendar-day"></i>
                <p>Nema utakmica za izabrani datum</p>
            </div>
        `;
        if (!silent) hideLoading();
        return;
    }
    
    matchesGrid.innerHTML = '';
    
    for (const match of filteredMatches) {
        const prediction = await getPredictionForMatch(match.team1, match.team2, match.venue);
        const matchStatus = getMatchStatus(match.date, match.time);
        
        const matchCard = document.createElement('div');
        matchCard.className = `match-card ${matchStatus.status === 'live' ? 'live' : ''}`;
        
        // Verovatnoće za prikaz
        const team1Prob = prediction.probabilities[`${match.team1}_win`] || 33;
        const drawProb = prediction.probabilities.draw || 33;
        const team2Prob = prediction.probabilities[`${match.team2}_win`] || 34;
        
        matchCard.innerHTML = `
            <div class="match-header">
                <span><i class="fas fa-calendar-alt"></i> ${match.date} | ${match.time}</span>
                <span><i class="fas fa-users"></i> Grupa ${match.group}</span>
            </div>
            <div class="match-body">
                <div class="match-status">
                    <span class="status-${matchStatus.status}" style="color: ${matchStatus.color}">
                        ${matchStatus.text}
                    </span>
                </div>
                
                <div class="teams">
                    <div class="team">
                        <div class="team-name">${match.team1}</div>
                        <div class="team-score">${matchStatus.status === 'finished' ? '?' : '-'}</div>
                    </div>
                    <div class="vs">VS</div>
                    <div class="team">
                        <div class="team-name">${match.team2}</div>
                        <div class="team-score">${matchStatus.status === 'finished' ? '?' : '-'}</div>
                    </div>
                </div>
                
                <div class="match-probabilities">
                    <div class="prob-row">
                        <span>${match.team1}</span>
                        <div class="prob-bar-container">
                            <div class="prob-bar-fill" style="width: 0%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>
                        </div>
                        <span>${team1Prob}%</span>
                    </div>
                    <div class="prob-row">
                        <span>Nerešeno</span>
                        <div class="prob-bar-container">
                            <div class="prob-bar-fill" style="width: 0%; background: linear-gradient(90deg, #f59e0b, #ef4444);"></div>
                        </div>
                        <span>${drawProb}%</span>
                    </div>
                    <div class="prob-row">
                        <span>${match.team2}</span>
                        <div class="prob-bar-container">
                            <div class="prob-bar-fill" style="width: 0%; background: linear-gradient(90deg, #10b981, #059669);"></div>
                        </div>
                        <span>${team2Prob}%</span>
                    </div>
                </div>
                
                <div class="prediction-box">
                    <div class="prediction-text">
                        🤖 AI predviđa: 
                        <span class="prediction-winner">${prediction.winner}</span>
                        <span style="font-size: 0.8rem;"> (${prediction.confidence}% sigurnosti)</span>
                    </div>
                </div>
            </div>
        `;
        
        matchesGrid.appendChild(matchCard);
        
        // Animacija progress bar-ova
        setTimeout(() => {
            const bars = matchCard.querySelectorAll('.prob-bar-fill');
            if (bars[0]) bars[0].style.width = `${team1Prob}%`;
            if (bars[1]) bars[1].style.width = `${drawProb}%`;
            if (bars[2]) bars[2].style.width = `${team2Prob}%`;
        }, 100);
    }
    
    if (!silent) hideLoading();
}

// Učitavanje live utakmica
async function loadLiveMatches(silent = false) {
    if (isUpdating) return;
    isUpdating = true;
    
    if (!silent) showLoading();
    
    try {
        // U stvarnosti bi se podaci učitavali sa API-ja
        // const response = await fetch(`${API_URL}/live-matches`);
        // const matches = await response.json();
        
        // Za sada koristimo mock podatke
        const matches = MATCH_SCHEDULE;
        
        await displayMatches(matches, silent);
        updateTimestamp();
        
    } catch (error) {
        console.error('Greška pri učitavanju:', error);
        if (!silent) {
            matchesGrid.innerHTML = `
                <div class="no-matches">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Greška pri učitavanju utakmica</p>
                    <button onclick="location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem;">Pokušaj ponovo</button>
                </div>
            `;
        }
    } finally {
        if (!silent) hideLoading();
        isUpdating = false;
    }
}

// Event listeneri
function setupEventListeners() {
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => loadLiveMatches(false));
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Date selector
    const dateBtns = document.querySelectorAll('.date-btn');
    dateBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            dateBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedDate = btn.dataset.date;
            loadLiveMatches(false);
        });
    });
}

// Pokreni inicijalizaciju
document.addEventListener('DOMContentLoaded', init);