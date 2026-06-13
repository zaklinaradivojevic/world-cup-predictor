"""
API sa XGBoost modelom - prave ML predikcije
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

app = Flask(__name__)
CORS(app)

# ============================================
# UČITAVANJE MODELA
# ============================================
print("="*50)
print("🏆 WORLD CUP 2026 PREDICTION API (XGBoost)")
print("="*50)

# Putanje do modela
model_path = 'backend/data/models/xgboost_model.pkl'
features_path = 'backend/data/models/features.txt'

# Proveri da li model postoji
if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("✅ XGBoost model učitana")
    
    # Učitaj feature names
    with open(features_path, 'r') as f:
        feature_names = [line.strip() for line in f.readlines()]
    print(f"✅ Feature-ovi: {feature_names}")
else:
    print("❌ Model nije pronađen! Prvo pokreni train_model.py")
    model = None
    feature_names = []

# ============================================
# LISTA TIMOVA
# ============================================
TEAMS = [
    "Brazil", "Argentina", "France", "Germany", "Spain", "England",
    "Netherlands", "Portugal", "Belgium", "Croatia", "Italy", "Uruguay",
    "Mexico", "USA", "Japan", "Morocco", "Senegal", "Australia",
    "South Africa", "South Korea", "Colombia", "Switzerland", "Poland",
    "Chile", "Nigeria", "Sweden", "Denmark", "Austria", "Czech Republic"
]

# Jačina timova (za feature-ove)
TEAM_STRENGTH = {
    'Brazil': 0.95, 'Argentina': 0.93, 'France': 0.92, 'Germany': 0.90,
    'Spain': 0.89, 'England': 0.88, 'Netherlands': 0.85, 'Portugal': 0.84,
    'Belgium': 0.83, 'Croatia': 0.80, 'Italy': 0.82, 'Uruguay': 0.78,
    'Mexico': 0.75, 'USA': 0.74, 'Japan': 0.72, 'Morocco': 0.70,
    'Senegal': 0.68, 'Australia': 0.65, 'South Africa': 0.60,
    'South Korea': 0.62, 'Colombia': 0.73, 'Switzerland': 0.69,
    'Poland': 0.67, 'Chile': 0.66, 'Nigeria': 0.64, 'Sweden': 0.63,
    'Denmark': 0.68, 'Austria': 0.61, 'Czech Republic': 0.60
}

# Sportmonks token
SPORTMONKS_TOKEN = os.getenv('SPORTMONKS_TOKEN', '')

# Cache za rezultate utakmica
matches_cache = {}
last_update = None

def get_strength(team):
    return TEAM_STRENGTH.get(team, 0.65)

def prepare_features(team1, team2, venue):
    """Priprema feature-ove za model"""
    strength1 = get_strength(team1)
    strength2 = get_strength(team2)
    
    home_factor = 1.20 if venue == 'home' else (0.85 if venue == 'away' else 1.00)
    
    features = np.array([[
        strength1,
        strength2,
        home_factor,
        1 if venue == 'home' else 0,
        1 if venue == 'neutral' else 0,
        1 if venue == 'away' else 0,
        strength1 - strength2
    ]])
    
    return features

# ============================================
# POZADINSKO AŽURIRANJE REZULTATA
# ============================================

def fetch_live_results():
    """Dohvata žive rezultate sa Sportmonks API-ja"""
    global matches_cache, last_update
    
    if not SPORTMONKS_TOKEN:
        print("⚠️ Sportmonks token nije podešen. Rezultati se neće automatski ažurirati.")
        return
    
    try:
        # PRAVILAN URL: token se NE šalje u URL-u!
        url = "https://api.sportmonks.com/v3/football/fixtures/between/2026-06-01/2026-07-31?include=scores;participants;state"
        
        # PRAVILAN HEADER: token ide u Authorization header
        headers = {
            "Authorization": SPORTMONKS_TOKEN
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            new_cache = {}
            
            for fixture in data.get('data', []):
                # Proveri da li je Svetsko prvenstvo (league_id = 1 ili drugi)
                # Ako ne znaš tačan league_id, prihvati sve utakmice u tom periodu
                participants = fixture.get('participants', [])
                if len(participants) >= 2:
                    match_id = fixture['id']
                    home_goals = 0
                    away_goals = 0
                    
                    # Dohvati rezultate
                    if fixture.get('scores'):
                        for score in fixture['scores']:
                            if score.get('type_id') == 1:  # Final score
                                home_goals = score.get('score', {}).get('home', 0)
                                away_goals = score.get('score', {}).get('away', 0)
                    
                    # Odredi status
                    state_id = fixture.get('state_id', 0)
                    if state_id == 5:
                        status = 'finished'
                    elif state_id == 4:
                        status = 'live'
                    else:
                        status = 'upcoming'
                    
                    # Formatiraj datum i vreme
                    starting_at = fixture.get('starting_at', '')
                    date_str = starting_at.split('T')[0] if starting_at else ''
                    time_str = starting_at.split('T')[1][:5] if starting_at and 'T' in starting_at else ''
                    
                    new_cache[match_id] = {
                        'id': match_id,
                        'team1': participants[0].get('name', ''),
                        'team2': participants[1].get('name', ''),
                        'date': date_str,
                        'time': time_str,
                        'status': status,
                        'home_goals': home_goals,
                        'away_goals': away_goals,
                        'score': f"{home_goals}-{away_goals}" if status == 'finished' else None,
                        'winner': participants[0].get('name', '') if home_goals > away_goals else (participants[1].get('name', '') if away_goals > home_goals else None)
                    }
            
            if new_cache:
                matches_cache = new_cache
                last_update = datetime.now()
                print(f"✅ Rezultati ažurirani: {len(matches_cache)} utakmica u kešu")
            else:
                print(f"⚠️ Nema utakmica u periodu (status: {response.status_code})")
        else:
            print(f"⚠️ API greška: {response.status_code}")
            if response.status_code == 401:
                print("   → Proveri Sportmonks token! Nije autentifikovan.")
            
    except Exception as e:
        print(f"⚠️ Greška pri dohvatanju rezultata: {e}")

def update_results_background():
    """Pokreće pozadinsku nit za ažuriranje rezultata svakih 60 sekundi"""
    while True:
        fetch_live_results()
        time.sleep(60)  # Ažuriraj svakih 60 sekundi

# Pokreni pozadinsku nit ako postoji token
if SPORTMONKS_TOKEN:
    thread = threading.Thread(target=update_results_background, daemon=True)
    thread.start()
    print("🔄 Pozadinsko ažuriranje rezultata pokrenuto (svakih 60 sekundi)")
else:
    print("⚠️ Sportmonks token nije podešen - live rezultati neće biti dostupni")

# ============================================
# ENDPOINTI
# ============================================

@app.route('/api/teams', methods=['GET'])
def get_teams():
    return jsonify({'teams': TEAMS})

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
    
    if model is None:
        return jsonify({'error': 'Model nije učitan'}), 500
    
    # Pripremi feature-ove
    features = prepare_features(team1, team2, venue)
    
    # Predikcija
    pred = model.predict(features)[0]
    proba = model.predict_proba(features)[0]
    
    results_map = {0: team1, 1: "Nerešeno", 2: team2}
    winner = results_map[pred]
    confidence = max(proba) * 100
    
    return jsonify({
        'team1': team1,
        'team2': team2,
        'winner': winner,
        'confidence': round(confidence, 1),
        'probabilities': {
            f'{team1}_win': round(proba[0] * 100, 1),
            'draw': round(proba[1] * 100, 1),
            f'{team2}_win': round(proba[2] * 100, 1)
        },
        'model_used': 'XGBoost (istreniran)'
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'teams_count': len(TEAMS),
        'matches_cached': len(matches_cache),
        'last_update': last_update.isoformat() if last_update else None
    })

@app.route('/api/live-matches', methods=['GET'])
def get_live_matches():
    """Vraća sve utakmice sa keširanim rezultatima"""
    if matches_cache:
        return jsonify({
            'matches': list(matches_cache.values()),
            'source': 'sportmonks',
            'last_update': last_update.isoformat() if last_update else None
        })
    else:
        # Ako nema keša, vrati prazan niz (bez lažnih podataka!)
        return jsonify({
            'matches': [],
            'source': 'no_data',
            'message': 'Sportmonks API nije vratio podatke. Proveri token i konekciju.'
        })

# ============================================
# TURNIR SIMULACIJA
# ============================================

@app.route('/api/simulate-group-stage', methods=['GET'])
def simulate_group_stage():
    """Simulira grupnu fazu"""
    import random
    
    # Grupe za SP 2026 (ažurirane prema tačnim informacijama)
    groups = {
        'A': ['Mexico', 'South Africa', 'South Korea', 'Czech Republic'],
        'B': ['Canada', 'Bosnia and Herzegovina', 'USA', 'Paraguay', 'Qatar', 'Switzerland'],
        'C': ['Brazil', 'Morocco', 'Haiti', 'Scotland'],
        'D': ['Australia', 'Turkiye', 'England', 'Senegal'],
        'E': ['Germany', 'Netherlands', 'Japan', 'Ecuador'],
        'F': ['Spain', 'Portugal', 'Belgium', 'Croatia'],
        'G': ['France', 'Denmark', 'Poland', 'Austria'],
        'H': ['Italy', 'Uruguay', 'Colombia', 'Chile']
    }
    
    results = {}
    
    for group_name, teams in groups.items():
        group_table = {}
        for team in teams:
            group_table[team] = {
                'played': 0, 'wins': 0, 'draws': 0, 'losses': 0,
                'goals_for': 0, 'goals_against': 0, 'points': 0, 'gd': 0
            }
        
        # Simuliraj utakmice u grupi
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                team1 = teams[i]
                team2 = teams[j]
                
                # Dohvati jačinu timova
                strength1 = TEAM_STRENGTH.get(team1, 0.65)
                strength2 = TEAM_STRENGTH.get(team2, 0.65)
                
                # Verovatnoće
                prob1 = strength1 / (strength1 + strength2)
                prob2 = strength2 / (strength1 + strength2)
                prob_draw = 0.25
                
                # Normalizacija
                total = prob1 + prob_draw + prob2
                prob1 /= total
                prob_draw /= total
                prob2 /= total
                
                r = random.random()
                if r < prob1:
                    winner = team1
                    goals1 = random.randint(1, 3)
                    goals2 = random.randint(0, 2)
                elif r < prob1 + prob_draw:
                    winner = None
                    goals1 = random.randint(0, 2)
                    goals2 = goals1
                else:
                    winner = team2
                    goals1 = random.randint(0, 2)
                    goals2 = random.randint(1, 3)
                
                # Ažuriraj tabelu
                if winner == team1:
                    group_table[team1]['wins'] += 1
                    group_table[team1]['points'] += 3
                    group_table[team2]['losses'] += 1
                elif winner == team2:
                    group_table[team2]['wins'] += 1
                    group_table[team2]['points'] += 3
                    group_table[team1]['losses'] += 1
                else:
                    group_table[team1]['draws'] += 1
                    group_table[team1]['points'] += 1
                    group_table[team2]['draws'] += 1
                    group_table[team2]['points'] += 1
                
                group_table[team1]['played'] += 1
                group_table[team2]['played'] += 1
                group_table[team1]['goals_for'] += goals1
                group_table[team1]['goals_against'] += goals2
                group_table[team2]['goals_for'] += goals2
                group_table[team2]['goals_against'] += goals1
        
        # Izračunaj gol razliku
        for team in group_table:
            group_table[team]['gd'] = group_table[team]['goals_for'] - group_table[team]['goals_against']
        
        # Sortiraj i odredi prolaznike
        sorted_teams = sorted(group_table.items(), key=lambda x: (x[1]['points'], x[1]['gd']), reverse=True)
        qualified = [team for team, _ in sorted_teams[:2]]
        
        results[group_name] = {
            'table': group_table,
            'qualified': qualified
        }
    
    return jsonify(results)


@app.route('/api/simulate-tournament', methods=['POST'])
def simulate_tournament():
    """Simulira ceo turnir (grupna + nokaut faza)"""
    import random
    
    data = request.json
    num_simulations = data.get('num_simulations', 100)
    
    # Grupe (ažurirane)
    groups = {
        'A': ['Mexico', 'South Africa', 'South Korea', 'Czech Republic'],
        'B': ['Canada', 'Bosnia and Herzegovina', 'USA', 'Paraguay', 'Qatar', 'Switzerland'],
        'C': ['Brazil', 'Morocco', 'Haiti', 'Scotland'],
        'D': ['Australia', 'Turkiye', 'England', 'Senegal'],
        'E': ['Germany', 'Netherlands', 'Japan', 'Ecuador'],
        'F': ['Spain', 'Portugal', 'Belgium', 'Croatia'],
        'G': ['France', 'Denmark', 'Poland', 'Austria'],
        'H': ['Italy', 'Uruguay', 'Colombia', 'Chile']
    }
    
    winners_count = {}
    
    for sim in range(num_simulations):
        # Simuliraj grupnu fazu
        qualified = []
        for group_name, teams in groups.items():
            # Poenovanje za grupu
            points = {team: 0 for team in teams}
            goals_for = {team: 0 for team in teams}
            goals_against = {team: 0 for team in teams}
            
            for i in range(len(teams)):
                for j in range(i+1, len(teams)):
                    team1 = teams[i]
                    team2 = teams[j]
                    
                    strength1 = TEAM_STRENGTH.get(team1, 0.65)
                    strength2 = TEAM_STRENGTH.get(team2, 0.65)
                    
                    prob1 = strength1 / (strength1 + strength2)
                    prob_draw = 0.25
                    prob2 = strength2 / (strength1 + strength2)
                    
                    total = prob1 + prob_draw + prob2
                    prob1 /= total
                    prob_draw /= total
                    prob2 /= total
                    
                    r = random.random()
                    if r < prob1:
                        points[team1] += 3
                        goals1 = random.randint(1, 2)
                        goals2 = random.randint(0, 1)
                    elif r < prob1 + prob_draw:
                        points[team1] += 1
                        points[team2] += 1
                        goals1 = random.randint(0, 1)
                        goals2 = goals1
                    else:
                        points[team2] += 3
                        goals1 = random.randint(0, 1)
                        goals2 = random.randint(1, 2)
                    
                    goals_for[team1] += goals1
                    goals_for[team2] += goals2
                    goals_against[team1] += goals2
                    goals_against[team2] += goals1
            
            # Odredi prolaznike (prva 2 iz svake grupe)
            sorted_teams = sorted(teams, key=lambda t: (points[t], goals_for[t] - goals_against[t]), reverse=True)
            qualified.extend(sorted_teams[:2])
        
        # Nokaut faza (pojednostavljeno)
        random.shuffle(qualified)
        champion = qualified[0]
        
        winners_count[champion] = winners_count.get(champion, 0) + 1
    
    return jsonify({
        'championship_probabilities': winners_count,
        'simulations_run': num_simulations
    })


@app.route('/api/elo-ratings', methods=['GET'])
def get_elo_ratings():
    """Vraća ELO rejtinge timova"""
    elo_data = []
    for team, strength in TEAM_STRENGTH.items():
        elo_data.append({
            'team': team,
            'elo_rating': int(1500 + strength * 500),
            'fifa_ranking': random.randint(1, 50),
            'world_cup_experience': random.randint(1, 5)
        })
    return jsonify(elo_data)


# ============================================
# POKRETANJE SERVERA
# ============================================
if __name__ == '__main__':
    print(f"\n🚀 Server running on http://localhost:5000")
    print(f"📊 {len(TEAMS)} timova učitano")
    print(f"⚡ Model: XGBoost Classifier")
    print(f"🔄 Live rezultati: {'Aktivni (token postavljen)' if SPORTMONKS_TOKEN else 'Neaktivni (dodaj SPORTMONKS_TOKEN u .env)'}")
    print("="*50)
    app.run(debug=True, port=5000)