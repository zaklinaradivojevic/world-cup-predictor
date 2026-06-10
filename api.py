from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.features.feature_engineering import FeatureEngineer
from backend.models.ensemble_model import EnsemblePredictor
from backend.utils.tournament_manager import TournamentManager
from backend.config import Config
import pandas as pd
import json

app = Flask(__name__)
CORS(app)

# Inicijalizacija
engineer = FeatureEngineer()
predictor = EnsemblePredictor()
tournament_manager = TournamentManager()

# Pokušaj da učitaš istrenirani model
try:
    predictor.load_models()
    print("✅ Ensemble model učitan")
except:
    print("⚠️ Model nije pronađen, pokreni train_model.py prvo")

# Učitaj konfiguraciju turnira
AVAILABLE_TOURNAMENTS = list(Config.COMPETITIONS.keys())

@app.route('/api/tournaments', methods=['GET'])
def get_tournaments():
    """Vraća listu dostupnih turnira"""
    return jsonify({
        'tournaments': AVAILABLE_TOURNAMENTS,
        'competitions': Config.COMPETITIONS
    })

@app.route('/api/load-tournament', methods=['POST'])
def load_tournament():
    """Učitava specifičan turnir"""
    data = request.json
    tournament_name = data.get('tournament_name')
    season = data.get('season', '2026')
    
    if tournament_name not in AVAILABLE_TOURNAMENTS:
        return jsonify({'error': 'Turnir nije pronađen'}), 404
    
    # Učitaj podatke za turnir (skraćeno za demo)
    tournament_manager.register_tournament(tournament_name, {
        'name': tournament_name,
        'season': season,
        'teams': Config.COMPETITIONS[tournament_name].get('teams', 32)
    })
    
    return jsonify({
        'message': f'Turnir {tournament_name} {season} učitan',
        'tournament': tournament_name,
        'season': season
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """Predviđa ishod utakmice (sada ensemble modelom)"""
    data = request.json
    team1 = data.get('team1')
    team2 = data.get('team2')
    tournament = data.get('tournament', 'World Cup')
    
    # Kreiraj feature-ove (za demo koristi mock podatke)
    mock_data = pd.DataFrame({
        'team1': [team1],
        'team2': [team2],
        'venue': ['neutral'],
        'result': ['D']  # dummy
    })
    
    X, _ = engineer.create_all_features(mock_data)
    
    # Predikcija ensemble modelom
    probas = predictor.predict_proba(X)[0]
    
    # Mapiramo klase: 0 = gost pobedio, 1 = nerešeno, 2 = domaćin pobedio
    home_win_prob = probas[2] if len(probas) > 2 else probas[1]
    draw_prob = probas[1] if len(probas) > 2 else probas[0]
    away_win_prob = probas[0] if len(probas) > 2 else probas[0]
    
    if home_win_prob > draw_prob and home_win_prob > away_win_prob:
        winner = team1
        confidence = home_win_prob
    elif away_win_prob > home_win_prob and away_win_prob > draw_prob:
        winner = team2
        confidence = away_win_prob
    else:
        winner = "Nerešeno"
        confidence = draw_prob
    
    return jsonify({
        'team1': team1,
        'team2': team2,
        'tournament': tournament,
        'winner': winner,
        'confidence': round(confidence * 100, 1),
        'probabilities': {
            f'{team1}_win': round(home_win_prob * 100, 1),
            'draw': round(draw_prob * 100, 1),
            f'{team2}_win': round(away_win_prob * 100, 1)
        },
        'model_used': 'ensemble (XGBoost+RF+NeuralNet)'
    })

@app.route('/api/feature-importance', methods=['GET'])
def feature_importance():
    """Vraća važnost feature-a za XGBoost model"""
    if predictor.xgb_model is not None:
        importance = predictor.xgb_model.feature_importances_
        features = engineer.feature_names
        
        sorted_idx = np.argsort(importance)[::-1][:20]
        
        return jsonify({
            'features': [features[i] for i in sorted_idx],
            'importance': [float(importance[i]) for i in sorted_idx]
        })
    
    return jsonify({'error': 'Model nije učitan'}), 404

@app.route('/api/hyperparameters', methods=['GET'])
def get_hyperparameters():
    """Vraća korišćene hyperparametre za modele"""
    return jsonify({
        'xgboost': predictor.xgb_model.get_params() if predictor.xgb_model else None,
        'random_forest': predictor.rf_model.get_params() if predictor.rf_model else None,
        'config': {
            'xgboost_grid': Config.XGBOOST_GRID,
            'rf_grid': Config.RF_GRID,
            'cv_folds': Config.CV_FOLDS
        }
    })

if __name__ == '__main__':
    print("🏆 UNIVERZALNI FUTBAL PREDIKCIONI SISTEM")
    print("🚀 Server running on http://localhost:5000")
    print(f"📊 Dostupni turniri: {', '.join(AVAILABLE_TOURNAMENTS)}")
    print("⚡ Ensemble model: XGBoost + Random Forest + Neural Network")
    app.run(debug=True, port=5000)