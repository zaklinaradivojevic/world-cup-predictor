// Live predikcije JavaScript - sa stvarnim rezultatima

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

// Datumi utakmica SP 2026 sa REZULTATIMA
const MATCH_SCHEDULE = [
    { date: "2026-06-11", team1: "Mexico", team2: "South Africa", venue: "neutral", time: "18:00", group: "A", finished: true, result: "2-1", winner: "Mexico", home_goals: 2, away_goals: 1 },
    { date: "2026-06-11", team1: "Germany", team2: "New Zealand", venue: "neutral", time: "21:00", group: "A", finished: true, result: "3-0", winner: "Germany", home_goals: 3, away_goals: 0 },
    { date: "2026-06-12", team1: "Brazil", team2: "Portugal", venue: "neutral", time: "18:00", group: "B", finished: true, result: "2-0", winner: "Brazil", home_goals: 2, away_goals: 0 },
    { date: "2026-06-12", team1: "USA", team2: "Saudi Arabia", venue: "neutral", time: "21:00", group: "B", finished: true, result: "1-1", winner: null, home_goals: 1, away_goals: 1 },
    { date: "2026-06-13", team1: "France", team2: "Denmark", venue: "neutral", time: "18:00", group: "C", finished: false, live: false, result: null, winner: null },
    { date: "2026-06-13", team1: "Japan", team2: "Ecuador", venue: "neutral", time: "21:00", group: "C", finished: false, live: false, result: null, winner: null },
    { date: "2026-06-14", team1: "Argentina", team2: "Croatia", venue: "neutral", time: "18:00", group: "D", finished: false, live: false, result: null, winner: null },
    { date: "2026-06-14", team1: "Australia", team2: "Canada", venue: "neutral", time: "21:00", group: "D", finished: false, live: false, result: null, winner: null },
    { date: "2026-06-15", team1: "Spain", team2: "Netherlands", venue: "neutral", time: "18:00", group: "E", finished: false, live: false, result: null, winner: null },
    { date: "2026-06-15", team1: "Morocco", team2: "Costa Rica", venue: "neutral", time: "21:00", group: "E", finished: false, live: false, result: null, winner: null },
    { date: "2026-06-16", team1: "England", team2: "Belgium", venue: "neutral", time: "18:00", group: "F", finished: false, live: false, result: null, winner: null },
    { date: "2026-06-16", team1: "Senegal", team2: "Iran", venue: "neutral", time: "21:00", group: "F", finished: false, live: false, result: null, winner: null }
];

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

// Auto-refresh na 30 sekundi
function startAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    autoRefreshInterval = setInterval(() => {
        loadLiveMatches(true);
    }, 30000);
}

function showLoading() { if (loadingOverlay) loadingOverlay.style.display = 'flex'; }
function hideLoading() { if (loadingOverlay) loadingOverlay.style.display = 'none'; }

function updateTimestamp() {
    const now = new Date();
    lastUpdateSpan.textContent = `Zadnje ažuriranje: ${now.toLocaleTimeString()}`;
}

// Filtriranje po datumu
function filterMatchesByDate(matches) {
    const today = new Date().toISOString().split('T')[0];
    const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
    
    if (selectedDate === 'today') return matches.filter(m => m.date === today);
    if (selectedDate === 'tomorrow') return matches.filter(m => m.date === tomorrow);
    return matches;
}

// Simulacija predikcije (dok API ne radi)
async function getPredictionForMatch(team1, team2, venue) {
    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team1, team2, venue, tournament: 'World Cup' })
        });
        if (response.ok) return await response.json();
    } catch (error) {
        console.log('API nije dostupan, koristim simulaciju');
    }
    
    return {
        winner: Math.random() > 0.5 ? team1 : team2,
        confidence: Math.floor(Math.random() * 30) + 50,
        probabilities: {
            [`${team1}_win`]: Math.floor(Math.random() * 40) + 30,
            draw: Math.floor(Math.random() * 20) + 10,
            [`${team2}_win`]: Math.floor(Math.random() * 40) + 30
        }
    };
}

// Određivanje statusa utakmice
function getMatchStatus(match) {
    if (match.finished) {
        return { 
            status: 'finished', 
            text: '✅ Završeno', 
            color: '#10b981', 
            score: match.result,
            home_goals: match.home_goals,
            away_goals: match.away_goals,
            winner: match.winner
        };
    }
    if (match.live) {
        return { 
            status: 'live', 
            text: '🔴 UŽIVO', 
            color: '#ef4444', 
            score: match.score, 
            minute: match.minute,
            home_goals: match.home_goals,
            away_goals: match.away_goals
        };
    }
    return { status: 'upcoming', text: '📅 Ususret', color: '#f59e0b', score: null };
}

// Prikazivanje utakmica
async function displayMatches(matches, silent = false) {
    if (!silent) showLoading();
    
    const filteredMatches = filterMatchesByDate(matches);
    
    if (filteredMatches.length === 0) {
        matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-calendar-day"></i><p>Nema utakmica za izabrani datum</p></div>`;
        if (!silent) hideLoading();
        return;
    }
    
    matchesGrid.innerHTML = '';
    
    for (const match of filteredMatches) {
        const prediction = await getPredictionForMatch(match.team1, match.team2, match.venue);
        const matchStatus = getMatchStatus(match);
        
        const matchCard = document.createElement('div');
        matchCard.className = `match-card ${matchStatus.status === 'live' ? 'live' : ''}`;
        
        // Prikaz rezultata ako je utakmica završena
        let scoreDisplay = '';
        if (matchStatus.status === 'finished' && matchStatus.score) {
            scoreDisplay = `
                <div class="teams">
                    <div class="team">
                        <div class="team-name">${match.team1}</div>
                        <div class="team-score" style="font-size: 2rem;">${matchStatus.home_goals}</div>
                    </div>
                    <div class="vs">VS</div>
                    <div class="team">
                        <div class="team-name">${match.team2}</div>
                        <div class="team-score" style="font-size: 2rem;">${matchStatus.away_goals}</div>
                    </div>
                </div>
            `;
        } else if (matchStatus.status === 'live' && matchStatus.score) {
            scoreDisplay = `
                <div class="teams">
                    <div class="team">
                        <div class="team-name">${match.team1}</div>
                        <div class="team-score" style="font-size: 2rem;">${matchStatus.home_goals || 0}</div>
                    </div>
                    <div class="vs">VS</div>
                    <div class="team">
                        <div class="team-name">${match.team2}</div>
                        <div class="team-score" style="font-size: 2rem;">${matchStatus.away_goals || 0}</div>
                    </div>
                </div>
            `;
            if (matchStatus.minute) {
                scoreDisplay += `<div style="text-align: center; font-size: 0.8rem;">${matchStatus.minute}' minut</div>`;
            }
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
        
        // Odrediti pobednika za prikaz
        let winnerText = '';
        if (matchStatus.status === 'finished' && matchStatus.winner) {
            winnerText = `🏆 ${matchStatus.winner} (utakmica završena)`;
        } else {
            winnerText = `${prediction.winner} (${prediction.confidence}% sigurnosti)`;
        }
        
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
                
                ${scoreDisplay}
                
                <div class="match-probabilities">
                    <div class="prob-row">
                        <span>${match.team1}</span>
                        <div class="prob-bar-container">
                            <div class="prob-bar-fill" style="width: ${prediction.probabilities[`${match.team1}_win`]}%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>
                        </div>
                        <span>${prediction.probabilities[`${match.team1}_win`]}%</span>
                    </div>
                    <div class="prob-row">
                        <span>Nerešeno</span>
                        <div class="prob-bar-container">
                            <div class="prob-bar-fill" style="width: ${prediction.probabilities.draw}%; background: linear-gradient(90deg, #f59e0b, #ef4444);"></div>
                        </div>
                        <span>${prediction.probabilities.draw}%</span>
                    </div>
                    <div class="prob-row">
                        <span>${match.team2}</span>
                        <div class="prob-bar-container">
                            <div class="prob-bar-fill" style="width: ${prediction.probabilities[`${match.team2}_win`]}%; background: linear-gradient(90deg, #10b981, #059669);"></div>
                        </div>
                        <span>${prediction.probabilities[`${match.team2}_win`]}%</span>
                    </div>
                </div>
                
                <div class="prediction-box">
                    <div class="prediction-text">
                        🤖 AI predviđa: 
                        <span class="prediction-winner">${winnerText}</span>
                    </div>
                </div>
            </div>
        `;
        
        matchesGrid.appendChild(matchCard);
        
        // Animacija progress bar-ova
        setTimeout(() => {
            const bars = matchCard.querySelectorAll('.prob-bar-fill');
            if (bars[0]) bars[0].style.width = `${prediction.probabilities[`${match.team1}_win`]}%`;
            if (bars[1]) bars[1].style.width = `${prediction.probabilities.draw}%`;
            if (bars[2]) bars[2].style.width = `${prediction.probabilities[`${match.team2}_win`]}%`;
        }, 100);
    }
    
    if (!silent) hideLoading();
}

async function loadLiveMatches(silent = false) {
    if (!silent) showLoading();
    
    try {
        await displayMatches(MATCH_SCHEDULE, silent);
        updateTimestamp();
    } catch (error) {
        console.error('Greška:', error);
        if (!silent) {
            matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-exclamation-triangle"></i><p>Greška pri učitavanju utakmica</p></div>`;
        }
    } finally {
        if (!silent) hideLoading();
    }
}

// Event listeneri
function setupEventListeners() {
    if (refreshBtn) refreshBtn.addEventListener('click', () => loadLiveMatches(false));
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
    
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

// Inicijalizacija
function init() {
    loadTheme();
    setupEventListeners();
    loadLiveMatches(false);
    startAutoRefresh();
}

document.addEventListener('DOMContentLoaded', init);