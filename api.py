"""
API sa XGBoost modelom - prave ML predikcije
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import os

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
        'teams_count': len(TEAMS)
    })

if __name__ == '__main__':
    print(f"\n🚀 Server running on http://localhost:5000")
    print(f"📊 {len(TEAMS)} timova učitano")
    print(f"⚡ Model: XGBoost Classifier")
    print("="*50)
    app.run(debug=True, port=5000)