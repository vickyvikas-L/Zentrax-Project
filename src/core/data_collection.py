import cv2
import mediapipe as mp
import numpy as np
import os
import time
import json
import speech_recognition as sr
from whisper_handler import HybridRecognizer

class DataCollector:
    def __init__(self, use_whisper=True):
        # Create directories for data storage
        self.base_dir = "training_data"
        self.gesture_dir = os.path.join(self.base_dir, "gestures")
        self.voice_dir = os.path.join(self.base_dir, "voice_commands")
        
        os.makedirs(self.gesture_dir, exist_ok=True)
        os.makedirs(self.voice_dir, exist_ok=True)
        
        # Initialize MediaPipe hands
        if hasattr(mp, 'solutions'):
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mp_drawing = mp.solutions.drawing_utils
        else:
            self.mp_hands = None
            self.hands = None
            self.mp_drawing = None
        
        # Initialize speech recognition with Whisper support
        self.use_whisper = use_whisper
        if use_whisper:
            self.hybrid_recognizer = HybridRecognizer(use_whisper=True, whisper_model="base")
            self.recognizer = self.hybrid_recognizer.recognizer
        else:
            self.recognizer = sr.Recognizer()
            self.hybrid_recognizer = None
        self.microphone = sr.Microphone()
        
        # Define gestures to collect
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
        
        # Define voice commands to collect
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
    
    def collect_gesture_data(self):
        """Collect hand gesture data from webcam"""
        print("Starting gesture data collection...")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return
        
        for gesture in self.gestures:
            gesture_samples = []
            samples_to_collect = 50
            
            print(f"\nPlease perform the '{gesture}' gesture.")
            print(f"Collecting {samples_to_collect} samples. Press 'c' to start capturing.")
            
            # Wait for user to press 'c' to start
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                cv2.putText(frame, f"Prepare for: {gesture}", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, "Press 'c' to start capturing", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow('Data Collection', frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('c'):
                    break
                elif key == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    return
            
            # Start collecting samples
            sample_count = 0
            while sample_count < samples_to_collect:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Flip the image horizontally for a more intuitive mirror view
                frame = cv2.flip(frame, 1)
                
                # Convert the BGR image to RGB
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process the image and detect hands
                results = self.hands.process(image_rgb)
                
                # Draw hand landmarks and collect data if hand is detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_drawing.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # Extract landmark data
                        landmarks_data = []
                        for landmark in hand_landmarks.landmark:
                            landmarks_data.append({
                                'x': landmark.x,
                                'y': landmark.y,
                                'z': landmark.z
                            })
                        
                        # Add sample
                        gesture_samples.append(landmarks_data)
                        sample_count += 1
                        
                        # Display progress
                        cv2.putText(frame, f"Samples: {sample_count}/{samples_to_collect}", 
                                   (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow('Data Collection', frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                
                # Add a small delay to avoid duplicate frames
                time.sleep(0.1)
            
            # Save collected samples
            if gesture_samples:
                file_path = os.path.join(self.gesture_dir, f"{gesture}.json")
                with open(file_path, 'w') as f:
                    json.dump(gesture_samples, f)
                print(f"Saved {len(gesture_samples)} samples for '{gesture}'")
        
        cap.release()
        cv2.destroyAllWindows()
        print("Gesture data collection completed!")
    
    def collect_voice_data(self):
        """Collect voice command data"""
        print("Starting voice command data collection...")
        
        for command in self.voice_commands:
            command_samples = []
            samples_to_collect = 10
            
            print(f"\nPlease say the command: '{command}'")
            print(f"Collecting {samples_to_collect} samples. Press Enter to start recording each sample.")
            
            sample_count = 0
            while sample_count < samples_to_collect:
                input(f"Press Enter to record sample {sample_count + 1}/{samples_to_collect}...")
                
                try:
                    with self.microphone as source:
                        print("Listening...")
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    
                    # Save audio data
                    audio_file = os.path.join(self.voice_dir, f"{command}_{sample_count}.wav")
                    with open(audio_file, "wb") as f:
                        f.write(audio.get_wav_data())
                    
                    # Try to recognize and verify using Whisper or Google
                    try:
                        if self.use_whisper and self.hybrid_recognizer:
                            text = self.hybrid_recognizer.recognize(audio).lower()
                        else:
                            text = self.recognizer.recognize_google(audio).lower()
                        print(f"Recognized: {text}")
                        
                        # Store the recognized text
                        command_samples.append({
                            'audio_file': audio_file,
                            'recognized_text': text,
                            'expected_command': command
                        })
                        
                        sample_count += 1
                        
                    except sr.UnknownValueError:
                        print("Could not understand audio. Please try again.")
                    except sr.RequestError as e:
                        print(f"Could not request results; {e}")
                        
                except Exception as e:
                    print(f"Error recording audio: {e}")
            
            # Save metadata
            metadata_file = os.path.join(self.voice_dir, f"{command}_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(command_samples, f)
            
            print(f"Saved {len(command_samples)} samples for '{command}'")
        
        print("Voice data collection completed!")
    
    def run(self):
        """Run the data collection process"""
        print("=== Windows Control Data Collection Tool ===")
        print("This tool will help you collect training data for the Windows Voice and Gesture Control system.")
        
        while True:
            print("\nSelect an option:")
            print("1. Collect gesture data")
            print("2. Collect voice command data")
            print("3. Exit")
            
            choice = input("Enter your choice (1-3): ")
            
            if choice == '1':
                self.collect_gesture_data()
            elif choice == '2':
                self.collect_voice_data()
            elif choice == '3':
                print("Exiting data collection tool.")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    collector = DataCollector()
    collector.run()