"""
Zentrax AI Assistant Module
An AI assistant with FRIDAY-like functionality (inspired by Iron Man)

This module provides:
- Text-to-speech voice responses
- AI personality and greetings
- Status updates and notifications
- Natural conversation abilities
"""

import os
import random
import subprocess
import threading
import queue
from datetime import datetime
from typing import Optional

# Try to import pyttsx3 for text-to-speech
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️  pyttsx3 not installed. Voice responses disabled. Install with: pip install pyttsx3")


class TTSWorker:
    """Background worker for text-to-speech to avoid blocking and conflicts."""
    
    def __init__(self, voice_speed: int = 175, voice_type: str = "female"):
        self.voice_speed = voice_speed
        self.voice_type = voice_type
        self.speech_queue = queue.Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def _worker_loop(self):
        """Worker loop that processes speech requests in a dedicated thread."""
        while self.running:
            try:
                text = self.speech_queue.get(timeout=0.5)
                if text is None:  # Shutdown signal
                    break
                self._speak_text(text)
                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠️  TTS worker error: {e}")
    
    def _speak_text(self, text: str):
        """Actually speak the text using pyttsx3."""
        if not TTS_AVAILABLE:
            return
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self.voice_speed)
            engine.setProperty('volume', 1.0)
            
            # Set voice
            voices = engine.getProperty('voices')
            for voice in voices:
                if self.voice_type == "female" and ("zira" in voice.name.lower() or "hazel" in voice.name.lower()):
                    engine.setProperty('voice', voice.id)
                    break
                elif self.voice_type == "male" and ("david" in voice.name.lower() or "mark" in voice.name.lower()):
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"⚠️  Speech error: {e}")
    
    def speak(self, text: str):
        """Queue text for speaking."""
        self.speech_queue.put(text)
    
    def stop(self):
        """Stop the TTS worker."""
        self.running = False
        self.speech_queue.put(None)


class FridayAssistant:
    """
    Zentrax AI Assistant - Your personal Windows AI with FRIDAY-like functionality
    """
    
    # Personality responses
    GREETINGS = [
        "Hello! How can I help you today?",
        "Hey there! What would you like me to do?",
        "At your service. What do you need?",
        "Good to see you! How may I assist?",
        "Online and ready. What's on your mind?",
    ]
    
    ACKNOWLEDGMENTS = [
        "On it.",
        "Right away.",
        "Consider it done.",
        "Working on it.",
        "Executing now.",
        "Done.",
        "I've got that handled.",
    ]
    
    CONFIRMATIONS = [
        "All done.",
        "Task completed successfully.",
        "That's taken care of.",
        "Finished.",
        "Complete.",
    ]
    
    ERRORS = [
        "I ran into a problem with that.",
        "Something went wrong. Let me know if you want me to try again.",
        "I couldn't complete that task.",
        "That didn't work as expected.",
        "There was an issue executing that command.",
    ]
    
    FAREWELLS = [
        "Going offline. Have a great day!",
        "Shutting down. Call me if you need anything.",
        "See you later!",
        "Until next time.",
        "Goodbye! Stay awesome.",
    ]
    
    THINKING = [
        "Let me check that for you.",
        "One moment please.",
        "Processing your request.",
        "Looking into that now.",
    ]
    
    # Time-based greetings
    MORNING_GREETINGS = [
        "Good morning! Ready to start the day?",
        "Morning! What's on the agenda today?",
        "Good morning! How can I help you this fine day?",
    ]
    
    AFTERNOON_GREETINGS = [
        "Good afternoon! How can I assist?",
        "Afternoon! What do you need?",
        "Good afternoon! Ready when you are.",
    ]
    
    EVENING_GREETINGS = [
        "Good evening! Still working hard?",
        "Evening! What can I do for you?",
        "Good evening! How may I help?",
    ]
    
    NIGHT_GREETINGS = [
        "Working late? I'm here to help.",
        "Burning the midnight oil? What do you need?",
        "Late night session? I've got your back.",
    ]
    
    def __init__(self, voice_enabled: bool = True, voice_speed: int = 175, voice_type: str = "female", name: str = "Zentrax"):
        """
        Initialize Zentrax AI assistant (FRIDAY-like functionality).
        
        Args:
            voice_enabled: Whether to speak responses aloud
            voice_speed: Speech rate (words per minute)
            voice_type: "male" or "female" voice
            name: The name of the assistant (default: Zentrax)
        """
        self.voice_enabled = voice_enabled and TTS_AVAILABLE
        self.voice_speed = voice_speed
        self.voice_type = voice_type
        self.name = name
        
        # Initialize TTS worker (runs in separate thread to avoid audio conflicts)
        if self.voice_enabled:
            try:
                self.tts_worker = TTSWorker(voice_speed=voice_speed, voice_type=voice_type)
                print(f"🔊 {self.name} voice system initialized")
            except Exception as e:
                print(f"⚠️  Voice initialization failed: {e}")
                self.voice_enabled = False
                self.tts_worker = None
        else:
            self.tts_worker = None
    
    def speak(self, text: str, print_text: bool = True):
        """
        Speak text aloud and optionally print it.
        
        Args:
            text: The text to speak
            print_text: Whether to also print the text
        """
        if print_text:
            print(f"🤖 {self.name}: {text}")
        
        if self.voice_enabled and self.tts_worker:
            self.tts_worker.speak(text)
    
    def greet(self) -> str:
        """Get a time-appropriate greeting."""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            greeting = random.choice(self.MORNING_GREETINGS)
        elif 12 <= hour < 17:
            greeting = random.choice(self.AFTERNOON_GREETINGS)
        elif 17 <= hour < 21:
            greeting = random.choice(self.EVENING_GREETINGS)
        else:
            greeting = random.choice(self.NIGHT_GREETINGS)
        
        self.speak(greeting)
        return greeting
    
    def acknowledge(self) -> str:
        """Acknowledge a command before executing."""
        response = random.choice(self.ACKNOWLEDGMENTS)
        self.speak(response)
        return response
    
    def confirm(self, details: Optional[str] = None) -> str:
        """Confirm task completion."""
        response = random.choice(self.CONFIRMATIONS)
        if details:
            response = f"{response} {details}"
        self.speak(response)
        return response
    
    def report_error(self, details: Optional[str] = None) -> str:
        """Report an error."""
        response = random.choice(self.ERRORS)
        if details:
            response = f"{response} {details}"
        self.speak(response)
        return response
    
    def farewell(self) -> str:
        """Say goodbye."""
        response = random.choice(self.FAREWELLS)
        self.speak(response)
        return response
    
    def thinking(self) -> str:
        """Indicate processing."""
        response = random.choice(self.THINKING)
        self.speak(response)
        return response
    
    def report_status(self, status_type: str, value: str):
        """Report system status in natural language."""
        status_messages = {
            "battery": f"Battery is at {value}.",
            "time": f"The time is {value}.",
            "date": f"Today is {value}.",
            "cpu": f"CPU usage is at {value}.",
            "memory": f"Memory usage is at {value}.",
            "disk": f"Disk space is at {value}.",
            "wifi": f"WiFi status: {value}.",
        }
        
        message = status_messages.get(status_type, f"{status_type}: {value}")
        self.speak(message)
        return message
    
    def introduce(self):
        """Introduce FRIDAY."""
        intro = (
            f"Hello, I'm {self.name}, your personal AI assistant. "
            "I can help you control your computer with voice commands and gestures. "
            "Just say my name followed by what you need!"
        )
        self.speak(intro)
        return intro
    
    def help_message(self):
        """Provide help information."""
        help_text = """
I can help you with:
- Opening apps: "Open Chrome", "Launch VS Code"
- Files: "Create a file", "Search for PDFs"
- System: "What's my battery?", "Take a screenshot"
- Web: "Search for Python tutorials"
- Control: "Volume up", "Lock screen"
- Window: "Minimize", "Switch window"

Just speak naturally and I'll understand!
        """
        self.speak(help_text.strip())
        return help_text
    
    def respond_to_thanks(self):
        """Respond to thank you."""
        responses = [
            "You're welcome!",
            "Happy to help!",
            "Anytime!",
            "My pleasure!",
            "Of course!",
        ]
        response = random.choice(responses)
        self.speak(response)
        return response
    
    def respond_to_compliment(self):
        """Respond to compliments."""
        responses = [
            "Thank you! I try my best.",
            "That's very kind of you!",
            "I appreciate that!",
            "You're making my circuits blush!",
            "Glad I could help!",
        ]
        response = random.choice(responses)
        self.speak(response)
        return response
    
    def not_understood(self):
        """Indicate command wasn't understood."""
        responses = [
            "I didn't quite catch that. Could you repeat?",
            "Sorry, I'm not sure what you mean. Can you try again?",
            "I didn't understand that command. Could you rephrase?",
            "Hmm, I'm not sure how to help with that. Try asking differently?",
        ]
        response = random.choice(responses)
        self.speak(response)
        return response
    
    def set_voice_enabled(self, enabled: bool):
        """Enable or disable voice."""
        self.voice_enabled = enabled and TTS_AVAILABLE
        if enabled:
            self.speak("Voice enabled.")
        else:
            print(f"🤖 {self.name}: Voice disabled.")
    
    def set_voice_speed(self, speed: int):
        """Set speech rate."""
        self.voice_speed = speed
        if self.engine:
            self.engine.setProperty('rate', speed)
    
    def list_voices(self):
        """List available voices."""
        if self.engine:
            voices = self.engine.getProperty('voices')
            print("\n📢 Available voices:")
            for idx, voice in enumerate(voices):
                print(f"  {idx}: {voice.name}")
            return voices
        return []
    
    def set_voice_by_index(self, index: int):
        """Set voice by index."""
        if self.engine:
            voices = self.engine.getProperty('voices')
            if 0 <= index < len(voices):
                self.engine.setProperty('voice', voices[index].id)
                self.speak("Voice changed successfully.")


class SystemMonitor:
    """
    System monitoring capabilities for FRIDAY.
    Provides real-time system information.
    """
    
    @staticmethod
    def get_battery_info() -> dict:
        """Get battery information."""
        try:
            result = subprocess.run(
                ["powershell", "-Command", 
                 "(Get-WmiObject Win32_Battery).EstimatedChargeRemaining"],
                capture_output=True, text=True, timeout=5
            )
            percent = result.stdout.strip()
            
            result2 = subprocess.run(
                ["powershell", "-Command",
                 "(Get-WmiObject Win32_Battery).BatteryStatus"],
                capture_output=True, text=True, timeout=5
            )
            status_code = result2.stdout.strip()
            
            status = "Unknown"
            if status_code == "1":
                status = "Discharging"
            elif status_code == "2":
                status = "Charging"
            elif status_code == "3":
                status = "Fully Charged"
            
            return {
                "percent": int(percent) if percent.isdigit() else None,
                "status": status,
                "is_charging": status_code == "2"
            }
        except Exception:
            return {"percent": None, "status": "Unknown", "is_charging": False}
    
    @staticmethod
    def get_cpu_usage() -> float:
        """Get CPU usage percentage."""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-WmiObject Win32_Processor).LoadPercentage"],
                capture_output=True, text=True, timeout=5
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0
    
    @staticmethod
    def get_memory_info() -> dict:
        """Get memory/RAM information."""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-WmiObject Win32_OperatingSystem | "
                 "Select-Object FreePhysicalMemory,TotalVisibleMemorySize | "
                 "ForEach-Object { $_.FreePhysicalMemory, $_.TotalVisibleMemorySize }"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                free_kb = int(lines[0].strip())
                total_kb = int(lines[1].strip())
                used_kb = total_kb - free_kb
                percent_used = (used_kb / total_kb) * 100
                return {
                    "total_gb": round(total_kb / 1024 / 1024, 2),
                    "used_gb": round(used_kb / 1024 / 1024, 2),
                    "free_gb": round(free_kb / 1024 / 1024, 2),
                    "percent_used": round(percent_used, 1)
                }
        except Exception:
            pass
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent_used": 0}
    
    @staticmethod
    def get_disk_info(drive: str = "C:") -> dict:
        """Get disk space information."""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 f"Get-WmiObject Win32_LogicalDisk -Filter 'DeviceID=\"{drive}\"' | "
                 "Select-Object FreeSpace,Size | "
                 "ForEach-Object { $_.FreeSpace, $_.Size }"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                free_bytes = int(lines[0].strip())
                total_bytes = int(lines[1].strip())
                used_bytes = total_bytes - free_bytes
                percent_used = (used_bytes / total_bytes) * 100
                return {
                    "drive": drive,
                    "total_gb": round(total_bytes / 1024**3, 2),
                    "used_gb": round(used_bytes / 1024**3, 2),
                    "free_gb": round(free_bytes / 1024**3, 2),
                    "percent_used": round(percent_used, 1)
                }
        except Exception:
            pass
        return {"drive": drive, "total_gb": 0, "used_gb": 0, "free_gb": 0, "percent_used": 0}
    
    @staticmethod
    def get_running_processes(top_n: int = 10) -> list:
        """Get top running processes by memory usage."""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 f"Get-Process | Sort-Object WorkingSet64 -Descending | "
                 f"Select-Object -First {top_n} Name,@{{Name='MemoryMB';Expression={{[math]::Round($_.WorkingSet64/1MB,0)}}}} | "
                 "Format-Table -HideTableHeaders"],
                capture_output=True, text=True, timeout=10
            )
            processes = []
            for line in result.stdout.strip().split('\n'):
                parts = line.strip().split()
                if len(parts) >= 2:
                    processes.append({
                        "name": parts[0],
                        "memory_mb": int(parts[-1]) if parts[-1].isdigit() else 0
                    })
            return processes
        except Exception:
            return []
    
    @staticmethod
    def get_network_status() -> dict:
        """Get network/WiFi status."""
        try:
            # Check if connected to internet
            result = subprocess.run(
                ["powershell", "-Command",
                 "Test-Connection google.com -Count 1 -Quiet"],
                capture_output=True, text=True, timeout=10
            )
            is_connected = result.stdout.strip().lower() == "true"
            
            # Get WiFi network name
            result2 = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=5
            )
            ssid = "Unknown"
            for line in result2.stdout.split('\n'):
                if "SSID" in line and "BSSID" not in line:
                    ssid = line.split(':')[-1].strip()
                    break
            
            return {
                "connected": is_connected,
                "wifi_name": ssid if ssid else "Unknown",
                "status": "Connected" if is_connected else "Disconnected"
            }
        except Exception:
            return {"connected": False, "wifi_name": "Unknown", "status": "Unknown"}
    
    @staticmethod  
    def get_bluetooth_status() -> dict:
        """Get Bluetooth status."""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq 'OK'} | Select-Object -First 1"],
                capture_output=True, text=True, timeout=5
            )
            is_enabled = len(result.stdout.strip()) > 0
            return {
                "enabled": is_enabled,
                "status": "Enabled" if is_enabled else "Disabled"
            }
        except Exception:
            return {"enabled": False, "status": "Unknown"}


# Quick test
if __name__ == "__main__":
    print("Testing FRIDAY Assistant...")
    print("=" * 50)
    
    friday = FridayAssistant(voice_enabled=True)
    friday.introduce()
    friday.greet()
    
    print("\n📊 System Status:")
    print("-" * 30)
    
    monitor = SystemMonitor()
    
    battery = monitor.get_battery_info()
    print(f"🔋 Battery: {battery['percent']}% ({battery['status']})")
    friday.report_status("battery", f"{battery['percent']} percent")
    
    cpu = monitor.get_cpu_usage()
    print(f"💻 CPU: {cpu}%")
    
    memory = monitor.get_memory_info()
    print(f"💾 RAM: {memory['used_gb']}GB / {memory['total_gb']}GB ({memory['percent_used']}%)")
    
    disk = monitor.get_disk_info()
    print(f"💿 Disk C: {disk['used_gb']}GB / {disk['total_gb']}GB ({disk['percent_used']}%)")
    
    network = monitor.get_network_status()
    print(f"🌐 Network: {network['status']} ({network['wifi_name']})")
    
    print("\n" + "=" * 50)
    friday.farewell()
