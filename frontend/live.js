// Live predikcije JavaScript - sa STVARNIM rezultatima sa API-ja

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
let liveMatches = [];

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

function filterMatchesByDate(matches) {
    const today = new Date().toISOString().split('T')[0];
    const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
    
    if (selectedDate === 'today') return matches.filter(m => m.date === today);
    if (selectedDate === 'tomorrow') return matches.filter(m => m.date === tomorrow);
    return matches;
}

// Dohvatanje predikcije
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

// Dohvatanje utakmica sa API-ja
async function fetchMatchesFromAPI() {
    try {
        const response = await fetch(`${API_URL}/live-matches`);
        const data = await response.json();
        
        if (data.matches && data.matches.length > 0) {
            console.log('✅ Dohvaćene utakmice:', data.matches);
            return data.matches;
        }
        return [];
    } catch (error) {
        console.error('❌ Greška:', error);
        return [];
    }
}

// Glavna funkcija za učitavanje i prikaz
async function loadLiveMatches(silent = false) {
    if (!silent) showLoading();
    
    try {
        const apiMatches = await fetchMatchesFromAPI();
        
        if (apiMatches.length === 0) {
            matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-info-circle"></i><p>Trenutno nema dostupnih utakmica</p></div>`;
            if (!silent) hideLoading();
            return;
        }
        
        // Filtriraj po datumu
        let filteredMatches = apiMatches;
        if (selectedDate === 'today') {
            const today = new Date().toISOString().split('T')[0];
            filteredMatches = apiMatches.filter(m => m.date === today);
        } else if (selectedDate === 'tomorrow') {
            const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
            filteredMatches = apiMatches.filter(m => m.date === tomorrow);
        }
        
        if (filteredMatches.length === 0) {
            matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-calendar-day"></i><p>Nema utakmica za izabrani datum</p></div>`;
            if (!silent) hideLoading();
            return;
        }
        
        matchesGrid.innerHTML = '';
        
        for (const match of filteredMatches) {
            const prediction = await getPredictionForMatch(match.team1, match.team2, 'neutral');
            
            // Odredi status i boju
            let statusText = '', statusColor = '';
            if (match.status === 'finished') {
                statusText = '✅ Završeno';
                statusColor = '#10b981';
            } else if (match.status === 'live') {
                statusText = '🔴 UŽIVO';
                statusColor = '#ef4444';
            } else {
                statusText = '📅 Ususret';
                statusColor = '#f59e0b';
            }
            
            // Prikaz rezultata - PRAVI REZULTATI!
            let scoreDisplay = '';
            if (match.status === 'finished' && match.home_goals !== undefined && match.away_goals !== undefined) {
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
            
            // Tekst pobednika
            let winnerText = '';
            if (match.status === 'finished') {
                if (match.winner) {
                    winnerText = `🏆 ${match.winner} (utakmica završena)`;
                } else if (match.home_goals === match.away_goals) {
                    winnerText = `🏆 Nerešeno (utakmica završena)`;
                } else {
                    winnerText = `🏆 ${match.home_goals > match.away_goals ? match.team1 : match.team2} (utakmica završena)`;
                }
            } else {
                winnerText = `${prediction.winner} (${prediction.confidence}% sigurnosti)`;
            }
            
            // Vreme i grupa
            const matchTime = match.time || '--:--';
            const matchGroup = match.group || '?';
            
            const matchCard = document.createElement('div');
            matchCard.className = `match-card ${match.status === 'live' ? 'live' : ''}`;
            
            matchCard.innerHTML = `
                <div class="match-header">
                    <span><i class="fas fa-calendar-alt"></i> ${match.date} | ${matchTime}</span>
                    <span><i class="fas fa-users"></i> Grupa ${matchGroup}</span>
                </div>
                <div class="match-body">
                    <div class="match-status">
                        <span style="color: ${statusColor}">
                            ${statusText}
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
            
            // Animacija
            setTimeout(() => {
                const bars = matchCard.querySelectorAll('.prob-bar-fill');
                if (bars[0]) bars[0].style.width = `${prediction.probabilities[`${match.team1}_win`]}%`;
                if (bars[1]) bars[1].style.width = `${prediction.probabilities.draw}%`;
                if (bars[2]) bars[2].style.width = `${prediction.probabilities[`${match.team2}_win`]}%`;
            }, 100);
        }
        
        updateTimestamp();
    } catch (error) {
        console.error('Greška:', error);
        matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-exclamation-triangle"></i><p>Greška pri učitavanju</p></div>`;
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
    console.log('🚀 Live stranica inicijalizovana');
    loadTheme();
    setupEventListeners();
    loadLiveMatches(false);
    startAutoRefresh();
}

document.addEventListener('DOMContentLoaded', init);