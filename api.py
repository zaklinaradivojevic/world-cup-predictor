"""
World Cup 2026 Prediction API - Simple version (bez TensorFlow)
Radi na Python 3.14 bez dodatnih biblioteka
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ============================================
# LISTA TIMOVA ZA SP 2026
# ============================================
TEAMS = [
    "Brazil", "Argentina", "France", "Germany", "Spain", "England",
    "Netherlands", "Portugal", "Belgium", "Croatia", "Italy", "Uruguay",
    "Mexico", "USA", "Japan", "Morocco", "Senegal", "Australia",
    "South Africa", "South Korea", "Colombia", "Switzerland", "Poland",
    "Chile", "Nigeria", "Sweden", "Denmark", "Austria", "Czech Republic"
]

# ============================================
# JAČINA TIMOVA (0-1 skala)
# ============================================
TEAM_STRENGTH = {
    'Brazil': 0.95,
    'Argentina': 0.93,
    'France': 0.92,
    'Germany': 0.90,
    'Spain': 0.89,
    'England': 0.88,
    'Netherlands': 0.85,
    'Portugal': 0.84,
    'Belgium': 0.83,
    'Croatia': 0.80,
    'Italy': 0.82,
    'Uruguay': 0.78,
    'Mexico': 0.75,
    'USA': 0.74,
    'Japan': 0.72,
    'Morocco': 0.70,
    'Senegal': 0.68,
    'Australia': 0.65,
    'South Africa': 0.60,
    'South Korea': 0.62,
    'Colombia': 0.73,
    'Switzerland': 0.69,
    'Poland': 0.67,
    'Chile': 0.66,
    'Nigeria': 0.64,
    'Sweden': 0.63,
    'Denmark': 0.68,
    'Austria': 0.61,
    'Czech Republic': 0.60
}

def get_strength(team):
    """Vraća jačinu tima (default 0.65)"""
    return TEAM_STRENGTH.get(team, 0.65)

# ============================================
# ENDPOINT 1: Lista timova
# ============================================
@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Vraća listu svih timova"""
    return jsonify({'teams': TEAMS})

# ============================================
# ENDPOINT 2: Predikcija utakmice
# ============================================
@app.route('/api/predict', methods=['POST'])
def predict():
    """Predviđa ishod utakmice na osnovu jačine timova i domaćeg terena"""
    
    data = request.json
    team1 = data.get('team1')
    team2 = data.get('team2')
    venue = data.get('venue', 'neutral')
    
    # Validacija
    if not team1 or not team2:
        return jsonify({'error': 'Nedostaju timovi'}), 400
    
    if team1 == team2:
        return jsonify({'error': 'Timovi moraju biti različiti'}), 400
    
    # Dohvati jačinu timova
    strength1 = get_strength(team1)
    strength2 = get_strength(team2)
    
    # Faktor domaćeg terena
    home_factor = {
        'home': 1.20,      # Domaćin ima 20% prednosti
        'neutral': 1.00,   # Neutralan teren
        'away': 0.85       # Gost ima 15% hendikepa
    }.get(venue, 1.00)
    
    # Izračunaj verovatnoće
    adjusted_strength1 = strength1 * home_factor
    total = adjusted_strength1 + strength2
    
    home_win = (adjusted_strength1 / total) * 0.7 + 0.15
    away_win = (strength2 / total) * 0.7 + 0.15
    draw = 1 - home_win - away_win
    
    # Normalizacija (da zbir bude 100%)
    total_prob = home_win + draw + away_win
    home_win = home_win / total_prob
    draw = draw / total_prob
    away_win = away_win / total_prob
    
    # Odredi pobednika
    if home_win > draw and home_win > away_win:
        winner = team1
        confidence = home_win
    elif away_win > home_win and away_win > draw:
        winner = team2
        confidence = away_win
    else:
        winner = "Nerešeno"
        confidence = draw
    
    # Vrati rezultat
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
        'venue': venue,
        'model_used': 'Strength-based simulation'
    })

# ============================================
# ENDPOINT 3: Health check
# ============================================
@app.route('/api/health', methods=['GET'])
def health():
    """Provera statusa servera"""
    return jsonify({
        'status': 'ok',
        'teams_count': len(TEAMS),
        'message': 'World Cup 2026 Prediction API is running'
    })

# ============================================
# POKRETANJE SERVERA
# ============================================
if __name__ == '__main__':
    print("=" * 50)
    print("🏆 WORLD CUP 2026 PREDICTION API")
    print("=" * 50)
    print(f"🚀 Server running on http://localhost:5000")
    print(f"📊 {len(TEAMS)} timova učitano")
    print(f"⚡ Model: Strength-based simulation")
    print("=" * 50)
    print("\nDostupni endpointi:")
    print("  GET  /api/teams     - Lista timova")
    print("  POST /api/predict   - Predikcija utakmice")
    print("  GET  /api/health    - Health check")
    print("\n" + "=" * 50)
    
    app.run(debug=True, port=5000)