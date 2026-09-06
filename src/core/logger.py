"""
Zentrax Logging Utility
Provides consistent, colored logging across all modules.
"""

import logging
import sys
from datetime import datetime
from typing import Optional

# Try to use colorama for Windows terminal color support
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class ZentraxFormatter(logging.Formatter):
    """Custom formatter with colors and icons."""
    
    if COLORAMA_AVAILABLE:
        COLORS = {
            'DEBUG': Fore.CYAN,
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.RED + Style.BRIGHT,
        }
        RESET = Style.RESET_ALL
    else:
        COLORS = {}
        RESET = ''
    
    ICONS = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️ ',
        'ERROR': '❌',
        'CRITICAL': '💀',
    }
    
    def format(self, record):
        # Add color and icon
        color = self.COLORS.get(record.levelname, '')
        icon = self.ICONS.get(record.levelname, '')
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Build message
        message = f"{color}[{timestamp}] {icon} {record.getMessage()}{self.RESET}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


class ZentraxLogger:
    """Central logger for the Zentrax application."""
    
    _instance: Optional['ZentraxLogger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """Configure the logger."""
        self._logger = logging.getLogger('zentrax')
        self._logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self._logger.handlers:
            return
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ZentraxFormatter())
        self._logger.addHandler(console_handler)
        
        # File handler (plain text)
        try:
            file_handler = logging.FileHandler('zentrax.log', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
            ))
            self._logger.addHandler(file_handler)
        except Exception:
            pass  # File logging optional
    
    @property
    def logger(self) -> logging.Logger:
        return self._logger
    
    def debug(self, msg: str):
        self._logger.debug(msg)
    
    def info(self, msg: str):
        self._logger.info(msg)
    
    def warning(self, msg: str):
        self._logger.warning(msg)
    
    def error(self, msg: str, exc_info: bool = False):
        self._logger.error(msg, exc_info=exc_info)
    
    def critical(self, msg: str, exc_info: bool = True):
        self._logger.critical(msg, exc_info=exc_info)
    
    def command(self, cmd: str, result: str = None):
        """Log a command execution."""
        msg = f"Command: {cmd}"
        if result:
            msg += f" → {result}"
        self._logger.info(msg)
    
    def voice(self, text: str, is_input: bool = True):
        """Log voice input/output."""
        direction = "🎤 Heard" if is_input else "🔊 Said"
        self._logger.info(f"{direction}: {text}")
    
    def gesture(self, gesture: str, action: str = None):
        """Log gesture detection."""
        msg = f"👋 Gesture: {gesture}"
        if action:
            msg += f" → {action}"
        self._logger.info(msg)


# Global logger instance
def get_logger() -> ZentraxLogger:
    """Get the global Zentrax logger."""
    return ZentraxLogger()


# Convenience functions
def log_info(msg: str):
    get_logger().info(msg)

def log_error(msg: str, exc_info: bool = False):
    get_logger().error(msg, exc_info=exc_info)

def log_warning(msg: str):
    get_logger().warning(msg)

def log_debug(msg: str):
    get_logger().debug(msg)

def log_command(cmd: str, result: str = None):
    get_logger().command(cmd, result)

def log_voice(text: str, is_input: bool = True):
    get_logger().voice(text, is_input)

def log_gesture(gesture: str, action: str = None):
    get_logger().gesture(gesture, action)
