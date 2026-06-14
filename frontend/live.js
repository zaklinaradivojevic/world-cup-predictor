// Live predikcije - SA FILTRIRANJEM

// TAČNI REZULTATI SP 2026
const WORLD_CUP_MATCHES = [
    { id: 1, team1: "Mexico", team2: "South Africa", date: "2026-06-11", time: "18:00", group: "A", finished: true, home_goals: 2, away_goals: 0, winner: "Mexico" },
    { id: 2, team1: "South Korea", team2: "Czech Republic", date: "2026-06-11", time: "21:00", group: "A", finished: true, home_goals: 2, away_goals: 1, winner: "South Korea" },
    { id: 3, team1: "Canada", team2: "Bosnia and Herzegovina", date: "2026-06-12", time: "21:00", group: "B", finished: true, home_goals: 1, away_goals: 1, winner: null },
    { id: 4, team1: "USA", team2: "Paraguay", date: "2026-06-12", time: "21:00", group: "B", finished: true, home_goals: 4, away_goals: 1, winner: "USA" },
    { id: 5, team1: "Qatar", team2: "Switzerland", date: "2026-06-13", time: "15:00", group: "B", finished: false },
    { id: 6, team1: "Brazil", team2: "Morocco", date: "2026-06-13", time: "18:00", group: "C", finished: true, home_goals: 1, away_goals: 1, winner: null },
    { id: 7, team1: "Haiti", team2: "Scotland", date: "2026-06-13", time: "21:00", group: "C", finished: true, home_goals: 0, away_goals: 1, winner: "Scotland" },
    { id: 8, team1: "Australia", team2: "Turkiye", date: "2026-06-14", time: "00:00", group: "D", finished: false }
];

// Trenutno izabrani filter
let currentFilter = 'today';

// Dohvatanje datuma
function getTodayDate() {
    const today = new Date();
    return today.toISOString().split('T')[0];
}

function getTomorrowDate() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
}

// Filtriranje utakmica
function filterMatches() {
    const today = getTodayDate();
    const tomorrow = getTomorrowDate();
    
    if (currentFilter === 'today') {
        return WORLD_CUP_MATCHES.filter(m => m.date === today);
    } else if (currentFilter === 'tomorrow') {
        return WORLD_CUP_MATCHES.filter(m => m.date === tomorrow);
    } else {
        return WORLD_CUP_MATCHES;
    }
}

// Prikaz utakmica
function displayMatches() {
    const matchesGrid = document.getElementById('matchesGrid');
    if (!matchesGrid) {
        console.error('matchesGrid nije pronađen!');
        return;
    }
    
    const filteredMatches = filterMatches();
    
    if (filteredMatches.length === 0) {
        matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-calendar-day"></i><p>Nema utakmica za izabrani datum</p></div>`;
        return;
    }
    
    matchesGrid.innerHTML = '';
    
    for (const match of filteredMatches) {
        const statusText = match.finished ? '✅ Završeno' : '📅 Ususret';
        const statusColor = match.finished ? '#10b981' : '#f59e0b';
        
        let scoreDisplay = '';
        if (match.finished) {
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
        
        let winnerText = '';
        if (match.finished && match.winner) {
            winnerText = `🏆 ${match.winner}`;
        } else if (match.finished && !match.winner && match.home_goals === match.away_goals) {
            winnerText = `🏆 Nerešeno`;
        } else {
            winnerText = `📊 Počeće u ${match.time}`;
        }
        
        const card = document.createElement('div');
        card.className = 'match-card';
        card.innerHTML = `
            <div class="match-header">
                <span><i class="fas fa-calendar-alt"></i> ${match.date} | ${match.time}</span>
                <span><i class="fas fa-users"></i> Grupa ${match.group}</span>
            </div>
            <div class="match-body">
                <div class="match-status">
                    <span style="color: ${statusColor}; font-weight: bold;">${statusText}</span>
                </div>
                ${scoreDisplay}
                <div class="prediction-box" style="margin-top: 1rem; padding: 0.75rem; background: rgba(102,126,234,0.1); border-radius: 8px; text-align: center;">
                    <div class="prediction-text">
                        🤖 ${match.finished ? 'Rezultat' : 'Početak'} : <strong>${winnerText}</strong>
                    </div>
                </div>
            </div>
        `;
        matchesGrid.appendChild(card);
    }
    
    const lastUpdateSpan = document.getElementById('lastUpdate');
    if (lastUpdateSpan) {
        const now = new Date();
        lastUpdateSpan.textContent = `Zadnje ažuriranje: ${now.toLocaleTimeString()}`;
    }
}

// Postavljanje event listenera za dugmad
function setupFilters() {
    const dateBtns = document.querySelectorAll('.date-btn');
    console.log('Pronađeno dugmadi:', dateBtns.length);
    
    dateBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            console.log('Kliknuto dugme:', this.dataset.date);
            
            dateBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.dataset.date;
            displayMatches();
        });
    });
}

// Tema
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    const icon = document.querySelector('#themeToggle i');
    if (icon) icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    const icon = document.querySelector('#themeToggle i');
    if (icon) icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

// Inicijalizacija
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Live stranica učitana');
    displayMatches();
    setupFilters();
    
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
    
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) refreshBtn.addEventListener('click', () => displayMatches());
    
    loadTheme();
});