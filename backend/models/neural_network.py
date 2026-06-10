"""
Neural Network Model - Deep learning za predikciju fudbalskih utakmica
Koristi TensorFlow/Keras
"""

import numpy as np
from sklearn.metrics import accuracy_score
import json
import os
from typing import Dict, Optional, Tuple

# Pokušaj import-ovati TensorFlow
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    print("⚠️ TensorFlow nije instaliran. Koristi: pip install tensorflow")
    TF_AVAILABLE = False

class NeuralNetworkModel:
    """
    Neural Network klasifikator za predikciju ishoda utakmice
    Arhitektura: 4 sloja sa Dropout i BatchNormalization
    """
    
    def __init__(self, input_dim: int, random_state: int = 42):
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow nije instaliran. Instalirajte sa: pip install tensorflow")
        
        self.input_dim = input_dim
        self.random_state = random_state
        self.model = None
        self.history = None
        self.is_trained = False
        
        # Seed za reproduktivnost
        tf.random.set_seed(random_state)
    
    def build_model(self) -> Sequential:
        """
        Kreira arhitekturu neuralne mreže
        
        Arhitektura:
        - Input layer → BatchNorm → Dropout
        - Hidden layer 1 (256) → BatchNorm → Dropout
        - Hidden layer 2 (128) → BatchNorm → Dropout  
        - Hidden layer 3 (64) → BatchNorm
        - Output layer (3) → Softmax
        """
        model = Sequential([
            # Input layer
            Dense(256, activation='relu', input_shape=(self.input_dim,)),
            BatchNormalization(),
            Dropout(0.3),
            
            # Hidden layer 1
            Dense(128, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            
            # Hidden layer 2
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.2),
            
            # Hidden layer 3
            Dense(32, activation='relu'),
            BatchNormalization(),
            
            # Output layer (3 klase: away_win, draw, home_win)
            Dense(3, activation='softmax')
        ])
        
        # Kompajliraj model
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 100,
              batch_size: int = 32,
              early_stopping_patience: int = 10) -> Dict:
        """
        Trenira neuralnu mrežu
        
        Args:
            X_train, y_train: Trening podaci
            X_val, y_val: Validacioni podaci (neophodni za early stopping)
            epochs: Maksimalan broj epoha
            batch_size: Veličina batch-a
            early_stopping_patience: Zaustavljanje ako nema poboljšanja
        
        Returns:
            Dict: Istorija treninga
        """
        print("🧠 Treniram Neural Network model...")
        
        # Build model
        self.model = self.build_model()
        
        # Callbacks
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=early_stopping_patience,
            restore_best_weights=True,
            verbose=1
        )
        
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=0.00001,
            verbose=0
        )
        
        # Trening
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, reduce_lr],
            verbose=0
        )
        
        self.is_trained = True
        
        # Evaluacija
        train_pred = np.argmax(self.predict_proba(X_train), axis=1)
        train_acc = accuracy_score(y_train, train_pred)
        
        val_pred = np.argmax(self.predict_proba(X_val), axis=1)
        val_acc = accuracy_score(y_val, val_pred)
        
        print(f"✅ Neural Network istreniran (trening: {train_acc:.2%}, validacija: {val_acc:.2%})")
        print(f"   Završeno epoha: {len(self.history.history['loss'])}/{epochs}")
        
        # Izračunaj feature importance (koristeći permutaciju)
        feature_importance = self._calculate_permutation_importance(X_val, y_val)
        
        return {
            'train_accuracy': train_acc,
            'validation_accuracy': val_acc,
            'epochs_completed': len(self.history.history['loss']),
            'history': {
                'loss': self.history.history['loss'],
                'val_loss': self.history.history['val_loss'],
                'accuracy': self.history.history['accuracy'],
                'val_accuracy': self.history.history['val_accuracy']
            },
            'feature_importance': feature_importance
        }
    
    def _calculate_permutation_importance(self, X_val: np.ndarray, y_val: np.ndarray,
                                           n_repeats: int = 5) -> list:
        """
        Izračunava feature importance koristeći permutaciju
        (koliko performanse padaju kada se feature permutira)
        """
        baseline_acc = accuracy_score(y_val, np.argmax(self.predict_proba(X_val), axis=1))
        importance = []
        
        for i in range(self.input_dim):
            scores = []
            for _ in range(n_repeats):
                X_permuted = X_val.copy()
                np.random.shuffle(X_permuted[:, i])
                perm_acc = accuracy_score(y_val, np.argmax(self.predict_proba(X_permuted), axis=1))
                scores.append(baseline_acc - perm_acc)
            importance.append(np.mean(scores))
        
        return importance
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predviđa klase"""
        if not self.is_trained:
            raise ValueError("Model nije istreniran!")
        proba = self.predict_proba(X)
        return np.argmax(proba, axis=1)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predviđa verovatnoće za svaku klasu"""
        if not self.is_trained:
            raise ValueError("Model nije istreniran!")
        return self.model.predict(X, verbose=0)
    
    def get_feature_importance(self, feature_names: list) -> Dict:
        """Vraća feature importance sa imenima"""
        # Ovo zahteva da je feature importance izračunat tokom treninga
        return {}
    
    def save(self, path: str = 'backend/data/models/neural_network.h5'):
        """Čuva model"""
        if not self.is_trained:
            raise ValueError("Model nije istreniran!")
        
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)
        print(f"💾 Neural Network model sačuvan na {path}")
    
    def load(self, path: str = 'backend/data/models/neural_network.h5'):
        """Učitava model"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow nije instaliran!")
        
        from tensorflow.keras.models import load_model
        self.model = load_model(path)
        self.is_trained = True
        print(f"📂 Neural Network model učitan sa {path}")
    
    def get_architecture_summary(self) -> str:
        """Vraća summary arhitekture"""
        if self.model is None:
            return "Model nije kreiran"
        
        # Dohvati summary kao string
        from io import StringIO
        stream = StringIO()
        self.model.summary(print_fn=lambda x: stream.write(x + '\n'))
        return stream.getvalue()


# Testiranje
if __name__ == "__main__":
    if TF_AVAILABLE:
        # Mock podaci
        X_train = np.random.rand(100, 10)
        y_train = np.random.randint(0, 3, 100)
        X_val = np.random.rand(50, 10)
        y_val = np.random.randint(0, 3, 50)
        
        model = NeuralNetworkModel(input_dim=10)
        model.train(X_train, y_train, X_val, y_val, epochs=20)
        
        print(model.get_architecture_summary())
    else:
        print("TensorFlow nije instaliran. Preskačem test.")