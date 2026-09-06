"""
Zentrax Application Builder
Converts the Python project into a standalone Windows executable.
Run this from the project root: python scripts/build_app.py
"""

import subprocess
import sys
import os

# Ensure we're in the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

def install_pyinstaller():
    """Install PyInstaller if not available."""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")

def build_exe():
    """Build the executable using PyInstaller."""
    print("\n🔨 Building Zentrax Application...")
    print("=" * 50)
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Zentrax",
        "--onedir",  # Create a folder with all dependencies (faster startup)
        # "--onefile",  # Uncomment for single .exe (slower startup)
        "--windowed",  # No console window (comment out if you want to see logs)
        "--icon=zentrax.ico",  # Icon file (if exists)
        "--add-data=training_data;training_data",  # Include training data
        "--add-data=frontend;frontend",  # Include frontend files
        "--add-data=src;src",  # Include source modules
        "--hidden-import=pyttsx3.drivers",
        "--hidden-import=pyttsx3.drivers.sapi5",
        "--hidden-import=speech_recognition",
        "--hidden-import=whisper",
        "--hidden-import=mediapipe",
        "--hidden-import=cv2",
        "--hidden-import=pyautogui",
        "--hidden-import=numpy",
        "--hidden-import=torch",
        "--collect-all=mediapipe",
        "--collect-all=whisper",
        "main.py"
    ]
    
    # Remove icon argument if icon doesn't exist
    if not os.path.exists("zentrax.ico"):
        cmd = [c for c in cmd if not c.startswith("--icon")]
        print("⚠️  No icon file found. Using default icon.")
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 50)
        print("✅ Build complete!")
        print("\n📁 Your application is in: dist/Zentrax/")
        print("🚀 Run: dist/Zentrax/Zentrax.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        print("\nTry running with console mode:")
        print("  python build_app.py --console")

def build_console_exe():
    """Build with console window visible (for debugging)."""
    print("\n🔨 Building Zentrax (Console Mode)...")
    print("=" * 50)
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Zentrax",
        "--onedir",
        "--console",  # Show console for debugging
        "--add-data=training_data;training_data",
        "--add-data=frontend;frontend",
        "--hidden-import=pyttsx3.drivers",
        "--hidden-import=pyttsx3.drivers.sapi5",
        "--hidden-import=speech_recognition",
        "--hidden-import=whisper",
        "--hidden-import=mediapipe",
        "--hidden-import=cv2",
        "--hidden-import=pyautogui",
        "--hidden-import=numpy",
        "--hidden-import=torch",
        "--collect-all=mediapipe",
        "--collect-all=whisper",
        "main.py"
    ]
    
    if os.path.exists("zentrax.ico"):
        cmd.insert(-1, "--icon=zentrax.ico")
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 50)
        print("✅ Build complete!")
        print("\n📁 Your application is in: dist/Zentrax/")
        print("🚀 Run: dist/Zentrax/Zentrax.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("   ZENTRAX APPLICATION BUILDER")
    print("=" * 50)
    
    install_pyinstaller()
    
    if "--console" in sys.argv:
        build_console_exe()
    else:
        build_exe()
