"""
Windows Command Generator using SmolLM2 via Ollama
This module converts natural language to executable Windows commands.
Includes a fallback pattern-matching mode when Ollama is unavailable.
"""

import json
import os
import re
import subprocess
import requests
import glob
from typing import Optional, Dict, Any, List


class PatternMatcher:
    """
    Fallback pattern-based command generator when Ollama is unavailable.
    Uses regex patterns and fuzzy matching to handle natural language.
    """
    
    def __init__(self):
        self.username = os.environ.get("USERNAME", "User")
        self.user_home = os.path.expanduser("~")
        
        # App name mappings (with common misspellings/variations)
        self.app_mappings = {
            "chrome": "chrome.exe", "google": "chrome.exe", "browser": "chrome.exe",
            "firefox": "firefox.exe", "edge": "msedge.exe",
            "notepad": "notepad.exe", "note pad": "notepad.exe", "nodepad": "notepad.exe",
            "calculator": "calc.exe", "calc": "calc.exe",
            "explorer": "explorer.exe", "file explorer": "explorer.exe", "files": "explorer.exe",
            "cmd": "cmd.exe", "command prompt": "cmd.exe", "terminal": "cmd.exe",
            "powershell": "powershell.exe",
            "task manager": "taskmgr.exe", "taskmgr": "taskmgr.exe",
            "control panel": "control.exe", "settings": "ms-settings:",
            "paint": "mspaint.exe", "word": "winword.exe", "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "vscode": "code.exe", "vs code": "code.exe", "visual studio code": "code.exe", "code": "code.exe",
            "spotify": "spotify.exe", "discord": "discord.exe", "slack": "slack.exe",
            "teams": "teams.exe", "zoom": "zoom.exe", "vlc": "vlc.exe",
            "camera": "microsoft.windows.camera:", "photos": "ms-photos:",
            "snipping tool": "snippingtool.exe", "snip": "snippingtool.exe",
        }
        
        # Folder mappings
        self.folder_mappings = {
            "downloads": os.path.join(self.user_home, "Downloads"),
            "download": os.path.join(self.user_home, "Downloads"),
            "documents": os.path.join(self.user_home, "Documents"),
            "document": os.path.join(self.user_home, "Documents"),
            "desktop": os.path.join(self.user_home, "Desktop"),
            "pictures": os.path.join(self.user_home, "Pictures"),
            "videos": os.path.join(self.user_home, "Videos"),
            "music": os.path.join(self.user_home, "Music"),
            "home": self.user_home,
            "zentrax": r"C:\Users\LENOVO\Desktop\programing_Files\git_Files\Zentrax",
        }
        
        # File extensions
        self.file_extensions = {
            "pdf": ".pdf", "word": ".docx", "doc": ".docx", "docx": ".docx",
            "excel": ".xlsx", "xlsx": ".xlsx", "xls": ".xls",
            "text": ".txt", "txt": ".txt", "tx": ".txt",
            "python": ".py", "py": ".py",
            "image": ".jpg", "photo": ".jpg", "picture": ".jpg",
            "video": ".mp4", "mp4": ".mp4",
            "music": ".mp3", "audio": ".mp3", "mp3": ".mp3",
        }
    
    def _normalize_text(self, text: str) -> str:
        """Clean and normalize input text."""
        text = text.lower().strip()
        text = re.sub(r'[.,!?:;]+$', '', text)  # Remove trailing punctuation
        text = re.sub(r'^(okay|ok|hey|please|can you|could you|i want to|i need to|so|um|uh)\s+', '', text)
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text
    
    def _find_file(self, name: str, extension: str = None) -> Optional[str]:
        """Find a file by name, with fuzzy matching."""
        search_locations = [
            self.folder_mappings["desktop"],
            self.folder_mappings["documents"],
            self.folder_mappings["downloads"],
            self.user_home,
        ]
        
        # Build search pattern
        name_clean = re.sub(r'[^\w]', '', name)  # Remove special chars
        patterns = [
            f"*{name_clean}*{extension}" if extension else f"*{name_clean}*",
            f"*{name}*{extension}" if extension else f"*{name}*",
        ]
        
        for location in search_locations:
            for pattern in patterns:
                matches = glob.glob(os.path.join(location, pattern))
                if matches:
                    return matches[0]
        
        # Recursive search if not found
        for pattern in patterns:
            matches = glob.glob(os.path.join(self.user_home, "**", pattern), recursive=True)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_file_info(self, text: str) -> tuple:
        """Extract filename and extension from text."""
        # Look for explicit file extensions
        ext_match = re.search(r'(\w+)\.(txt|pdf|docx?|xlsx?|py|jpg|png|mp[34]|exe)', text)
        if ext_match:
            return ext_match.group(1), "." + ext_match.group(2)
        
        # Look for file type keywords
        for keyword, ext in self.file_extensions.items():
            if keyword in text:
                # Extract the name before the keyword
                name_match = re.search(rf'(\w+)\s+{keyword}', text)
                if name_match:
                    return name_match.group(1), ext
                # Or after "open/find"
                name_match = re.search(rf'(?:open|find|search)\s+(\w+)\s+{keyword}', text)
                if name_match:
                    return name_match.group(1), ext
                return None, ext
        
        return None, None
    
    def match(self, text: str) -> Optional[Dict[str, Any]]:
        """Match natural language to a command using patterns."""
        original_text = text
        text = self._normalize_text(text)
        
        if not text or len(text) < 2:
            return None
        
        # ============ SYSTEM INFO COMMANDS ============
        # Battery percentage
        if re.search(r'battery|power|charge', text):
            return {"action": "system_info", "target": "battery"}
        
        # Time/Date
        if re.search(r'what.*(time|date)|current (time|date)', text):
            return {"action": "system_info", "target": "datetime"}
        
        # ============ WEB SEARCH (in browser) ============
        # "search for X in chrome/browser" or "google X"
        web_search = re.search(r'(?:search|google|look up|find)\s+(?:for\s+)?(.+?)\s+(?:in|on|using)\s+(?:chrome|browser|google|internet|web)', text)
        if web_search:
            query = web_search.group(1).strip()
            return {"action": "web_search", "target": query}
        
        # "google something" pattern
        if text.startswith("google "):
            query = text[7:].strip()
            return {"action": "web_search", "target": query}
        
        # ============ SCREENSHOT ============
        if re.search(r'(take|capture|grab).*(screenshot|screen|snap)', text) or text == "screenshot":
            return {"action": "screenshot"}
        
        # ============ VOLUME CONTROL ============
        if re.search(r'(volume|sound).*(up|increase|raise|higher|louder)', text) or re.search(r'(turn|crank|raise).*(up)', text):
            return {"action": "volume_up", "extra": {"amount": 10}}
        if re.search(r'(volume|sound).*(down|decrease|lower|reduce|quieter)', text) or re.search(r'(turn|lower).*(down)', text):
            return {"action": "volume_down", "extra": {"amount": 10}}
        if re.search(r'(mute|unmute|silence)', text):
            return {"action": "mute"}
        
        # ============ WINDOW CONTROL ============
        if re.search(r'(close).*(window|this|current|app)', text) or text == "close":
            return {"action": "close_window", "target": "current"}
        if re.search(r'minimize', text):
            return {"action": "minimize_window", "target": "current"}
        if re.search(r'maximize|full\s*screen', text):
            return {"action": "maximize_window", "target": "current"}
        if re.search(r'(switch|next|alt.?tab|over next)', text):
            return {"action": "switch_window", "target": "next"}
        
        # ============ SYSTEM ACTIONS ============
        if re.search(r'lock.*(screen|computer|pc)', text):
            return {"action": "lock_screen"}
        if re.search(r'shutdown|shut\s*down|power\s*off', text):
            return {"action": "shutdown", "extra": {"delay": 0}}
        if re.search(r'restart|reboot', text):
            return {"action": "restart", "extra": {"delay": 0}}
        if re.search(r'sleep|hibernate', text):
            return {"action": "sleep"}
        
        # ============ OPEN FILE BY NAME (with fuzzy matching) ============
        # "open linux pdf" / "open harish.txt" / "open the document"
        open_file_match = re.search(r'open\s+(?:the\s+)?(?:file\s+)?(\w+)[\s.]*(pdf|txt|tx|docx?|xlsx?|py|jpg|png)?', text)
        if open_file_match and open_file_match.group(1) not in self.app_mappings:
            name = open_file_match.group(1)
            ext = open_file_match.group(2)
            
            # Map common transcription errors
            ext_map = {"tx": ".txt", "txt": ".txt", "pdf": ".pdf", "doc": ".docx", "docx": ".docx"}
            extension = ext_map.get(ext) if ext else None
            
            # Try to find the file
            file_path = self._find_file(name, extension)
            if file_path:
                return {"action": "open_file", "path": file_path}
            
            # If extension specified, create the file
            if extension:
                file_path = os.path.join(self.folder_mappings["desktop"], f"{name}{extension}")
                return {"action": "create_and_open_file", "path": file_path, "extra": {"app": "notepad.exe"}}
        
        # ============ OPEN FILE IN APP ============
        # "open harish.txt in notepad" / "open file X with notepad"
        open_in_app = re.search(r'open\s+(?:the\s+)?(?:file\s+)?(\S+)\s+(?:in|with|using)\s+(\w+)', text)
        if open_in_app:
            filename = open_in_app.group(1)
            app_name = open_in_app.group(2).lower()
            
            # Fix common transcription errors
            app_name = {"nodepad": "notepad", "hordepad": "notepad", "notpad": "notepad"}.get(app_name, app_name)
            
            # Find the file
            file_path = self._find_file(filename)
            if file_path:
                return {"action": "open_file", "path": file_path}
            
            # Create new file
            if "." not in filename:
                filename += ".txt"
            file_path = os.path.join(self.folder_mappings["desktop"], filename)
            return {"action": "create_and_open_file", "path": file_path, "extra": {"app": self.app_mappings.get(app_name, "notepad.exe")}}
        
        # ============ CREATE FILE ============
        # "create a file" / "create file harish.txt" / "new file"
        create_file = re.search(r'(create|make|new)\s+(?:a\s+)?file\s*(?:called\s+|named\s+)?(\S+)?', text)
        if create_file:
            filename = create_file.group(2) if create_file.group(2) else "new_file"
            if "." not in filename:
                filename += ".txt"
            # Fix .tx -> .txt
            filename = re.sub(r'\.tx$', '.txt', filename)
            file_path = os.path.join(self.folder_mappings["desktop"], filename)
            return {"action": "create_and_open_file", "path": file_path, "extra": {"app": "notepad.exe"}}
        
        # ============ SEARCH FILES ============
        search_match = re.search(r'(search|find|look\s*for|locate)\s+(?:for\s+)?(?:my\s+)?(?:all\s+)?(.+?)(?:\s+files?)?$', text)
        if search_match:
            query = search_match.group(2).strip()
            query = re.sub(r'\s+files?$', '', query)
            query = re.sub(r'^(all|my|the)\s+', '', query)
            
            # Check if it's a file type
            if query in ["pdf", "pdfs"]:
                return {"action": "search_and_open", "target": "*.pdf", "path": self.user_home}
            elif query in ["doc", "docs", "word", "documents"]:
                return {"action": "search_and_open", "target": "*.docx", "path": self.user_home}
            elif query in ["text", "txt"]:
                return {"action": "search_and_open", "target": "*.txt", "path": self.user_home}
            elif query in ["python", "py"]:
                return {"action": "search_and_open", "target": "*.py", "path": self.user_home}
            else:
                return {"action": "search", "target": f"*{query}*", "path": self.user_home}
        
        # ============ OPEN FOLDER ============
        for folder_name, folder_path in self.folder_mappings.items():
            if re.search(rf'open\s+(?:the\s+)?(?:my\s+)?{folder_name}', text):
                return {"action": "open_folder", "path": folder_path}
        
        # ============ OPEN FOLDER IN VS CODE ============
        vscode_folder = re.search(r'open\s+(\w+)\s+(?:folder\s+)?(?:in|with)\s+(?:vs\s*code|vscode|code)', text)
        if vscode_folder:
            folder_name = vscode_folder.group(1).lower()
            folder_path = self.folder_mappings.get(folder_name)
            if folder_path and os.path.exists(folder_path):
                return {"action": "run_command", "extra": {"command": f'code "{folder_path}"'}}
        
        # ============ OPEN APP ============
        for app_name, exe_name in self.app_mappings.items():
            if re.search(rf'open\s+(?:the\s+)?{re.escape(app_name)}(?:\s|$)', text):
                if exe_name.endswith(":"):
                    return {"action": "run_command", "extra": {"command": f"start {exe_name}"}}
                return {"action": "open_app", "target": exe_name}
        
        # Generic app open
        open_app = re.search(r'open\s+(?:the\s+)?(\w+)$', text)
        if open_app:
            app_name = open_app.group(1).lower()
            if app_name in self.app_mappings:
                return {"action": "open_app", "target": self.app_mappings[app_name]}
            # Don't try to open as .exe if it looks like a file
            if not any(ext in app_name for ext in ['txt', 'pdf', 'doc', 'py']):
                return {"action": "open_app", "target": f"{app_name}.exe"}
        
        # ============ TASK MANAGER ============
        if "task manager" in text or "taskmgr" in text:
            return {"action": "open_app", "target": "taskmgr.exe"}
        
        # ============ ADVANCED FRIDAY COMMANDS ============
        
        # Brightness control
        if re.search(r'(increase|raise|turn up|brighter).*(brightness|screen)', text) or re.search(r'brightness.*(up|increase)', text):
            return {"action": "brightness_up", "extra": {"amount": 15}}
        if re.search(r'(decrease|lower|turn down|dimmer).*(brightness|screen)', text) or re.search(r'brightness.*(down|decrease)', text):
            return {"action": "brightness_down", "extra": {"amount": 15}}
        if re.search(r'(set|make).*(brightness|screen).*(\d+)', text):
            match = re.search(r'(\d+)', text)
            level = int(match.group(1)) if match else 50
            return {"action": "set_brightness", "extra": {"level": level}}
        
        # WiFi control
        if re.search(r'(turn|switch).*(on|enable).*(wifi|wi-fi|wireless|internet)', text) or re.search(r'(enable|connect).*(wifi|wi-fi|wireless)', text):
            return {"action": "wifi_toggle", "extra": {"state": "on"}}
        if re.search(r'(turn|switch).*(off|disable).*(wifi|wi-fi|wireless|internet)', text) or re.search(r'(disable|disconnect).*(wifi|wi-fi|wireless)', text):
            return {"action": "wifi_toggle", "extra": {"state": "off"}}
        if re.search(r'toggle.*(wifi|wi-fi|wireless)', text):
            return {"action": "wifi_toggle", "extra": {"state": "toggle"}}
        
        # Bluetooth control
        if re.search(r'(open|turn|toggle|enable|disable).*(bluetooth)', text):
            return {"action": "bluetooth_toggle"}
        
        # Kill/close process
        kill_match = re.search(r'(kill|terminate|end|stop|force\s*close)\s+(?:the\s+)?(?:process\s+)?(\w+)', text)
        if kill_match:
            process = kill_match.group(2)
            return {"action": "kill_process", "target": process}
        
        # List processes
        if re.search(r'(list|show|what).*(running|process|apps|programs)', text) or re.search(r'running\s+(apps|process)', text):
            return {"action": "list_processes", "extra": {"count": 10}}
        
        # Media controls
        if re.search(r'(play|pause|resume|toggle).*(music|media|song|track|video)?', text) and not re.search(r'play\s+\w+', text):
            return {"action": "media_play_pause"}
        if re.search(r'(next|skip).*(song|track|music)?', text):
            return {"action": "media_next"}
        if re.search(r'(previous|prev|back|last).*(song|track|music)?', text):
            return {"action": "media_previous"}
        if re.search(r'stop.*(music|media|playing)', text):
            return {"action": "media_stop"}
        
        # Open URL
        url_match = re.search(r'(open|go to|visit|navigate to)\s+((?:https?://)?(?:www\.)?[\w.-]+\.[a-z]{2,}(?:/\S*)?)', text)
        if url_match:
            url = url_match.group(2)
            return {"action": "open_url", "target": url}
        
        # Common websites
        if re.search(r'(open|go to)\s+(youtube|github|gmail|google|facebook|twitter|instagram|linkedin|reddit)', text):
            site = re.search(r'(youtube|github|gmail|google|facebook|twitter|instagram|linkedin|reddit)', text).group(1)
            urls = {
                "youtube": "youtube.com", "github": "github.com", "gmail": "gmail.com",
                "google": "google.com", "facebook": "facebook.com", "twitter": "twitter.com",
                "instagram": "instagram.com", "linkedin": "linkedin.com", "reddit": "reddit.com"
            }
            return {"action": "open_url", "target": urls.get(site, f"{site}.com")}
        
        # Tab controls
        if re.search(r'(new|open)\s*tab', text):
            return {"action": "new_tab"}
        if re.search(r'close\s*tab', text):
            return {"action": "close_tab"}
        if re.search(r'(refresh|reload)\s*(?:page|tab)?', text):
            return {"action": "refresh_page"}
        
        # Show desktop
        if re.search(r'show\s*desktop|minimize\s*all|go to desktop', text):
            return {"action": "show_desktop"}
        
        # Empty recycle bin
        if re.search(r'empty.*(recycle|trash|bin)', text) or re.search(r'(clear|clean).*(recycle|trash)', text):
            return {"action": "empty_recycle_bin"}
        
        # Emoji picker
        if re.search(r'(open|show).*(emoji|emoticon)', text):
            return {"action": "open_emoji_picker"}
        
        # Clipboard history
        if re.search(r'(open|show).*(clipboard|paste\s*history)', text):
            return {"action": "open_clipboard_history"}
        
        # Night light / blue light filter
        if re.search(r'(night\s*light|blue\s*light|night\s*mode|eye\s*comfort)', text):
            return {"action": "night_light_toggle"}
        
        # Airplane mode
        if re.search(r'airplane\s*mode|flight\s*mode', text):
            return {"action": "airplane_mode_toggle"}
        
        # Scroll commands
        if re.search(r'scroll\s*(up|down)', text):
            direction = "up" if "up" in text else "down"
            return {"action": "scroll", "extra": {"direction": direction, "amount": 5}}
        
        # CPU/Memory/Disk info
        if re.search(r'(cpu|processor).*(usage|info|status)', text):
            return {"action": "system_info", "extra": {"type": "cpu"}}
        if re.search(r'(ram|memory).*(usage|info|status)', text):
            return {"action": "system_info", "extra": {"type": "memory"}}
        if re.search(r'(disk|storage|space).*(usage|info|status|left|available)', text):
            return {"action": "system_info", "extra": {"type": "disk"}}
        if re.search(r'(wifi|network|internet).*(status|info|connected)', text):
            return {"action": "system_info", "extra": {"type": "network"}}
        
        # General status check
        if re.search(r'(system|computer|pc).*(status|info|health)', text) or text in ["status", "system info", "how am i doing"]:
            return {"action": "system_info", "extra": {"type": "all"}}
        
        # Help command
        if text in ["help", "what can you do", "commands", "help me"]:
            return {"action": "help"}
        
        # Thank you response (for FRIDAY personality)
        if re.search(r'(thank|thanks|thank you)', text):
            return {"action": "thanks"}
        
        # Who are you?
        if re.search(r'(who are you|what is your name|introduce yourself)', text):
            return {"action": "introduce"}
        
        # ============ TYPE TEXT / VOICE TYPING ============
        # "type hello world" / "write hello world" / "type in notepad: hello"
        type_match = re.search(r'(?:type|write|input|enter)\s+(?:in\s+(?:notepad|file)\s*[:\.\-]?\s*)?["\']?(.+?)["\']?$', text)
        if type_match:
            text_to_type = type_match.group(1).strip()
            if text_to_type and len(text_to_type) > 1:
                return {"action": "type_text", "extra": {"text": text_to_type}}
        
        # "voice typing" / "activate voice typing" / "start dictation"
        if re.search(r'(voice\s*typing|dictation|dictate|start\s*typing|voice\s*input)', text):
            return {"action": "voice_typing"}
        
        # ============ WEB RESEARCH ============
        # "research about python" / "search the web for AI" / "look up machine learning"
        research_match = re.search(r'(?:research|search\s+(?:the\s+)?(?:web|internet)\s+(?:for|about)?|look\s+up|find\s+(?:info|information)\s+(?:about|on))\s+(.+)', text)
        if research_match:
            query = research_match.group(1).strip()
            return {"action": "web_search", "target": query}
        
        # "what is X" / "tell me about X" - treat as web search
        what_is_match = re.search(r'(?:what\s+is|tell\s+me\s+about|explain|define)\s+(.+)', text)
        if what_is_match:
            query = what_is_match.group(1).strip()
            if len(query) > 2 and query not in ["the time", "time", "date", "battery"]:
                return {"action": "web_search", "target": query}
        
        return None


class WindowsCommandGenerator:
    """
    Uses SmolLM2 (via Ollama) to interpret natural language commands
    and generate structured JSON commands for Windows automation.
    """
    
    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL_NAME = "smollm2:135m"  # SmolLM2 model in Ollama
    
    # System prompt for the LLM
    SYSTEM_PROMPT = """You are the command-generation brain for a Windows-automation system.
Your role is to read the user's natural-language instructions and output a precise, executable command that controls the Windows operating system.

You must be able to:
1. Search for files and folders on the system
2. Open any file or application by generating the correct command
3. Perform general OS actions (window control, system settings, process control, etc.)

Your output must ALWAYS be a valid JSON object with this structure:
{
  "action": "<action_name>",
  "target": "<file_or_app_or_window>",
  "path": "<absolute_or_relative_path_if_needed>",
  "extra": {...}
}

Available actions:
- "open_app": Open an application (target = exe name like "chrome.exe", "notepad.exe", "explorer.exe")
- "open_file": Open a specific file (path = full path to file)
- "open_folder": Open a folder in explorer (path = folder path)
- "search": Search for files (target = search pattern like "*.pdf", "*.docx")
- "create_file": Create a new file (path = full path, extra.content = optional content)
- "create_folder": Create a new folder (path = folder path)
- "delete": Delete file or folder (path = full path)
- "move": Move file/folder (path = source, extra.destination = target)
- "rename": Rename file/folder (path = full path, extra.new_name = new name)
- "copy": Copy file/folder (path = source, extra.destination = target)
- "maximize_window": Maximize current/specified window (target = window title or "current")
- "minimize_window": Minimize current/specified window (target = window title or "current")
- "close_window": Close current/specified window (target = window title or "current")
- "switch_window": Switch to a window (target = window title or app name)
- "run_command": Run a shell command (extra.command = the command string)
- "open_control_panel": Open control panel (target = specific panel or "main")
- "open_settings": Open Windows settings (target = specific setting or "main")
- "task_manager": Open task manager
- "keyboard_action": Perform keyboard shortcut (extra.keys = list of keys like ["ctrl", "c"])
- "mouse_action": Perform mouse action (extra.action = "click"/"double_click"/"right_click", extra.x, extra.y)
- "volume_up": Increase volume (extra.amount = optional percentage)
- "volume_down": Decrease volume (extra.amount = optional percentage)
- "mute": Mute/unmute audio
- "screenshot": Take a screenshot (extra.save_path = optional path)
- "lock_screen": Lock the computer
- "shutdown": Shutdown computer (extra.delay = optional seconds)
- "restart": Restart computer (extra.delay = optional seconds)
- "sleep": Put computer to sleep

Common application shortcuts:
- Chrome/Google: chrome.exe
- Firefox: firefox.exe
- Edge: msedge.exe
- Notepad: notepad.exe
- Calculator: calc.exe
- File Explorer: explorer.exe
- Command Prompt: cmd.exe
- PowerShell: powershell.exe
- Task Manager: taskmgr.exe
- Control Panel: control.exe
- Settings: ms-settings:
- VS Code: code.exe
- Word: winword.exe
- Excel: excel.exe
- PowerPoint: powerpnt.exe

Default paths:
- User Documents: C:/Users/{username}/Documents
- User Desktop: C:/Users/{username}/Desktop
- User Downloads: C:/Users/{username}/Downloads

IMPORTANT: 
- Output ONLY the JSON object, no explanations or markdown
- Use forward slashes in paths
- For the current user, use the placeholder {username} which will be replaced
- If information is missing but can be reasonably inferred, make the inference
- If the request is unclear, still provide the best possible command

Examples:

User: "open chrome"
Output: {"action": "open_app", "target": "chrome.exe"}

User: "search for my pdf files"
Output: {"action": "search", "target": "*.pdf", "path": "C:/Users/{username}"}

User: "open the file called report.docx"
Output: {"action": "open_file", "path": "C:/Users/{username}/Documents/report.docx"}

User: "close this window"
Output: {"action": "close_window", "target": "current"}

User: "create a folder called Projects on desktop"
Output: {"action": "create_folder", "path": "C:/Users/{username}/Desktop/Projects"}

User: "take a screenshot"
Output: {"action": "screenshot"}

User: "open task manager"
Output: {"action": "open_app", "target": "taskmgr.exe"}

User: "turn up the volume"
Output: {"action": "volume_up", "extra": {"amount": 10}}
"""

    def __init__(self, model_name: str = None, ollama_url: str = None, use_fallback: bool = True):
        """
        Initialize the Windows Command Generator.
        
        Args:
            model_name: Ollama model name (default: smollm2)
            ollama_url: Ollama API URL (default: http://localhost:11434/api/generate)
            use_fallback: Use pattern matching when Ollama is unavailable (default: True)
        """
        self.model_name = model_name or self.MODEL_NAME
        self.ollama_url = ollama_url or self.OLLAMA_URL
        self.username = os.environ.get("USERNAME", "User")
        self.use_fallback = use_fallback
        self.pattern_matcher = PatternMatcher() if use_fallback else None
        self.ollama_available = None  # Will be checked on first use
        
    def _replace_placeholders(self, text: str) -> str:
        """Replace placeholders like {username} with actual values."""
        return text.replace("{username}", self.username)
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Call the Ollama API with the given prompt.
        
        Args:
            prompt: The user's natural language command
            
        Returns:
            The LLM's response text or None if failed
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": f"{self.SYSTEM_PROMPT}\n\nUser: {prompt}\nOutput:",
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent outputs
                    "num_predict": 500,  # Limit response length
                }
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.ConnectionError:
            self.ollama_available = False
            return None
        except requests.exceptions.Timeout:
            return None
        except Exception as e:
            self.ollama_available = False
            return None
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse the LLM response as JSON.
        
        Args:
            response: The raw LLM response
            
        Returns:
            Parsed JSON dict or None if parsing failed
        """
        if not response:
            return None
            
        # Try to extract JSON from the response
        try:
            # First, try direct parsing
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON within the response
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        print(f"❌ Failed to parse LLM response as JSON: {response[:200]}")
        return None
    
    def generate_command(self, natural_language: str) -> Optional[Dict[str, Any]]:
        """
        Convert natural language to a structured command.
        
        Args:
            natural_language: The user's command in plain English
            
        Returns:
            A structured command dict or None if generation failed
        """
        print(f"🧠 Processing: \"{natural_language}\"")
        
        # Check if Ollama is available (cache the result)
        if self.ollama_available is None:
            self.ollama_available = self._check_ollama_connection()
        
        command = None
        
        # Try Ollama first if available
        if self.ollama_available:
            response = self._call_ollama(natural_language)
            if response:
                command = self._parse_json_response(response)
        
        # Fallback to pattern matching if Ollama failed or unavailable
        if command is None and self.use_fallback and self.pattern_matcher:
            print("📋 Using pattern matching (Ollama unavailable)")
            command = self.pattern_matcher.match(natural_language)
        
        if not command:
            print("❌ Could not understand command")
            return None
        
        # Replace placeholders with actual values
        if "path" in command and command["path"]:
            command["path"] = self._replace_placeholders(command["path"])
        if "target" in command and command["target"]:
            command["target"] = self._replace_placeholders(str(command["target"]))
        if "extra" in command and isinstance(command["extra"], dict):
            for key, value in command["extra"].items():
                if isinstance(value, str):
                    command["extra"][key] = self._replace_placeholders(value)
        
        print(f"✅ Generated command: {json.dumps(command, indent=2)}")
        return command
    
    def check_ollama_status(self) -> bool:
        """
        Check if Ollama is running and the model is available.
        
        Returns:
            True if Ollama is ready, False otherwise
        """
        try:
            # Check if Ollama is running
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=5
            )
            response.raise_for_status()
            
            # Check if model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            
            if self.model_name not in model_names and f"{self.model_name}:latest" not in [m.get("name", "") for m in models]:
                print(f"⚠️  Model '{self.model_name}' not found. Available models: {model_names}")
                print(f"   Pull it with: ollama pull {self.model_name}")
                return False
            
            print(f"✅ Ollama is ready with model '{self.model_name}'")
            return True
            
        except requests.exceptions.ConnectionError:
            print("❌ Ollama is not running. Start it with: ollama serve")
            return False
        except Exception as e:
            print(f"❌ Error checking Ollama status: {e}")
            return False


# Convenience function for quick command generation
def generate_windows_command(natural_language: str) -> Optional[Dict[str, Any]]:
    """
    Quick helper to generate a Windows command from natural language.
    
    Args:
        natural_language: The user's command in plain English
        
    Returns:
        A structured command dict or None if generation failed
    """
    generator = WindowsCommandGenerator()
    return generator.generate_command(natural_language)


if __name__ == "__main__":
    # Test the command generator
    generator = WindowsCommandGenerator()
    
    # Check Ollama status
    if not generator.check_ollama_status():
        print("\n💡 To set up Ollama with SmolLM2:")
        print("   1. Install Ollama from https://ollama.ai")
        print("   2. Run: ollama serve")
        print("   3. Run: ollama pull smollm2")
        exit(1)
    
    # Test commands
    test_commands = [
        "open chrome",
        "search for my pdf files",
        "open notepad",
        "take a screenshot",
        "close this window",
        "open the downloads folder",
        "create a folder called TestProject on desktop",
        "open task manager",
        "turn up the volume",
    ]
    
    print("\n" + "="*60)
    print("Testing Windows Command Generator with SmolLM2")
    print("="*60 + "\n")
    
    for cmd in test_commands:
        result = generator.generate_command(cmd)
        print("-" * 40 + "\n")
