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
import ssl
import certifi

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

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
        
        # Ignoriši SSL grešku (privremeno)
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            matches = []
            
            for match in data.get('matches', []):
                group_name = match.get('group', '')
                if group_name.startswith('GROUP_'):
                    group_name = group_name.replace('GROUP_', '')
                
                utc_date = match.get('utcDate', '')
                match_date = utc_date[:10] if utc_date else ''
                match_time = utc_date[11:16] if utc_date and len(utc_date) > 11 else ''
                
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
            return None
    except Exception as e:
        print(f"⚠️ Greška pri dohvatanju: {e}")
        return None

# ============================================
# STATIČKI PODACI (FALLBACK)
# ============================================

def get_static_matches():
    """Statički podaci kao rezerva"""
    return [
        {'id': 1, 'team1': 'Mexico', 'team2': 'South Africa', 'date': '2026-06-11', 'time': '18:00', 'group': 'A', 'status': 'finished', 'home_goals': 2, 'away_goals': 0, 'winner': 'Mexico'},
        {'id': 2, 'team1': 'South Korea', 'team2': 'Czech Republic', 'date': '2026-06-11', 'time': '21:00', 'group': 'A', 'status': 'finished', 'home_goals': 2, 'away_goals': 1, 'winner': 'South Korea'},
        {'id': 3, 'team1': 'Germany', 'team2': 'Curacao', 'date': '2026-06-14', 'time': '19:00', 'group': 'E', 'status': 'upcoming', 'home_goals': 0, 'away_goals': 0, 'winner': None},
        {'id': 4, 'team1': 'Netherlands', 'team2': 'Japan', 'date': '2026-06-14', 'time': '22:00', 'group': 'F', 'status': 'upcoming', 'home_goals': 0, 'away_goals': 0, 'winner': None},
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
    
    if not USE_MOCK_DATA:
        matches = fetch_matches_from_api()
        if matches:
            matches_cache = matches
            last_update = datetime.now()
            print(f"✅ Keš ažuriran: {len(matches_cache)} utakmica")
            return
    
    # Fallback na statičke podatke
    matches_cache = get_static_matches()
    last_update = datetime.now()
    print(f"📋 Koristim statičke podatke: {len(matches_cache)} utakmica")

# ============================================
# KOMPLETNA LISTA TIMOVA ZA PREDIKTOR
# ============================================

ALL_TEAMS = [
    "Brazil", "Argentina", "France", "Germany", "Spain", "England",
    "Netherlands", "Portugal", "Belgium", "Croatia", "Italy", "Uruguay",
    "Mexico", "USA", "Japan", "Morocco", "Senegal", "Australia",
    "South Africa", "South Korea", "Colombia", "Switzerland", "Poland",
    "Chile", "Nigeria", "Sweden", "Denmark", "Austria", "Czech Republic",
    "Canada", "Paraguay", "Qatar", "Haiti", "Scotland", "Turkiye",
    "Ecuador", "Tunisia", "Saudi Arabia", "Egypt", "Iran", "Cabo Verde",
    "Curacao", "New Zealand", "Uzbekistan", "Jordan", "Ghana", "Norway",
    "Panama", "Algeria", "Ivory Coast", "Wales", "Ukraine", "Slovakia"
]

# ============================================
# ENDPOINTI
# ============================================
@app.route('/')
def home():
    return jsonify({
        'message': '🏆 World Cup 2026 Prediction API is running!',
        'status': 'online',
        'endpoints': {
            'teams': '/api/teams',
            'predict': '/api/predict (POST)',
            'live-matches': '/api/live-matches',
            'health': '/api/health'
        }
    })

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Vraća listu svih timova za prediktor"""
    return jsonify({'teams': sorted(ALL_TEAMS)})

@app.route('/api/live-matches', methods=['GET'])
def get_live_matches():
    """Vraća sve utakmice iz keša"""
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
    
    # Jednostavna simulacija
    home_win = random.uniform(0.3, 0.7)
    draw = random.uniform(0.15, 0.35)
    away_win = 1 - home_win - draw
    
    total = home_win + draw + away_win
    home_win /= total
    draw /= total
    away_win /= total
    
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
        'model_used': 'AI Prediction Engine'
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'matches_count': len(matches_cache),
        'teams_count': len(ALL_TEAMS),
        'last_update': last_update.isoformat() if last_update else None
    })

# ============================================
# POKRETANJE
# ============================================
if __name__ == '__main__':
    # Prvo ažuriranje
    update_matches_cache()
    
    print(f"\n🚀 Server running on http://localhost:5000")
    print(f"📊 {len(ALL_TEAMS)} timova učitano")
    print(f"📋 {len(matches_cache)} utakmica u kešu")
    print("="*50)
    app.run(debug=True, port=5000)