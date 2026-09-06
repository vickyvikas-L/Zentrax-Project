"""
Zentrax Configuration
Central configuration for all settings.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
TRAINING_DATA_DIR = PROJECT_ROOT / "training_data"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


class ZentraxConfig:
    """Centralized configuration management."""
    
    # Default settings
    DEFAULTS = {
        # Voice Recognition
        "voice": {
            "wake_phrase": "zentrax",
            "wake_variants": ["zentrax", "hey zentrax", "hi zentrax", "ok zentrax", "hello"],
            "energy_threshold": 1500,
            "pause_threshold": 1.0,
            "use_whisper": True,
            "whisper_model": "base",
        },
        
        # Text-to-Speech
        "tts": {
            "enabled": True,
            "voice_speed": 175,
            "voice_type": "female",  # "male" or "female"
            "volume": 1.0,
        },
        
        # Gesture Recognition
        "gesture": {
            "min_detection_confidence": 0.5,
            "min_tracking_confidence": 0.5,
            "cooldown_frames": 30,
        },
        
        # Server
        "server": {
            "websocket_port": 8765,
            "frontend_port": 8080,
            "host": "localhost",
        },
        
        # LLM
        "llm": {
            "use_ollama": True,
            "ollama_url": "http://localhost:11434",
            "model": "smollm2:135m",
            "timeout": 5,
        },
        
        # UI
        "ui": {
            "auto_open_browser": True,
            "theme": "dark",
        },
        
        # Logging
        "logging": {
            "level": "INFO",
            "log_to_file": True,
            "log_file": "zentrax.log",
        },
    }
    
    _instance = None
    _config: Dict[str, Any] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from file or use defaults."""
        config_file = CONFIG_DIR / "settings.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self._config = {**self.DEFAULTS, **json.load(f)}
            except Exception:
                self._config = self.DEFAULTS.copy()
        else:
            self._config = self.DEFAULTS.copy()
    
    def save(self):
        """Save configuration to file."""
        CONFIG_DIR.mkdir(exist_ok=True)
        config_file = CONFIG_DIR / "settings.json"
        
        with open(config_file, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'voice.wake_phrase')."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set a configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def voice(self) -> Dict:
        return self._config.get('voice', {})
    
    @property
    def tts(self) -> Dict:
        return self._config.get('tts', {})
    
    @property
    def gesture(self) -> Dict:
        return self._config.get('gesture', {})
    
    @property
    def server(self) -> Dict:
        return self._config.get('server', {})
    
    @property
    def llm(self) -> Dict:
        return self._config.get('llm', {})


# Global config instance
def get_config() -> ZentraxConfig:
    """Get the global configuration."""
    return ZentraxConfig()
