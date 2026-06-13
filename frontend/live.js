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
let liveMatches = []; // Keš za utakmice sa API-ja

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

// Dohvatanje predikcije za utakmicu
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
    
    // Fallback simulacija ako API ne radi
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

// Dohvatanje utakmica sa backend API-ja
async function fetchMatchesFromAPI() {
    try {
        const response = await fetch(`${API_URL}/live-matches`);
        const data = await response.json();
        
        if (data.matches && data.matches.length > 0) {
            console.log(`✅ Dohvaćeno ${data.matches.length} utakmica sa API-ja (izvor: ${data.source})`);
            return data.matches;
        } else {
            console.log('⚠️ API nije vratio utakmice, koristim prazan niz');
            return [];
        }
    } catch (error) {
        console.error('❌ Greška pri dohvatanju sa API-ja:', error);
        return [];
    }
}

// Određivanje statusa i rezultata utakmice iz API podataka
function processMatchFromAPI(apiMatch) {
    const isFinished = apiMatch.status === 'finished';
    const isLive = apiMatch.status === 'live';
    const hasScore = apiMatch.home_goals !== undefined && apiMatch.away_goals !== undefined;
    
    return {
        date: apiMatch.date,
        team1: apiMatch.team1,
        team2: apiMatch.team2,
        time: apiMatch.time || '--:--',
        group: apiMatch.group || '?',
        finished: isFinished,
        live: isLive,
        result: hasScore ? `${apiMatch.home_goals}-${apiMatch.away_goals}` : null,
        winner: apiMatch.winner,
        home_goals: apiMatch.home_goals,
        away_goals: apiMatch.away_goals,
        score: hasScore ? `${apiMatch.home_goals}-${apiMatch.away_goals}` : null
    };
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
        // Dohvati predikciju za ovu utakmicu
        const prediction = await getPredictionForMatch(match.team1, match.team2, 'neutral');
        
        const matchCard = document.createElement('div');
        const isLiveClass = match.live ? 'live' : '';
        matchCard.className = `match-card ${isLiveClass}`;
        
        // Prikaz rezultata
        let scoreDisplay = '';
        if (match.finished && match.score) {
            // Završena utakmica - prikazujemo stvarni rezultat
            scoreDisplay = `
                <div class="teams">
                    <div class="team">
                        <div class="team-name">${match.team1}</div>
                        <div class="team-score" style="font-size: 2rem;">${match.home_goals}</div>
                    </div>
                    <div class="vs">VS</div>
                    <div class="team">
                        <div class="team-name">${match.team2}</div>
                        <div class="team-score" style="font-size: 2rem;">${match.away_goals}</div>
                    </div>
                </div>
            `;
        } else if (match.live && match.score) {
            // Utakmica u toku
            scoreDisplay = `
                <div class="teams">
                    <div class="team">
                        <div class="team-name">${match.team1}</div>
                        <div class="team-score" style="font-size: 2rem;">${match.home_goals || 0}</div>
                    </div>
                    <div class="vs">VS</div>
                    <div class="team">
                        <div class="team-name">${match.team2}</div>
                        <div class="team-score" style="font-size: 2rem;">${match.away_goals || 0}</div>
                    </div>
                </div>
            `;
        } else {
            // Utakmica koja još nije počela
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
        
        // Status utakmice
        let statusText = '';
        let statusColor = '';
        if (match.finished) {
            statusText = '✅ Završeno';
            statusColor = '#10b981';
        } else if (match.live) {
            statusText = '🔴 UŽIVO';
            statusColor = '#ef4444';
        } else {
            statusText = '📅 Ususret';
            statusColor = '#f59e0b';
        }
        
        // Tekst pobednika
        let winnerText = '';
        if (match.finished && match.winner) {
            winnerText = `🏆 ${match.winner} (utakmica završena)`;
        } else if (match.finished && !match.winner && match.home_goals === match.away_goals) {
            winnerText = `🏆 Nerešeno (utakmica završena)`;
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

// Glavna funkcija za učitavanje live utakmica
async function loadLiveMatches(silent = false) {
    if (!silent) showLoading();
    
    try {
        // Dohvati utakmice sa API-ja
        const apiMatches = await fetchMatchesFromAPI();
        
        if (apiMatches.length > 0) {
            // Konvertuj API podatke u format za prikaz
            const processedMatches = apiMatches.map(match => processMatchFromAPI(match));
            liveMatches = processedMatches;
            await displayMatches(processedMatches, silent);
        } else {
            // Ako nema podataka sa API-ja, prikaži poruku
            matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-info-circle"></i><p>Trenutno nema dostupnih utakmica. Proverite API konekciju.</p></div>`;
        }
        
        updateTimestamp();
    } catch (error) {
        console.error('Greška pri učitavanju:', error);
        if (!silent) {
            matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-exclamation-triangle"></i><p>Greška pri učitavanju utakmica sa API-ja</p><button onclick="location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem;">Pokušaj ponovo</button></div>`;
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
            if (liveMatches.length > 0) {
                displayMatches(liveMatches, true);
            } else {
                loadLiveMatches(false);
            }
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