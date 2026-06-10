import numpy as np
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping
import joblib
from ..config import Config

class NeuralNetworkModel:
    """Neuralna mreža sa TensorFlow/Keras"""
    
    def __init__(self, input_dim):
        self.model = self._build_model(input_dim)
        self.input_dim = input_dim
    
    def _build_model(self, input_dim):
        model = Sequential([
            Dense(256, activation='relu', input_shape=(input_dim,)),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(128, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.2),
            
            Dense(32, activation='relu'),
            Dense(3, activation='softmax')  # 3 klase: pobeda domaćin, nerešeno, pobeda gost
        ])
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, X_train, y_train, X_val, y_val):
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=32,
            callbacks=[early_stop],
            verbose=0
        )
        
        return history
    
    def predict_proba(self, X):
        return self.model.predict(X, verbose=0)
    
    def save(self, path):
        self.model.save(path)
    
    def load(self, path):
        from tensorflow.keras.models import load_model
        self.model = load_model(path)


class EnsemblePredictor:
    """
    Stacking Ensemble koji kombinuje:
    - XGBoost (sa tuniranim parametrima)
    - Random Forest
    - Neural Network
    """
    
    def __init__(self):
        self.xgb_model = None
        self.rf_model = None
        self.nn_model = None
        self.meta_model = LogisticRegression()
        self.is_trained = False
    
    def train(self, X_train, y_train, X_val, y_val):
        """Trenira sve modele i meta-model"""
        
        print("🤖 Treniram XGBoost...")
        self._train_xgboost(X_train, y_train)
        
        print("🌲 Treniram Random Forest...")
        self._train_random_forest(X_train, y_train)
        
        print("🧠 Treniram Neural Network...")
        self.nn_model = NeuralNetworkModel(X_train.shape[1])
        self.nn_model.train(X_train, y_train, X_val, y_val)
        
        print("⚡ Treniram Meta-model (Stacking)...")
        self._train_meta_model(X_train, y_train, X_val, y_val)
        
        self.is_trained = True
        print("✅ Ensemble model uspešno istreniran!")
        
        return self
    
    def _train_xgboost(self, X_train, y_train):
        """Trenira XGBoost sa optimalnim parametrima"""
        from ..utils.hyperparameter_tuning import HyperparameterTuner
        
        tuner = HyperparameterTuner()
        
        # Pokušaj da učitaš najbolje parametre
        best_params = tuner.load_best_params('xgboost')
        
        if best_params is None:
            # Ako nema sačuvanih, koristi default
            best_params = {
                'n_estimators': 300,
                'max_depth': 8,
                'learning_rate': 0.05,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': Config.RANDOM_STATE
            }
        
        self.xgb_model = xgb.XGBClassifier(
            **best_params,
            eval_metric='mlogloss',
            use_label_encoder=False
        )
        
        self.xgb_model.fit(X_train, y_train)
    
    def _train_random_forest(self, X_train, y_train):
        """Trenira Random Forest sa optimalnim parametrima"""
        from ..utils.hyperparameter_tuning import HyperparameterTuner
        
        tuner = HyperparameterTuner()
        best_params = tuner.load_best_params('random_forest')
        
        if best_params is None:
            best_params = {
                'n_estimators': 200,
                'max_depth': 20,
                'min_samples_split': 5,
                'random_state': Config.RANDOM_STATE
            }
        
        self.rf_model = RandomForestClassifier(**best_params)
        self.rf_model.fit(X_train, y_train)
    
    def _train_meta_model(self, X_train, y_train, X_val, y_val):
        """Trenira meta-model na predikcijama osnovnih modela"""
        
        # Dohvati predikcije osnovnih modela
        xgb_pred_train = self.xgb_model.predict_proba(X_train)
        rf_pred_train = self.rf_model.predict_proba(X_train)
        nn_pred_train = self.nn_model.predict_proba(X_train)
        
        # Stack features
        meta_features_train = np.column_stack([
            xgb_pred_train, rf_pred_train, nn_pred_train
        ])
        
        # Validacioni skup za meta-model
        xgb_pred_val = self.xgb_model.predict_proba(X_val)
        rf_pred_val = self.rf_model.predict_proba(X_val)
        nn_pred_val = self.nn_model.predict_proba(X_val)
        
        meta_features_val = np.column_stack([
            xgb_pred_val, rf_pred_val, nn_pred_val
        ])
        
        # Treniraj meta-model
        self.meta_model.fit(meta_features_train, y_train)
        
        # Evaluacija meta-modela
        meta_score = self.meta_model.score(meta_features_val, y_val)
        print(f"📊 Meta-model tačnost na validaciji: {meta_score:.2%}")
    
    def predict_proba(self, X):
        """Predviđa verovatnoće za sve klase"""
        if not self.is_trained:
            raise ValueError("Model nije istreniran!")
        
        # Dohvati predikcije svih modela
        xgb_pred = self.xgb_model.predict_proba(X)
        rf_pred = self.rf_model.predict_proba(X)
        nn_pred = self.nn_model.predict_proba(X)
        
        # Stack features
        meta_features = np.column_stack([xgb_pred, rf_pred, nn_pred])
        
        # Meta-model predikcija
        final_probs = self.meta_model.predict_proba(meta_features)
        
        return final_probs
    
    def predict(self, X):
        """Predviđa klase"""
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)
    
    def save_models(self, base_path='backend/data/models/'):
        """Čuva sve modele"""
        import os
        os.makedirs(base_path, exist_ok=True)
        
        joblib.dump(self.xgb_model, f'{base_path}/xgboost.pkl')
        joblib.dump(self.rf_model, f'{base_path}/random_forest.pkl')
        joblib.dump(self.meta_model, f'{base_path}/meta_model.pkl')
        self.nn_model.save(f'{base_path}/neural_network.h5')
        
        print(f"💾 Modeli sačuvani u {base_path}")
    
    def load_models(self, base_path='backend/data/models/'):
        """Učitava sačuvane modele"""
        self.xgb_model = joblib.load(f'{base_path}/xgboost.pkl')
        self.rf_model = joblib.load(f'{base_path}/random_forest.pkl')
        self.meta_model = joblib.load(f'{base_path}/meta_model.pkl')
        self.nn_model = NeuralNetworkModel(0)
        self.nn_model.load(f'{base_path}/neural_network.h5')
        
        self.is_trained = True
        print("📂 Modeli učitani")