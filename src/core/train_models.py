import os
import json
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import tensorflow as tf
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import LSTM, Dense, Dropout # type: ignore
from tensorflow.keras.utils import to_categorical # type: ignore

class ModelTrainer:
    def __init__(self):
        self.base_dir = "training_data"
        self.gesture_dir = os.path.join(self.base_dir, "gestures")
        self.voice_dir = os.path.join(self.base_dir, "voice_commands")
        self.models_dir = os.path.join(self.base_dir, "models")
        
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Define gestures and commands
        self.gestures = [
            "open_palm",
            "closed_fist",
            "pointing",
            "thumbs_up",
            "thumbs_down",
            "swipe_left",
            "swipe_right",
            "pinch"
        ]
        
        self.voice_commands = [
            "open browser",
            "close window",
            "minimize",
            "maximize",
            "volume up",
            "volume down",
            "scroll up",
            "scroll down",
            "take screenshot",
            "exit program"
        ]
    
    def load_gesture_data(self):
        """Load and preprocess gesture data"""
        print("Loading gesture data...")
        
        X = []
        y = []
        
        for i, gesture in enumerate(self.gestures):
            file_path = os.path.join(self.gesture_dir, f"{gesture}.json")
            if not os.path.exists(file_path):
                print(f"Warning: No data file found for gesture '{gesture}'")
                continue
                
            with open(file_path, 'r') as f:
                samples = json.load(f)
            
            for sample in samples:
                # Flatten the landmarks into a feature vector
                features = []
                for landmark in sample:
                    features.extend([landmark['x'], landmark['y'], landmark['z']])
                
                X.append(features)
                y.append(i)  # Use index as the class label
        
        return np.array(X), np.array(y)
    
    def train_gesture_model_rf(self):
        """Train a Random Forest model for gesture recognition"""
        X, y = self.load_gesture_data()
        
        if len(X) == 0:
            print("No gesture data available for training")
            return
        
        print(f"Training gesture model with {len(X)} samples")
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train a Random Forest classifier
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Gesture model accuracy: {accuracy:.4f}")
        print(classification_report(y_test, y_pred, target_names=self.gestures))
        
        # Save the model
        model_path = os.path.join(self.models_dir, "gesture_model_rf.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        print(f"Gesture model saved to {model_path}")
    
    def train_gesture_model_lstm(self):
        """Train an LSTM model for gesture recognition"""
        X, y = self.load_gesture_data()
        
        if len(X) == 0:
            print("No gesture data available for training")
            return
        
        # Reshape data for LSTM [samples, time steps, features]
        # For simplicity, we'll treat each landmark as a time step
        n_samples = X.shape[0]
        n_landmarks = 21  # MediaPipe hand tracking has 21 landmarks
        n_features = 3    # x, y, z coordinates
        
        X_reshaped = X.reshape(n_samples, n_landmarks, n_features)
        
        # One-hot encode the labels
        y_categorical = to_categorical(y, num_classes=len(self.gestures))
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X_reshaped, y_categorical, test_size=0.2, random_state=42)
        
        # Build LSTM model
        model = Sequential([
            LSTM(64, input_shape=(n_landmarks, n_features), return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(len(self.gestures), activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Train the model
        print("Training LSTM gesture model...")
        model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            validation_data=(X_test, y_test),
            verbose=1
        )
        
        # Evaluate the model
        loss, accuracy = model.evaluate(X_test, y_test)
        print(f"LSTM Gesture model accuracy: {accuracy:.4f}")
        
        # Save the model
        model_path = os.path.join(self.models_dir, "gesture_model_lstm")
        model.save(model_path)
        
        print(f"LSTM Gesture model saved to {model_path}")
    
    def run(self):
        """Run the model training process"""
        print("=== Windows Control Model Training ===")
        
        while True:
            print("\nSelect an option:")
            print("1. Train Random Forest gesture model")
            print("2. Train LSTM gesture model")
            print("3. Exit")
            
            choice = input("Enter your choice (1-3): ")
            
            if choice == '1':
                self.train_gesture_model_rf()
            elif choice == '2':
                self.train_gesture_model_lstm()
            elif choice == '3':
                print("Exiting model training tool.")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.run()