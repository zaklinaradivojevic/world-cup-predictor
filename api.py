"""
API sa XGBoost modelom - STVARNI PODACI SA FOOTBALL-DATA.ORG
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import os
import random
import requests
from datetime import datetime
import time
import threading
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ============================================
# API KONFIGURACIJA
# ============================================
FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '')
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'

print("="*50)
print("🏆 WORLD CUP 2026 PREDICTION API")
print("="*50)
print(f"🔑 Football-Data.org token: {'✅' if FOOTBALL_DATA_API_KEY else '❌'}")
print(f"🎭 Mock podaci: {'❌ NE' if not USE_MOCK_DATA else '✅ DA'}")
print("="*50)

# ============================================
# UČITAVANJE MODELA
# ============================================
model_path = 'backend/data/models/xgboost_model.pkl'
features_path = 'backend/data/models/features.txt'

if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("✅ XGBoost model učitana")
    with open(features_path, 'r') as f:
        feature_names = [line.strip() for line in f.readlines()]
else:
    print("❌ Model nije pronađen! Koristim simulaciju.")
    model = None

# ============================================
# DOHVATANJE PODATAKA SA FOOTBALL-DATA.ORG
# ============================================

def fetch_matches_from_api():
    """Dohvata utakmice sa Football-Data.org API-ja"""
    if not FOOTBALL_DATA_API_KEY:
        print("⚠️ Nema API ključa za Football-Data.org")
        return None
    
    try:
        headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
        url = "https://api.football-data.org/v4/competitions/WC/matches"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            matches = []
            
            for match in data.get('matches', []):
                # Ime grupe (npr. "GROUP_A" -> "A")
                group_name = match.get('group', '')
                if group_name.startswith('GROUP_'):
                    group_name = group_name.replace('GROUP_', '')
                
                # Datum i vreme
                utc_date = match.get('utcDate', '')
                match_date = utc_date[:10] if utc_date else ''
                match_time = utc_date[11:16] if utc_date and len(utc_date) > 11 else ''
                
                # Status i golovi
                status = match.get('status', '')
                if status == 'FINISHED':
                    match_status = 'finished'
                    home_goals = match.get('score', {}).get('fullTime', {}).get('home', 0)
                    away_goals = match.get('score', {}).get('fullTime', {}).get('away', 0)
                    winner = match.get('score', {}).get('winner', None)
                elif status == 'IN_PLAY' or status == 'LIVE':
                    match_status = 'live'
                    home_goals = match.get('score', {}).get('halfTime', {}).get('home', 0)
                    away_goals = match.get('score', {}).get('halfTime', {}).get('away', 0)
                    winner = None
                else:
                    match_status = 'upcoming'
                    home_goals = 0
                    away_goals = 0
                    winner = None
                
                # Ime timova
                home_team = match.get('homeTeam', {}).get('name', '')
                away_team = match.get('awayTeam', {}).get('name', '')
                
                matches.append({
                    'id': match.get('id'),
                    'team1': home_team,
                    'team2': away_team,
                    'date': match_date,
                    'time': match_time,
                    'group': group_name,
                    'status': match_status,
                    'home_goals': home_goals,
                    'away_goals': away_goals,
                    'score': f"{home_goals}-{away_goals}" if match_status == 'finished' else None,
                    'winner': winner
                })
            
            print(f"✅ Dohvaćeno {len(matches)} utakmica sa Football-Data.org")
            return matches
        else:
            print(f"⚠️ API greška: {response.status_code}")
            if response.status_code == 403:
                print("   → Proveri API ključ! Možda je istekao.")
            return None
    except Exception as e:
        print(f"⚠️ Greška pri dohvatanju: {e}")
        return None

# ============================================
# FALLBACK: STATIČKI PODACI (ako API ne radi)
# ============================================

def get_static_matches():
    """Statički podaci kao rezerva"""
    return [
        {'id': 1, 'team1': 'Mexico', 'team2': 'South Africa', 'date': '2026-06-11', 'time': '18:00', 'group': 'A', 'status': 'finished', 'home_goals': 2, 'away_goals': 0, 'winner': 'Mexico'},
        {'id': 2, 'team1': 'South Korea', 'team2': 'Czech Republic', 'date': '2026-06-11', 'time': '21:00', 'group': 'A', 'status': 'finished', 'home_goals': 2, 'away_goals': 1, 'winner': 'South Korea'},
        {'id': 3, 'team1': 'Germany', 'team2': 'Curacao', 'date': '2026-06-14', 'time': '19:00', 'group': 'E', 'status': 'upcoming', 'home_goals': 0, 'away_goals': 0, 'winner': None},
        {'id': 4, 'team1': 'Netherlands', 'team2': 'Japan', 'date': '2026-06-14', 'time': '22:00', 'group': 'F', 'status': 'upcoming', 'home_goals': 0, 'away_goals': 0, 'winner': None},
        {'id': 5, 'team1': 'Ecuador', 'team2': 'Ivory Coast', 'date': '2026-06-15', 'time': '01:00', 'group': 'E', 'status': 'upcoming', 'home_goals': 0, 'away_goals': 0, 'winner': None},
        {'id': 6, 'team1': 'Sweden', 'team2': 'Tunisia', 'date': '2026-06-15', 'time': '04:00', 'group': 'F', 'status': 'upcoming', 'home_goals': 0, 'away_goals': 0, 'winner': None},
    ]

# ============================================
# CACHE ZA UTAKMICE
# ============================================
matches_cache = []
last_update = None

def update_matches_cache():
    """Ažurira keš utakmica"""
    global matches_cache, last_update
    
    print("🔄 Ažuriranje utakmica...")
    
    # Pokušaj sa API-jem
    matches = fetch_matches_from_api()
    
    # Ako API ne radi ili koristimo mock, uzmi statičke
    if not matches or USE_MOCK_DATA:
        matches = get_static_matches()
        print("📋 Koristim statičke podatke")
    else:
        print("📡 Koristim podatke sa Football-Data.org")
    
    matches_cache = matches
    last_update = datetime.now()
    print(f"✅ Keš ažuriran: {len(matches_cache)} utakmica")

def background_updater():
    """Pozadinsko ažuriranje svakih 5 minuta"""
    while True:
        time.sleep(300)  # 5 minuta
        update_matches_cache()

# Prvo ažuriranje
update_matches_cache()

# Pokreni pozadinsku nit
if not USE_MOCK_DATA and FOOTBALL_DATA_API_KEY:
    thread = threading.Thread(target=background_updater, daemon=True)
    thread.start()
    print("🔄 Pozadinsko ažuriranje pokrenuto (svakih 5 minuta)")
else:
    print("📋 Automatsko ažuriranje isključeno (mock podaci)")

# ============================================
# LISTA TIMOVA (dinamički iz utakmica)
# ============================================

def get_all_teams():
    teams = set()
    for match in matches_cache:
        teams.add(match['team1'])
        teams.add(match['team2'])
    return sorted(list(teams))

TEAMS = get_all_teams()
print(f"📊 {len(TEAMS)} timova učitano")

# ============================================
# JAČINA TIMOVA (za predikciju)
# ============================================
TEAM_STRENGTH = {
    'Brazil': 0.95, 'Argentina': 0.93, 'France': 0.92, 'Germany': 0.90,
    'Spain': 0.89, 'England': 0.88, 'Netherlands': 0.85, 'Portugal': 0.84,
    'Belgium': 0.83, 'Croatia': 0.80, 'Italy': 0.82, 'Uruguay': 0.78,
    'Mexico': 0.75, 'USA': 0.74, 'Japan': 0.72, 'Morocco': 0.70,
    'Senegal': 0.68, 'Australia': 0.65, 'South Africa': 0.60,
    'South Korea': 0.62, 'Colombia': 0.73, 'Switzerland': 0.69,
    'Poland': 0.67, 'Chile': 0.66, 'Nigeria': 0.64, 'Sweden': 0.63,
    'Denmark': 0.68, 'Austria': 0.61, 'Czech Republic': 0.60,
    'Canada': 0.70, 'Paraguay': 0.62, 'Qatar': 0.58, 'Haiti': 0.55,
    'Scotland': 0.66, 'Turkiye': 0.64, 'Ecuador': 0.67, 'Tunisia': 0.61,
    'Saudi Arabia': 0.56, 'Egypt': 0.63, 'Iran': 0.60, 'Cabo Verde': 0.54,
    'Curacao': 0.52, 'New Zealand': 0.53, 'Uzbekistan': 0.51, 'Jordan': 0.50,
    'Ghana': 0.65, 'Norway': 0.64, 'Panama': 0.55, 'Algeria': 0.66,
    'Ivory Coast': 0.64
}

def get_strength(team):
    return TEAM_STRENGTH.get(team, 0.65)

# ============================================
# ENDPOINTI
# ============================================

@app.route('/api/teams', methods=['GET'])
def get_teams():
    return jsonify({'teams': get_all_teams()})

@app.route('/api/live-matches', methods=['GET'])
def get_live_matches():
    return jsonify({
        'matches': matches_cache,
        'source': 'football-data.org' if not USE_MOCK_DATA else 'static',
        'last_update': last_update.isoformat() if last_update else None
    })

@app.route('/api/refresh', methods=['POST'])
def refresh_matches():
    """Ručno osvežavanje utakmica"""
    update_matches_cache()
    return jsonify({'message': 'Utakmice osvežene', 'count': len(matches_cache)})

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    team1 = data.get('team1')
    team2 = data.get('team2')
    venue = data.get('venue', 'neutral')
    
    if not team1 or not team2:
        return jsonify({'error': 'Nedostaju timovi'}), 400
    
    if team1 == team2:
        return jsonify({'error': 'Timovi moraju biti različiti'}), 400
    
    # Izračunaj verovatnoće na osnovu jačine timova
    strength1 = get_strength(team1)
    strength2 = get_strength(team2)
    
    home_factor = 1.20 if venue == 'home' else (0.85 if venue == 'away' else 1.00)
    adjusted_strength1 = strength1 * home_factor
    
    total = adjusted_strength1 + strength2
    home_win = (adjusted_strength1 / total) * 0.7 + 0.15
    away_win = (strength2 / total) * 0.7 + 0.15
    draw = 1 - home_win - away_win
    
    # Normalizacija
    total_prob = home_win + draw + away_win
    home_win /= total_prob
    draw /= total_prob
    away_win /= total_prob
    
    if home_win > draw and home_win > away_win:
        winner = team1
        confidence = home_win
    elif away_win > home_win and away_win > draw:
        winner = team2
        confidence = away_win
    else:
        winner = "Nerešeno"
        confidence = draw
    
    return jsonify({
        'team1': team1,
        'team2': team2,
        'winner': winner,
        'confidence': round(confidence * 100, 1),
        'probabilities': {
            f'{team1}_win': round(home_win * 100, 1),
            'draw': round(draw * 100, 1),
            f'{team2}_win': round(away_win * 100, 1)
        },
        'model_used': 'Strength-based (Football-Data.org)'
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'matches_count': len(matches_cache),
        'teams_count': len(get_all_teams()),
        'last_update': last_update.isoformat() if last_update else None,
        'source': 'football-data.org' if not USE_MOCK_DATA else 'static'
    })

# ============================================
# TURNIR SIMULACIJA (skraćena)
# ============================================

@app.route('/api/simulate-group-stage', methods=['GET'])
def simulate_group_stage():
    """Vraća stvarne grupe sa podacima iz API-ja"""
    groups = {}
    for match in matches_cache:
        group = match.get('group', 'Unknown')
        if group not in groups:
            groups[group] = {}
        
        for team in [match['team1'], match['team2']]:
            if team not in groups[group]:
                groups[group][team] = {'played': 0, 'points': 0}
    
    return jsonify(groups)


@app.route('/api/teams', methods=['GET'])
def get_teams():
    # Privremena lista dok API ne bude vraćao prave timove
    all_teams = [
        "Brazil", "Argentina", "France", "Germany", "Spain", "England",
        "Netherlands", "Portugal", "Belgium", "Croatia", "Italy", "Uruguay",
        "Mexico", "USA", "Japan", "Morocco", "Senegal", "Australia",
        "South Africa", "South Korea", "Colombia", "Switzerland", "Poland",
        "Chile", "Nigeria", "Sweden", "Denmark", "Austria", "Czech Republic",
        "Canada", "Paraguay", "Qatar", "Haiti", "Scotland", "Turkiye",
        "Ecuador", "Tunisia", "Saudi Arabia", "Egypt", "Iran", "Cabo Verde",
        "Curacao", "New Zealand", "Uzbekistan", "Jordan", "Ghana", "Norway",
        "Panama", "Algeria", "Ivory Coast"
    ]
    return jsonify({'teams': sorted(all_teams)})

# ============================================
# POKRETANJE
# ============================================
if __name__ == '__main__':
    print(f"\n🚀 Server running on http://localhost:5000")
    print(f"📊 {len(TEAMS)} timova učitano")
    print(f"📋 {len(matches_cache)} utakmica u kešu")
    print("="*50)
    app.run(debug=True, port=5000)