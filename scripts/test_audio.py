"""Test script to verify TTS audio output."""
import pyttsx3
import time

print("Testing Text-to-Speech...")
print("=" * 40)

# Initialize engine
engine = pyttsx3.init()

# Set properties
engine.setProperty('rate', 175)
engine.setProperty('volume', 1.0)

# List voices
voices = engine.getProperty('voices')
print(f"Found {len(voices)} voices:")
for i, voice in enumerate(voices):
    print(f"  {i}: {voice.name}")

# Try speaking
print("\n>>> Speaking: 'Hello, I am Zentrax'")
print("    (You should hear audio now)")
engine.say("Hello, I am Zentrax, your AI assistant")
engine.runAndWait()

print("\n>>> Speaking: 'The time is 3 PM'")
engine.say("The time is 3 PM")
engine.runAndWait()

print("\n" + "=" * 40)
print("Test complete. Did you hear the audio?")
print("If not, check:")
print("  1. System volume is not muted")
print("  2. Speakers/headphones are connected")
print("  3. No other app is blocking audio")
