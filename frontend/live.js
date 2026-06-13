// Live predikcije - jednostavna verzija

const API_URL = 'http://localhost:5000/api';

document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Stranica učitana, dohvatam utakmice...');
    
    const matchesGrid = document.getElementById('matchesGrid');
    
    if (!matchesGrid) {
        console.error('Element matchesGrid nije pronađen!');
        return;
    }
    
    matchesGrid.innerHTML = '<div class="no-matches"><div class="loader-circle"></div><p>Učitavanje utakmica...</p></div>';
    
    try {
        const response = await fetch(`${API_URL}/live-matches`);
        const data = await response.json();
        
        console.log('Dobijeni podaci:', data);
        
        if (!data.matches || data.matches.length === 0) {
            matchesGrid.innerHTML = '<div class="no-matches"><i class="fas fa-info-circle"></i><p>Nema dostupnih utakmica</p></div>';
            return;
        }
        
        matchesGrid.innerHTML = '';
        
        for (const match of data.matches) {
            const statusText = match.status === 'finished' ? '✅ Završeno' : '📅 Ususret';
            const statusColor = match.status === 'finished' ? '#10b981' : '#f59e0b';
            
            const card = document.createElement('div');
            card.className = 'match-card';
            card.innerHTML = `
                <div class="match-header">
                    <span><i class="fas fa-calendar-alt"></i> ${match.date} | ${match.time || '--:--'}</span>
                    <span><i class="fas fa-users"></i> Grupa ${match.group || '?'}</span>
                </div>
                <div class="match-body">
                    <div class="match-status">
                        <span style="color: ${statusColor}; font-weight: bold;">${statusText}</span>
                    </div>
                    <div class="teams">
                        <div class="team">
                            <div class="team-name">${match.team1}</div>
                            <div class="team-score" style="font-size: 2rem; font-weight: 800;">${match.home_goals !== undefined ? match.home_goals : '-'}</div>
                        </div>
                        <div class="vs">VS</div>
                        <div class="team">
                            <div class="team-name">${match.team2}</div>
                            <div class="team-score" style="font-size: 2rem; font-weight: 800;">${match.away_goals !== undefined ? match.away_goals : '-'}</div>
                        </div>
                    </div>
                    <div class="prediction-box" style="margin-top: 1rem; padding: 0.75rem; background: rgba(102,126,234,0.1); border-radius: 8px; text-align: center;">
                        <div class="prediction-text">
                            🤖 AI predviđa: <strong>${match.winner || (match.home_goals > match.away_goals ? match.team1 : (match.away_goals > match.home_goals ? match.team2 : 'Nerešeno')) || match.team1}</strong>
                        </div>
                    </div>
                </div>
            `;
            matchesGrid.appendChild(card);
        }
        
        // Ažuriraj timestamp
        const lastUpdateSpan = document.getElementById('lastUpdate');
        if (lastUpdateSpan) {
            const now = new Date();
            lastUpdateSpan.textContent = `Zadnje ažuriranje: ${now.toLocaleTimeString()}`;
        }
        
    } catch (error) {
        console.error('Greška:', error);
        matchesGrid.innerHTML = `<div class="no-matches"><i class="fas fa-exclamation-triangle"></i><p>Greška: ${error.message}</p><button onclick="location.reload()" style="margin-top:1rem;padding:0.5rem 1rem;">Pokušaj ponovo</button></div>`;
    }
});

// Tema (jednostavna)
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

// Refresh dugme
const refreshBtn = document.getElementById('refreshBtn');
if (refreshBtn) {
    refreshBtn.addEventListener('click', () => location.reload());
}

const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
}

loadTheme();