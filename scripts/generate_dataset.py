"""
Zentrax Dataset Generator
Generates high-quality instruction → reasoning → action training data.

Usage:
    python scripts/generate_dataset.py --output data/zentrax_train.jsonl --size 100
    python scripts/generate_dataset.py --output data/zentrax_train.jsonl --size 100 --include-safety

Output:
    JSONL file with samples in the format:
    {
        "id": "zentrax_000001",
        "instruction": "open chrome",
        "context": null,
        "reasoning": "...",
        "action": {"action": "open_app", "target": "chrome.exe", ...},
        "category": "app",
        "difficulty": "simple",
        "tags": ["browser", "launch"]
    }
"""

import json
import random
import hashlib
import argparse
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
import sys

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Action:
    """Structured action output."""
    action: str
    target: Optional[str] = None
    path: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Sample:
    """Training sample."""
    id: str
    instruction: str
    context: Optional[Dict[str, Any]]
    reasoning: str
    action: Dict[str, Any]
    category: str
    difficulty: str
    tags: List[str]


# ============================================================================
# ACTION TAXONOMY
# ============================================================================

ACTION_TAXONOMY = {
    "app": {
        "description": "Application lifecycle management",
        "actions": ["open_app", "kill_process", "list_processes", "task_manager"]
    },
    "file": {
        "description": "File system operations",
        "actions": ["open_file", "create_file", "create_and_open_file", "delete", "move", "rename", "copy", "search", "search_and_open"]
    },
    "folder": {
        "description": "Directory operations",
        "actions": ["open_folder", "create_folder"]
    },
    "window": {
        "description": "Window management",
        "actions": ["maximize_window", "minimize_window", "close_window", "switch_window", "show_desktop"]
    },
    "browser": {
        "description": "Web browser control",
        "actions": ["open_url", "web_search", "new_tab", "close_tab", "refresh_page"]
    },
    "input": {
        "description": "Keyboard, mouse, and text input",
        "actions": ["keyboard_action", "mouse_action", "type_text", "click", "scroll", "voice_typing"]
    },
    "media": {
        "description": "Media playback control",
        "actions": ["media_play_pause", "media_next", "media_previous", "media_stop", "volume_up", "volume_down", "mute"]
    },
    "system": {
        "description": "OS-level controls",
        "actions": ["screenshot", "lock_screen", "shutdown", "restart", "sleep", "system_info", "run_command", "open_settings", "open_control_panel", "empty_recycle_bin"]
    },
    "hardware": {
        "description": "Hardware toggles",
        "actions": ["brightness_up", "brightness_down", "set_brightness", "wifi_toggle", "bluetooth_toggle", "night_light_toggle", "airplane_mode_toggle"]
    },
    "ui": {
        "description": "UI utilities",
        "actions": ["open_emoji_picker", "open_clipboard_history"]
    }
}


# ============================================================================
# PHRASE VARIANTS - Natural language variations for each action
# ============================================================================

PHRASE_VARIANTS = {
    # === APP ACTIONS ===
    "open_app": [
        "open {app}",
        "launch {app}",
        "start {app}",
        "run {app}",
        "fire up {app}",
        "can you open {app}",
        "please start {app}",
        "I need {app}",
        "get {app} running",
        "bring up {app}",
        "open up {app}",
        "start up {app}",
        "could you launch {app}",
        "load {app}",
        "execute {app}",
        "i want to use {app}",
        "open {app} for me",
        "please open {app}",
        "launch {app} please",
        "can you start {app} for me",
    ],
    "kill_process": [
        "kill {app}",
        "close {app}",
        "stop {app}",
        "end {app}",
        "terminate {app}",
        "force close {app}",
        "force quit {app}",
        "kill the {app} process",
        "end task {app}",
        "stop {app} from running",
    ],
    "list_processes": [
        "list all processes",
        "show running processes",
        "what's running",
        "show me running apps",
        "list running applications",
        "what processes are running",
        "show active processes",
        "display running tasks",
    ],
    "task_manager": [
        "open task manager",
        "show task manager",
        "launch task manager",
        "bring up task manager",
        "I need task manager",
        "open the task manager",
        "start task manager",
    ],
    
    # === FILE ACTIONS ===
    "open_file": [
        "open {filename}",
        "open the file {filename}",
        "open {filename} file",
        "open file {filename}",
        "show me {filename}",
        "display {filename}",
        "view {filename}",
        "can you open {filename}",
        "please open {filename}",
        "open {filename} for me",
        "i need to see {filename}",
        "load {filename}",
    ],
    "create_file": [
        "create a file called {filename}",
        "create file {filename}",
        "make a new file named {filename}",
        "new file {filename}",
        "create {filename}",
        "make file {filename}",
        "create a new file {filename}",
        "touch {filename}",
        "create {filename} in {location}",
        "make a file called {filename} in {location}",
    ],
    "create_and_open_file": [
        "create and open {filename}",
        "make {filename} and open it",
        "create {filename} then open it",
        "new file {filename} and open",
        "create {filename} and show it",
    ],
    "delete": [
        "delete {filename}",
        "remove {filename}",
        "delete the file {filename}",
        "remove file {filename}",
        "trash {filename}",
        "delete {filename} from {location}",
        "remove {filename} from {location}",
        "get rid of {filename}",
    ],
    "move": [
        "move {filename} to {destination}",
        "move {filename} from {location} to {destination}",
        "transfer {filename} to {destination}",
        "relocate {filename} to {destination}",
        "put {filename} in {destination}",
    ],
    "rename": [
        "rename {filename} to {newname}",
        "change {filename} name to {newname}",
        "rename file {filename} to {newname}",
        "call {filename} as {newname} instead",
    ],
    "copy": [
        "copy {filename} to {destination}",
        "copy {filename}",
        "duplicate {filename}",
        "make a copy of {filename}",
        "copy {filename} to {destination}",
        "duplicate {filename} to {destination}",
    ],
    "search": [
        "search for {query}",
        "find {query}",
        "look for {query}",
        "search {query}",
        "find files named {query}",
        "search for {query} in {location}",
        "find {query} files",
        "locate {query}",
        "where is {query}",
        "find all {query} files",
    ],
    "search_and_open": [
        "find and open {query}",
        "search for {query} and open it",
        "find {query} and open the first one",
        "locate {query} and open it",
        "find {query} and show me",
    ],
    
    # === FOLDER ACTIONS ===
    "open_folder": [
        "open {folder}",
        "open {folder} folder",
        "open the {folder} folder",
        "show me {folder}",
        "go to {folder}",
        "navigate to {folder}",
        "open my {folder}",
        "show {folder} folder",
        "browse {folder}",
        "explore {folder}",
    ],
    "create_folder": [
        "create a folder called {name} in {location}",
        "make a new folder named {name} on {location}",
        "new folder {name} in {location}",
        "add folder {name} to {location}",
        "create directory {name} at {location}",
        "create folder {name}",
        "make folder {name} in {location}",
        "mkdir {name} in {location}",
        "create a new folder {name}",
    ],
    
    # === WINDOW ACTIONS ===
    "maximize_window": [
        "maximize",
        "maximize window",
        "maximize the window",
        "make window fullscreen",
        "fullscreen",
        "maximize this window",
        "make it bigger",
        "expand the window",
        "maximize current window",
    ],
    "minimize_window": [
        "minimize",
        "minimize window",
        "minimize the window",
        "hide window",
        "minimize this window",
        "minimize current window",
        "hide this window",
        "put it in taskbar",
    ],
    "close_window": [
        "close window",
        "close the window",
        "close this window",
        "close current window",
        "close it",
        "exit window",
    ],
    "switch_window": [
        "switch to {app}",
        "switch window to {app}",
        "go to {app} window",
        "focus {app}",
        "bring {app} to front",
        "show {app} window",
        "alt tab to {app}",
    ],
    "show_desktop": [
        "show desktop",
        "go to desktop",
        "minimize all windows",
        "show the desktop",
        "hide all windows",
        "clear desktop",
        "show me the desktop",
    ],
    
    # === BROWSER ACTIONS ===
    "open_url": [
        "open {url}",
        "go to {url}",
        "navigate to {url}",
        "open website {url}",
        "visit {url}",
        "browse to {url}",
        "open {url} in browser",
        "take me to {url}",
    ],
    "web_search": [
        "search for {query}",
        "google {query}",
        "search {query} on google",
        "look up {query}",
        "search the web for {query}",
        "web search {query}",
        "find {query} online",
        "search {query} online",
        "google search {query}",
        "search internet for {query}",
    ],
    "new_tab": [
        "new tab",
        "open new tab",
        "open a new tab",
        "create new tab",
        "add new tab",
        "open tab",
    ],
    "close_tab": [
        "close tab",
        "close this tab",
        "close current tab",
        "close the tab",
        "exit tab",
    ],
    "refresh_page": [
        "refresh",
        "refresh page",
        "reload",
        "reload page",
        "refresh the page",
        "reload this page",
    ],
    
    # === INPUT ACTIONS ===
    "keyboard_action": [
        "press {key}",
        "hit {key}",
        "type {key}",
        "press {key} key",
        "tap {key}",
    ],
    "type_text": [
        "type {text}",
        "write {text}",
        "input {text}",
        "enter {text}",
        "type out {text}",
    ],
    "click": [
        "click",
        "click here",
        "left click",
        "right click",
        "double click",
        "click at {x} {y}",
    ],
    "scroll": [
        "scroll {direction}",
        "scroll {direction} a bit",
        "scroll {direction} more",
        "page {direction}",
    ],
    "mouse_action": [
        "move mouse to {x} {y}",
        "move cursor to {x} {y}",
        "drag to {x} {y}",
    ],
    "voice_typing": [
        "start voice typing",
        "enable voice typing",
        "turn on voice typing",
        "voice input",
        "dictation mode",
    ],
    
    # === MEDIA ACTIONS ===
    "media_play_pause": [
        "play",
        "pause",
        "play pause",
        "toggle play",
        "play or pause",
        "resume",
        "pause music",
        "play music",
        "pause video",
        "play video",
    ],
    "media_next": [
        "next",
        "next track",
        "skip",
        "skip track",
        "next song",
        "play next",
    ],
    "media_previous": [
        "previous",
        "previous track",
        "go back",
        "last song",
        "previous song",
        "play previous",
    ],
    "media_stop": [
        "stop",
        "stop playing",
        "stop music",
        "stop the music",
        "stop media",
    ],
    "volume_up": [
        "volume up",
        "turn up the volume",
        "increase volume",
        "louder",
        "louder please",
        "raise the volume",
        "make it louder",
        "boost the sound",
        "turn it up",
        "crank it up",
    ],
    "volume_down": [
        "volume down",
        "turn down the volume",
        "decrease volume",
        "quieter",
        "lower the volume",
        "make it quieter",
        "reduce volume",
        "turn it down",
    ],
    "mute": [
        "mute",
        "mute volume",
        "silence",
        "mute audio",
        "mute sound",
        "turn off sound",
        "mute everything",
        "unmute",
        "toggle mute",
    ],
    
    # === SYSTEM ACTIONS ===
    "screenshot": [
        "take a screenshot",
        "screenshot",
        "capture screen",
        "take screenshot",
        "screen capture",
        "grab screenshot",
        "capture the screen",
        "take a screen capture",
        "print screen",
        "snip screen",
    ],
    "lock_screen": [
        "lock",
        "lock screen",
        "lock the screen",
        "lock computer",
        "lock my pc",
        "lock the computer",
    ],
    "shutdown": [
        "shutdown",
        "shut down",
        "turn off",
        "power off",
        "shut down computer",
        "turn off computer",
        "shutdown the pc",
    ],
    "restart": [
        "restart",
        "reboot",
        "restart computer",
        "reboot computer",
        "restart the pc",
        "reboot the system",
    ],
    "sleep": [
        "sleep",
        "sleep mode",
        "put to sleep",
        "go to sleep",
        "enter sleep mode",
        "hibernate",
    ],
    "system_info": [
        "system info",
        "show system info",
        "system information",
        "about this pc",
        "computer info",
        "show system information",
        "what are my specs",
    ],
    "run_command": [
        "run {command}",
        "execute {command}",
        "run command {command}",
        "terminal {command}",
        "cmd {command}",
    ],
    "open_settings": [
        "open settings",
        "settings",
        "show settings",
        "go to settings",
        "windows settings",
        "open windows settings",
    ],
    "open_control_panel": [
        "open control panel",
        "control panel",
        "show control panel",
        "launch control panel",
    ],
    "empty_recycle_bin": [
        "empty recycle bin",
        "clear recycle bin",
        "empty the recycle bin",
        "delete recycle bin contents",
        "clean recycle bin",
        "empty trash",
    ],
    
    # === HARDWARE ACTIONS ===
    "brightness_up": [
        "brightness up",
        "increase brightness",
        "brighter",
        "make it brighter",
        "turn up brightness",
        "raise brightness",
    ],
    "brightness_down": [
        "brightness down",
        "decrease brightness",
        "dimmer",
        "make it dimmer",
        "turn down brightness",
        "lower brightness",
    ],
    "set_brightness": [
        "set brightness to {level}",
        "brightness {level}",
        "set brightness {level}",
        "change brightness to {level}",
    ],
    "wifi_toggle": [
        "toggle wifi",
        "turn on wifi",
        "turn off wifi",
        "enable wifi",
        "disable wifi",
        "wifi on",
        "wifi off",
    ],
    "bluetooth_toggle": [
        "toggle bluetooth",
        "turn on bluetooth",
        "turn off bluetooth",
        "enable bluetooth",
        "disable bluetooth",
        "bluetooth on",
        "bluetooth off",
    ],
    "night_light_toggle": [
        "toggle night light",
        "turn on night light",
        "turn off night light",
        "enable night mode",
        "disable night mode",
        "night light on",
        "night light off",
        "blue light filter",
    ],
    "airplane_mode_toggle": [
        "toggle airplane mode",
        "airplane mode on",
        "airplane mode off",
        "enable airplane mode",
        "disable airplane mode",
        "flight mode",
    ],
    
    # === UI ACTIONS ===
    "open_emoji_picker": [
        "open emoji picker",
        "emoji",
        "emojis",
        "show emojis",
        "emoji keyboard",
        "insert emoji",
    ],
    "open_clipboard_history": [
        "open clipboard history",
        "clipboard history",
        "show clipboard",
        "clipboard",
        "paste history",
    ],
}


# ============================================================================
# SLOT FILLERS - Values for template placeholders
# ============================================================================

class SlotFillers:
    """Provides realistic values for template slots."""
    
    APPS = [
        ("chrome", "chrome.exe", ["browser", "web"]),
        ("google chrome", "chrome.exe", ["browser", "web"]),
        ("firefox", "firefox.exe", ["browser", "web"]),
        ("mozilla firefox", "firefox.exe", ["browser", "web"]),
        ("edge", "msedge.exe", ["browser", "web"]),
        ("microsoft edge", "msedge.exe", ["browser", "web"]),
        ("notepad", "notepad.exe", ["editor", "text"]),
        ("vscode", "code.exe", ["editor", "ide"]),
        ("visual studio code", "code.exe", ["editor", "ide"]),
        ("vs code", "code.exe", ["editor", "ide"]),
        ("word", "WINWORD.EXE", ["office", "document"]),
        ("microsoft word", "WINWORD.EXE", ["office", "document"]),
        ("excel", "EXCEL.EXE", ["office", "spreadsheet"]),
        ("microsoft excel", "EXCEL.EXE", ["office", "spreadsheet"]),
        ("powerpoint", "POWERPNT.EXE", ["office", "presentation"]),
        ("spotify", "Spotify.exe", ["music", "media"]),
        ("discord", "Discord.exe", ["chat", "social"]),
        ("slack", "slack.exe", ["chat", "work"]),
        ("teams", "Teams.exe", ["chat", "work"]),
        ("microsoft teams", "Teams.exe", ["chat", "work"]),
        ("terminal", "cmd.exe", ["system", "cli"]),
        ("command prompt", "cmd.exe", ["system", "cli"]),
        ("cmd", "cmd.exe", ["system", "cli"]),
        ("powershell", "powershell.exe", ["system", "cli"]),
        ("calculator", "calc.exe", ["utility"]),
        ("calc", "calc.exe", ["utility"]),
        ("paint", "mspaint.exe", ["graphics", "utility"]),
        ("file explorer", "explorer.exe", ["system", "files"]),
        ("explorer", "explorer.exe", ["system", "files"]),
        ("steam", "steam.exe", ["gaming"]),
        ("obs", "obs64.exe", ["streaming", "recording"]),
        ("vlc", "vlc.exe", ["media", "video"]),
        ("zoom", "Zoom.exe", ["meeting", "video"]),
        ("skype", "Skype.exe", ["chat", "video"]),
        ("telegram", "Telegram.exe", ["chat", "social"]),
        ("whatsapp", "WhatsApp.exe", ["chat", "social"]),
        ("outlook", "OUTLOOK.EXE", ["email", "office"]),
        ("thunderbird", "thunderbird.exe", ["email"]),
        ("gimp", "gimp.exe", ["graphics", "editor"]),
        ("photoshop", "Photoshop.exe", ["graphics", "editor"]),
        ("premiere", "Premiere Pro.exe", ["video", "editor"]),
        ("audacity", "audacity.exe", ["audio", "editor"]),
        ("blender", "blender.exe", ["3d", "graphics"]),
        ("unity", "Unity.exe", ["gaming", "development"]),
    ]
    
    LOCATIONS = [
        ("desktop", "Desktop", "C:\\Users\\{username}\\Desktop"),
        ("my desktop", "Desktop", "C:\\Users\\{username}\\Desktop"),
        ("documents", "Documents", "C:\\Users\\{username}\\Documents"),
        ("my documents", "Documents", "C:\\Users\\{username}\\Documents"),
        ("downloads", "Downloads", "C:\\Users\\{username}\\Downloads"),
        ("my downloads", "Downloads", "C:\\Users\\{username}\\Downloads"),
        ("pictures", "Pictures", "C:\\Users\\{username}\\Pictures"),
        ("my pictures", "Pictures", "C:\\Users\\{username}\\Pictures"),
        ("music", "Music", "C:\\Users\\{username}\\Music"),
        ("my music", "Music", "C:\\Users\\{username}\\Music"),
        ("videos", "Videos", "C:\\Users\\{username}\\Videos"),
        ("my videos", "Videos", "C:\\Users\\{username}\\Videos"),
        ("home", "Home", "C:\\Users\\{username}"),
        ("user folder", "Home", "C:\\Users\\{username}"),
        ("c drive", "C:", "C:\\"),
        ("program files", "Program Files", "C:\\Program Files"),
    ]
    
    FILE_TYPES = [
        ("pdf", ".pdf", "document"),
        ("word", ".docx", "document"),
        ("doc", ".docx", "document"),
        ("excel", ".xlsx", "spreadsheet"),
        ("spreadsheet", ".xlsx", "spreadsheet"),
        ("text", ".txt", "text"),
        ("txt", ".txt", "text"),
        ("image", ".jpg", "image"),
        ("photo", ".jpg", "image"),
        ("picture", ".png", "image"),
        ("video", ".mp4", "video"),
        ("mp4", ".mp4", "video"),
        ("music", ".mp3", "audio"),
        ("audio", ".mp3", "audio"),
        ("mp3", ".mp3", "audio"),
        ("zip", ".zip", "archive"),
        ("python", ".py", "code"),
        ("javascript", ".js", "code"),
        ("json", ".json", "data"),
        ("csv", ".csv", "data"),
        ("html", ".html", "web"),
        ("presentation", ".pptx", "document"),
    ]
    
    FOLDER_NAMES = [
        "Projects", "Work", "Personal", "Backup", "Archive",
        "Photos", "Videos", "Music", "Games", "Notes",
        "School", "University", "Research", "Development", "Testing",
        "Temp", "Old", "New", "Important", "Misc",
        "2024", "2025", "2026", "Assets", "Resources",
        "Documents", "Downloads", "Data", "Code", "Scripts",
    ]
    
    FILENAMES = [
        ("report", "report.docx"),
        ("notes", "notes.txt"),
        ("presentation", "presentation.pptx"),
        ("budget", "budget.xlsx"),
        ("resume", "resume.pdf"),
        ("cv", "cv.pdf"),
        ("readme", "README.md"),
        ("config", "config.json"),
        ("data", "data.csv"),
        ("image", "image.png"),
        ("photo", "photo.jpg"),
        ("video", "video.mp4"),
        ("script", "script.py"),
        ("document", "document.pdf"),
        ("todo", "todo.txt"),
        ("log", "log.txt"),
        ("backup", "backup.zip"),
        # Additional filenames for more variety
        ("meeting notes", "meeting_notes.docx"),
        ("project plan", "project_plan.xlsx"),
        ("invoice", "invoice.pdf"),
        ("contract", "contract.pdf"),
        ("screenshot", "screenshot.png"),
        ("wallpaper", "wallpaper.jpg"),
        ("music", "music.mp3"),
        ("recording", "recording.wav"),
        ("database", "database.db"),
        ("settings", "settings.json"),
        ("styles", "styles.css"),
        ("index", "index.html"),
        ("main", "main.py"),
        ("app", "app.js"),
        ("test", "test.py"),
        ("requirements", "requirements.txt"),
        ("changelog", "CHANGELOG.md"),
        ("license", "LICENSE"),
        ("gitignore", ".gitignore"),
        ("dockerfile", "Dockerfile"),
        ("makefile", "Makefile"),
        ("readme file", "README.txt"),
        ("cover letter", "cover_letter.pdf"),
        ("thesis", "thesis.docx"),
        ("essay", "essay.docx"),
        ("assignment", "assignment.pdf"),
        ("homework", "homework.docx"),
        ("lecture notes", "lecture_notes.pdf"),
        ("study guide", "study_guide.pdf"),
        ("cheat sheet", "cheat_sheet.pdf"),
        ("reference", "reference.docx"),
        ("template", "template.docx"),
        ("form", "form.pdf"),
        ("survey", "survey.xlsx"),
        ("analysis", "analysis.xlsx"),
        ("chart", "chart.xlsx"),
        ("diagram", "diagram.png"),
        ("flowchart", "flowchart.png"),
        ("mockup", "mockup.png"),
        ("design", "design.psd"),
        ("logo", "logo.png"),
        ("icon", "icon.ico"),
        ("banner", "banner.jpg"),
        ("poster", "poster.pdf"),
        ("flyer", "flyer.pdf"),
        ("brochure", "brochure.pdf"),
        ("catalog", "catalog.pdf"),
        ("manual", "manual.pdf"),
        ("guide", "guide.pdf"),
        ("tutorial", "tutorial.pdf"),
        ("handbook", "handbook.pdf"),
        ("policy", "policy.pdf"),
        ("procedure", "procedure.docx"),
        ("checklist", "checklist.xlsx"),
        ("schedule", "schedule.xlsx"),
        ("calendar", "calendar.ics"),
        ("contacts", "contacts.csv"),
        ("addresses", "addresses.xlsx"),
        ("inventory", "inventory.xlsx"),
        ("expense report", "expense_report.xlsx"),
        ("timesheet", "timesheet.xlsx"),
        ("payroll", "payroll.xlsx"),
        ("tax return", "tax_return.pdf"),
        ("bank statement", "bank_statement.pdf"),
        ("receipt", "receipt.pdf"),
        ("order", "order.pdf"),
        ("shipping label", "shipping_label.pdf"),
        ("tracking", "tracking.xlsx"),
        ("feedback", "feedback.docx"),
        ("review", "review.docx"),
        ("summary", "summary.docx"),
        ("report draft", "report_draft.docx"),
        ("final report", "final_report.pdf"),
        ("draft", "draft.docx"),
        ("outline", "outline.docx"),
        ("agenda", "agenda.docx"),
        ("minutes", "minutes.docx"),
        ("proposal", "proposal.pdf"),
        ("quote", "quote.pdf"),
        ("estimate", "estimate.xlsx"),
        ("bid", "bid.pdf"),
    ]
    
    WEBSITES = [
        ("google", "https://google.com"),
        ("youtube", "https://youtube.com"),
        ("github", "https://github.com"),
        ("stackoverflow", "https://stackoverflow.com"),
        ("reddit", "https://reddit.com"),
        ("twitter", "https://twitter.com"),
        ("facebook", "https://facebook.com"),
        ("instagram", "https://instagram.com"),
        ("linkedin", "https://linkedin.com"),
        ("amazon", "https://amazon.com"),
        ("netflix", "https://netflix.com"),
        ("wikipedia", "https://wikipedia.org"),
        ("gmail", "https://mail.google.com"),
        ("drive", "https://drive.google.com"),
        ("docs", "https://docs.google.com"),
    ]
    
    SEARCH_QUERIES = [
        "python tutorial",
        "how to code",
        "best restaurants near me",
        "weather today",
        "latest news",
        "machine learning",
        "web development",
        "javascript guide",
        "windows tips",
        "productivity apps",
        "free music",
        "online courses",
        "stock market",
        "recipe ideas",
        "travel deals",
        # Additional queries
        "react tutorial",
        "typescript basics",
        "docker guide",
        "kubernetes tutorial",
        "aws certification",
        "git commands",
        "linux commands",
        "sql tutorial",
        "mongodb guide",
        "api design",
        "rest api",
        "graphql tutorial",
        "css flexbox",
        "css grid",
        "html5 features",
        "node.js tutorial",
        "express.js guide",
        "django tutorial",
        "flask guide",
        "fastapi tutorial",
        "rust programming",
        "go language",
        "kotlin tutorial",
        "swift programming",
        "flutter tutorial",
        "react native",
        "vue.js guide",
        "angular tutorial",
        "svelte tutorial",
        "next.js guide",
        "tailwind css",
        "bootstrap 5",
        "sass tutorial",
        "webpack guide",
        "vite tutorial",
        "eslint configuration",
        "prettier setup",
        "jest testing",
        "cypress testing",
        "selenium tutorial",
        "postman api",
        "insomnia rest",
        "visual studio code extensions",
        "vim tutorial",
        "neovim setup",
        "zsh configuration",
        "powershell scripting",
        "bash scripting",
        "regex tutorial",
        "json format",
        "yaml syntax",
        "markdown guide",
        "latex tutorial",
        "figma tutorial",
        "photoshop basics",
        "illustrator guide",
        "premiere pro",
        "after effects",
        "blender tutorial",
        "unity game development",
        "unreal engine",
        "godot tutorial",
        "arduino projects",
        "raspberry pi",
        "home automation",
        "smart home",
        "3d printing",
        "electronics basics",
        "circuit design",
        "pcb design",
        "embedded systems",
        "iot projects",
        "cybersecurity basics",
        "ethical hacking",
        "penetration testing",
        "network security",
        "encryption algorithms",
        "blockchain tutorial",
        "cryptocurrency",
        "nft explained",
        "defi guide",
        "trading strategies",
        "investment tips",
        "personal finance",
        "budgeting apps",
        "productivity hacks",
        "time management",
        "note taking apps",
        "task management",
        "project management",
        "agile methodology",
        "scrum guide",
        "kanban board",
        "remote work tips",
        "video conferencing",
        "screen recording",
        "podcast equipment",
        "streaming setup",
        "youtube tutorial",
        "tiktok tips",
        "instagram growth",
        "twitter marketing",
        "linkedin optimization",
        "seo basics",
        "content marketing",
        "email marketing",
        "affiliate marketing",
        "dropshipping guide",
        "ecommerce tips",
        "shopify tutorial",
        "wordpress guide",
        "wix tutorial",
        "squarespace",
        "webflow tutorial",
        "domain hosting",
        "ssl certificate",
        "website security",
        "page speed optimization",
        "google analytics",
        "google ads",
        "facebook ads",
        "social media marketing",
        "influencer marketing",
        "brand building",
        "startup ideas",
        "business plan",
        "pitch deck",
        "venture capital",
        "angel investors",
        "crowdfunding",
        "small business",
        "freelancing tips",
        "remote jobs",
        "resume tips",
        "interview preparation",
        "salary negotiation",
        "career development",
        "leadership skills",
        "communication skills",
        "public speaking",
        "negotiation tactics",
        "conflict resolution",
        "team building",
        "employee motivation",
        "performance review",
        "hr management",
        "recruitment process",
        "onboarding process",
        "company culture",
        "workplace wellness",
        "mental health tips",
        "stress management",
        "meditation guide",
        "yoga for beginners",
        "home workout",
        "nutrition guide",
        "meal planning",
        "healthy recipes",
        "weight loss tips",
        "muscle building",
        "running tips",
        "cycling guide",
        "swimming techniques",
        "hiking trails",
        "camping gear",
        "travel photography",
        "camera settings",
        "photo editing",
        "lightroom tutorial",
        "video editing",
        "color grading",
        "sound design",
        "music production",
        "guitar lessons",
        "piano tutorial",
        "singing tips",
        "songwriting",
        "podcast editing",
        "audiobook recording",
        "voice acting",
        "animation tutorial",
        "motion graphics",
        "vfx tutorial",
        "game design",
        "level design",
        "character design",
        "concept art",
        "digital painting",
        "illustration tips",
        "comic drawing",
        "manga tutorial",
        "watercolor painting",
        "oil painting",
        "sculpture basics",
        "pottery tutorial",
        "woodworking",
        "metalworking",
        "sewing tutorial",
        "knitting patterns",
        "crochet guide",
        "embroidery tutorial",
        "jewelry making",
        "candle making",
        "soap making",
        "home decor diy",
        "furniture restoration",
        "gardening tips",
        "plant care",
        "composting guide",
        "sustainable living",
        "zero waste tips",
        "renewable energy",
        "electric vehicles",
        "solar panels",
        "home improvement",
        "plumbing basics",
        "electrical wiring",
        "hvac maintenance",
        "appliance repair",
        "car maintenance",
        "motorcycle repair",
        "boat maintenance",
        "rv living",
    ]
    
    KEYBOARD_KEYS = [
        ("enter", "enter"),
        ("escape", "escape"),
        ("esc", "escape"),
        ("tab", "tab"),
        ("space", "space"),
        ("backspace", "backspace"),
        ("delete", "delete"),
        ("home", "home"),
        ("end", "end"),
        ("page up", "pageup"),
        ("page down", "pagedown"),
        ("up", "up"),
        ("down", "down"),
        ("left", "left"),
        ("right", "right"),
        ("f1", "f1"),
        ("f5", "f5"),
        ("f11", "f11"),
        ("ctrl+c", "ctrl+c"),
        ("ctrl+v", "ctrl+v"),
        ("ctrl+z", "ctrl+z"),
        ("ctrl+s", "ctrl+s"),
        ("ctrl+a", "ctrl+a"),
        ("alt+tab", "alt+tab"),
        ("alt+f4", "alt+f4"),
        ("win+d", "win+d"),
        ("win+e", "win+e"),
        ("win+r", "win+r"),
    ]
    
    TEXT_SAMPLES = [
        "Hello World",
        "This is a test",
        "Meeting at 3pm",
        "Remember to call",
        "TODO: fix bug",
        "URGENT",
        "Thanks!",
        "See you later",
        "Done",
        "In progress",
    ]
    
    SCROLL_DIRECTIONS = [
        ("up", "up"),
        ("down", "down"),
    ]
    
    BRIGHTNESS_LEVELS = [
        "0%", "10%", "20%", "25%", "30%", "40%", "50%",
        "60%", "70%", "75%", "80%", "90%", "100%",
        "0", "10", "20", "25", "30", "40", "50",
        "60", "70", "75", "80", "90", "100",
        "low", "medium", "high", "max", "minimum", "maximum",
    ]


# ============================================================================
# REASONING TEMPLATES
# ============================================================================

REASONING_TEMPLATES = {
    "open_app": "User wants to launch an application. '{app}' refers to {target}. Action: open_app with target {target}.",
    "kill_process": "User wants to terminate a running application. '{app}' process should be ended. Action: kill_process with target {target}.",
    "list_processes": "User wants to see all running processes. This requires listing active system processes. Action: list_processes.",
    "task_manager": "User wants to open the Windows Task Manager for process management. Action: task_manager.",
    
    "open_file": "User wants to open a file. The file '{filename}' should be opened with its default application. Action: open_file with path to the file.",
    "create_file": "User wants to create a new file. Name: '{filename}', Location: '{location}'. Action: create_file with computed path.",
    "create_and_open_file": "User wants to create a new file and immediately open it. Name: '{filename}'. Action: create_and_open_file.",
    "delete": "User wants to delete a file or folder. Target: '{filename}'. This will move it to recycle bin. Action: delete.",
    "move": "User wants to move a file. Source: '{filename}', Destination: '{destination}'. Action: move.",
    "rename": "User wants to rename a file. Current name: '{filename}', New name: '{newname}'. Action: rename.",
    "copy": "User wants to copy a file. Source: '{filename}', Destination: '{destination}'. Action: copy.",
    "search": "User wants to search for files matching '{query}'. This will search the filesystem. Action: search.",
    "search_and_open": "User wants to find and open a file matching '{query}'. Action: search_and_open.",
    
    "open_folder": "User wants to open a folder in File Explorer. Target: '{folder}'. Action: open_folder with path.",
    "create_folder": "User wants to create a new directory. Name: '{name}', Location: '{location}'. Action: create_folder with computed path.",
    
    "maximize_window": "User wants to maximize the current window to fill the screen. Action: maximize_window.",
    "minimize_window": "User wants to minimize the current window to the taskbar. Action: minimize_window.",
    "close_window": "User wants to close the current window. Action: close_window.",
    "switch_window": "User wants to switch focus to another window. Target: '{app}'. Action: switch_window.",
    "show_desktop": "User wants to minimize all windows and show the desktop. Action: show_desktop.",
    
    "open_url": "User wants to open a website. URL: '{url}'. This will open in the default browser. Action: open_url.",
    "web_search": "User wants to search the web for '{query}'. This will open a search in the browser. Action: web_search.",
    "new_tab": "User wants to open a new browser tab. Action: new_tab.",
    "close_tab": "User wants to close the current browser tab. Action: close_tab.",
    "refresh_page": "User wants to refresh the current webpage. Action: refresh_page.",
    
    "keyboard_action": "User wants to simulate a keyboard press. Key: '{key}'. Action: keyboard_action.",
    "type_text": "User wants to type text. Content: '{text}'. Action: type_text.",
    "click": "User wants to simulate a mouse click. Action: click.",
    "scroll": "User wants to scroll the page. Direction: '{direction}'. Action: scroll.",
    "mouse_action": "User wants to control the mouse cursor. Action: mouse_action.",
    "voice_typing": "User wants to enable voice-to-text input. Action: voice_typing.",
    
    "media_play_pause": "User wants to toggle media playback. Action: media_play_pause.",
    "media_next": "User wants to skip to the next track. Action: media_next.",
    "media_previous": "User wants to go to the previous track. Action: media_previous.",
    "media_stop": "User wants to stop media playback. Action: media_stop.",
    "volume_up": "User wants to increase the system volume. Action: volume_up.",
    "volume_down": "User wants to decrease the system volume. Action: volume_down.",
    "mute": "User wants to mute or unmute the system audio. Action: mute.",
    
    "screenshot": "User wants to capture a screenshot of the screen. Action: screenshot.",
    "lock_screen": "User wants to lock the computer screen. Action: lock_screen.",
    "shutdown": "User wants to shut down the computer. Action: shutdown.",
    "restart": "User wants to restart the computer. Action: restart.",
    "sleep": "User wants to put the computer to sleep. Action: sleep.",
    "system_info": "User wants to view system information. Action: system_info.",
    "run_command": "User wants to run a terminal command. Command: '{command}'. Action: run_command.",
    "open_settings": "User wants to open Windows Settings. Action: open_settings.",
    "open_control_panel": "User wants to open the Control Panel. Action: open_control_panel.",
    "empty_recycle_bin": "User wants to empty the recycle bin. This will permanently delete all items. Action: empty_recycle_bin.",
    
    "brightness_up": "User wants to increase screen brightness. Action: brightness_up.",
    "brightness_down": "User wants to decrease screen brightness. Action: brightness_down.",
    "set_brightness": "User wants to set brightness to a specific level: '{level}'. Action: set_brightness.",
    "wifi_toggle": "User wants to toggle WiFi on or off. Action: wifi_toggle.",
    "bluetooth_toggle": "User wants to toggle Bluetooth on or off. Action: bluetooth_toggle.",
    "night_light_toggle": "User wants to toggle night light mode. Action: night_light_toggle.",
    "airplane_mode_toggle": "User wants to toggle airplane mode. Action: airplane_mode_toggle.",
    
    "open_emoji_picker": "User wants to open the emoji picker. Action: open_emoji_picker.",
    "open_clipboard_history": "User wants to view clipboard history. Action: open_clipboard_history.",
}


# ============================================================================
# SAFETY SAMPLES
# ============================================================================

HARMFUL_PATTERNS = [
    # System destruction
    ("delete system32", "deny", "I cannot delete system-critical files. This would make your computer unusable.", "destructive"),
    ("format c drive", "deny", "I cannot format the system drive. This would destroy all data and the operating system.", "destructive"),
    ("rm -rf /", "deny", "I cannot execute destructive commands that would delete system files.", "destructive"),
    ("delete everything", "deny", "I cannot delete all files. Please specify exactly what you want to delete.", "destructive"),
    ("wipe the hard drive", "deny", "I cannot wipe storage devices. This is an irreversible destructive action.", "destructive"),
    
    # Privilege escalation
    ("bypass uac", "deny", "I cannot bypass Windows security features. UAC exists to protect your system.", "security"),
    ("disable antivirus", "deny", "I cannot disable security software. This would leave your system vulnerable.", "security"),
    ("run as admin without asking", "deny", "I cannot bypass administrator permission prompts. This is a security feature.", "security"),
    ("hack into", "deny", "I cannot perform unauthorized access to systems or accounts.", "security"),
    ("crack password", "deny", "I cannot help with password cracking or unauthorized access.", "security"),
    
    # Privacy violations  
    ("keylogger", "deny", "I cannot install or enable keyloggers. This would violate privacy.", "privacy"),
    ("record without consent", "deny", "I cannot record users without their knowledge and consent.", "privacy"),
    ("spy on", "deny", "I cannot help with surveillance or spying activities.", "privacy"),
    ("access other user accounts", "deny", "I cannot access accounts that don't belong to you.", "privacy"),
    ("steal data", "deny", "I cannot help with data theft or exfiltration.", "privacy"),
    
    # Malware-like behavior
    ("hide from task manager", "deny", "I cannot hide processes from system monitoring tools.", "malware"),
    ("run on startup silently", "deny", "I cannot configure hidden startup programs. Startup items should be visible.", "malware"),
    ("disable firewall", "deny", "I cannot disable the Windows Firewall. This would compromise network security.", "malware"),
    ("inject code", "deny", "I cannot inject code into other processes.", "malware"),
    ("create virus", "deny", "I cannot help create malicious software.", "malware"),
]

OUT_OF_SCOPE_PATTERNS = [
    ("write me a poem", "deny", "I'm designed for Windows automation tasks. I can't write creative content."),
    ("tell me a joke", "deny", "I'm an OS automation assistant. I can help with system tasks, not entertainment."),
    ("what's the meaning of life", "deny", "I'm focused on Windows automation. For general questions, try a search."),
    ("help me with my homework", "deny", "I'm designed for system tasks. I can't help with homework."),
    ("translate this to french", "deny", "I'm a Windows automation assistant. I can't perform translations."),
    ("summarize this article", "deny", "I'm designed for OS tasks. I can't summarize content."),
    ("write code for me", "deny", "I automate Windows tasks. For coding help, try a code assistant."),
    ("explain quantum physics", "deny", "I'm focused on Windows automation. For educational content, try a search."),
]

AMBIGUOUS_PATTERNS = [
    ("open it", "clarify", "Which item would you like me to open?", ["file", "folder", "app"]),
    ("delete that", "clarify", "What would you like me to delete?", ["file", "folder"]),
    ("close it", "clarify", "Which window or app should I close?", ["window", "app"]),
    ("search", "clarify", "What would you like me to search for?", []),
    ("the file", "clarify", "Which file are you referring to?", []),
    ("find files", "clarify", "What type of files should I search for, and where?", []),
    ("open the folder", "clarify", "Which folder would you like me to open?", []),
    ("copy this", "clarify", "What would you like me to copy, and where should I copy it to?", []),
    ("move it", "clarify", "What should I move and where should I move it to?", []),
]

CONFIRM_PATTERNS = [
    ("shutdown", "confirm", "Are you sure you want to shut down the computer? You may lose unsaved work."),
    ("restart", "confirm", "Are you sure you want to restart? You may lose unsaved work."),
    ("empty recycle bin", "confirm", "This will permanently delete all items in the recycle bin. Continue?"),
    ("delete", "confirm", "Are you sure you want to delete this? It will be moved to the recycle bin."),
    ("format", "confirm", "Formatting will erase all data. This cannot be undone. Are you sure?"),
]

ERROR_PATTERNS = [
    ("set brightness to 150%", "error", "invalid_value", "Brightness must be between 0% and 100%."),
    ("open C:\\???\\*<>", "error", "invalid_path", "The path contains invalid characters. Windows filenames cannot include: \\ / : * ? \" < > |"),
    ("delete C:\\Windows\\System32\\kernel32.dll", "error", "access_denied", "Cannot delete system-protected files."),
    ("open nonexistentapp12345.exe", "error", "not_found", "Application not found. Please check the name and try again."),
]


# ============================================================================
# DATASET GENERATOR
# ============================================================================

class DatasetGenerator:
    """Main generator class for creating training datasets."""
    
    def __init__(self, target_size_mb: float = 100.0, include_safety: bool = True):
        self.target_bytes = int(target_size_mb * 1024 * 1024)
        self.include_safety = include_safety
        self.fillers = SlotFillers()
        self.seen_hashes = set()
        self.sample_id = 0
        
        # Category weights for balanced distribution
        # Higher weights for categories with fewer slot combinations
        self.category_weights = {
            "app": 0.14,
            "file": 0.12,
            "folder": 0.08,
            "window": 0.10,
            "browser": 0.12,
            "input": 0.10,
            "media": 0.12,
            "system": 0.10,
            "hardware": 0.08,
            "ui": 0.04,
        }
        
        if include_safety:
            # Reduce other weights to make room for safety
            factor = 0.86
            self.category_weights = {k: v * factor for k, v in self.category_weights.items()}
            self.category_weights["safety"] = 0.14

    def generate(self) -> Generator[Sample, None, None]:
        """Yields samples until target size is reached."""
        current_bytes = 0
        
        while current_bytes < self.target_bytes:
            # Select category based on weights
            categories = list(self.category_weights.keys())
            weights = list(self.category_weights.values())
            category = random.choices(categories, weights=weights, k=1)[0]
            
            if category == "safety":
                sample = self._generate_safety_sample()
            else:
                sample = self._generate_action_sample(category)
            
            if sample and self._is_unique(sample):
                sample_json = json.dumps(asdict(sample))
                current_bytes += len(sample_json.encode('utf-8'))
                yield sample
                
                # Progress indicator
                if self.sample_id % 1000 == 0:
                    progress = (current_bytes / self.target_bytes) * 100
                    print(f"\r  Progress: {progress:.1f}% ({self.sample_id} samples)", end="", flush=True)

    def _generate_action_sample(self, category: str) -> Optional[Sample]:
        """Generate a single action sample."""
        actions = ACTION_TAXONOMY.get(category, {}).get("actions", [])
        if not actions:
            return None
        
        action_type = random.choice(actions)
        phrases = PHRASE_VARIANTS.get(action_type, [])
        if not phrases:
            return None
        
        phrase_template = random.choice(phrases)
        slots = self._fill_slots(action_type)
        
        try:
            instruction = self._format_phrase(phrase_template, slots)
        except KeyError:
            return None
        
        action = self._build_action(action_type, slots)
        reasoning = self._generate_reasoning(action_type, slots)
        difficulty = self._compute_difficulty(action_type, slots)
        tags = self._extract_tags(action_type, slots)
        
        self.sample_id += 1
        return Sample(
            id=f"zentrax_{self.sample_id:06d}",
            instruction=instruction,
            context=self._maybe_add_context(),
            reasoning=reasoning,
            action=asdict(action) if isinstance(action, Action) else action,
            category=category,
            difficulty=difficulty,
            tags=tags
        )

    def _generate_safety_sample(self) -> Optional[Sample]:
        """Generate a safety-related sample."""
        sample_type = random.choice(["deny_harmful", "deny_scope", "clarify", "confirm", "error"])
        
        self.sample_id += 1
        
        if sample_type == "deny_harmful":
            pattern = random.choice(HARMFUL_PATTERNS)
            instruction = pattern[0]
            # Add variation
            variations = [
                instruction,
                f"can you {instruction}",
                f"please {instruction}",
                f"I want to {instruction}",
                f"help me {instruction}",
            ]
            instruction = random.choice(variations)
            
            return Sample(
                id=f"zentrax_{self.sample_id:06d}",
                instruction=instruction,
                context=None,
                reasoning=f"User is requesting a harmful action: {pattern[0]}. This could damage the system or violate security. Must refuse.",
                action={
                    "action": "deny",
                    "reason": pattern[2],
                    "suggestion": None
                },
                category="safety",
                difficulty="simple",
                tags=["deny", "harmful", pattern[3]]
            )
        
        elif sample_type == "deny_scope":
            pattern = random.choice(OUT_OF_SCOPE_PATTERNS)
            return Sample(
                id=f"zentrax_{self.sample_id:06d}",
                instruction=pattern[0],
                context=None,
                reasoning=f"User is asking for something outside my capabilities as an OS automation assistant. This is not a system task.",
                action={
                    "action": "deny",
                    "reason": pattern[2],
                    "suggestion": None
                },
                category="safety",
                difficulty="simple",
                tags=["deny", "out-of-scope"]
            )
        
        elif sample_type == "clarify":
            pattern = random.choice(AMBIGUOUS_PATTERNS)
            return Sample(
                id=f"zentrax_{self.sample_id:06d}",
                instruction=pattern[0],
                context=None,
                reasoning=f"User's request is ambiguous. '{pattern[0]}' does not specify the target clearly. Need to ask for clarification.",
                action={
                    "action": "clarify",
                    "question": pattern[2],
                    "options": pattern[3] if len(pattern) > 3 else []
                },
                category="safety",
                difficulty="medium",
                tags=["clarify", "ambiguous"]
            )
        
        elif sample_type == "confirm":
            pattern = random.choice(CONFIRM_PATTERNS)
            original_action = pattern[0]
            return Sample(
                id=f"zentrax_{self.sample_id:06d}",
                instruction=original_action,
                context={"confirm_required": True},
                reasoning=f"User requested '{original_action}'. This is a potentially destructive or impactful action that requires confirmation.",
                action={
                    "action": "confirm",
                    "warning": pattern[2],
                    "original_action": {
                        "action": original_action.replace(" ", "_"),
                        "target": None,
                        "path": None,
                        "extra": {}
                    }
                },
                category="safety",
                difficulty="medium",
                tags=["confirm", "destructive"]
            )
        
        else:  # error
            pattern = random.choice(ERROR_PATTERNS)
            return Sample(
                id=f"zentrax_{self.sample_id:06d}",
                instruction=pattern[0],
                context=None,
                reasoning=f"User's request contains an error: {pattern[2]}. Cannot execute as specified.",
                action={
                    "action": "error",
                    "error_type": pattern[2],
                    "message": pattern[3]
                },
                category="safety",
                difficulty="simple",
                tags=["error", pattern[2]]
            )

    def _fill_slots(self, action_type: str) -> Dict[str, Any]:
        """Fill template slots with appropriate values."""
        slots = {}
        
        if action_type in ["open_app", "kill_process", "switch_window"]:
            app = random.choice(self.fillers.APPS)
            slots["app"] = app[0]
            slots["target"] = app[1]
            slots["tags"] = app[2]
        
        elif action_type in ["open_file", "create_file", "create_and_open_file", "delete", "copy"]:
            filename = random.choice(self.fillers.FILENAMES)
            location = random.choice(self.fillers.LOCATIONS)
            slots["filename"] = filename[0]
            slots["full_filename"] = filename[1]
            slots["location"] = location[0]
            slots["location_name"] = location[1]
            slots["base_path"] = location[2]
        
        elif action_type in ["move", "rename"]:
            filename = random.choice(self.fillers.FILENAMES)
            location = random.choice(self.fillers.LOCATIONS)
            destination = random.choice(self.fillers.LOCATIONS)
            slots["filename"] = filename[0]
            slots["full_filename"] = filename[1]
            slots["location"] = location[0]
            slots["base_path"] = location[2]
            slots["destination"] = destination[0]
            slots["dest_path"] = destination[2]
            slots["newname"] = random.choice(self.fillers.FILENAMES)[0]
        
        elif action_type in ["search", "search_and_open"]:
            file_type = random.choice(self.fillers.FILE_TYPES)
            location = random.choice(self.fillers.LOCATIONS)
            slots["query"] = file_type[0]
            slots["file_ext"] = file_type[1]
            slots["location"] = location[0]
            slots["search_path"] = location[2]
        
        elif action_type in ["open_folder"]:
            location = random.choice(self.fillers.LOCATIONS)
            slots["folder"] = location[0]
            slots["folder_name"] = location[1]
            slots["path"] = location[2]
        
        elif action_type in ["create_folder"]:
            name = random.choice(self.fillers.FOLDER_NAMES)
            location = random.choice(self.fillers.LOCATIONS)
            slots["name"] = name
            slots["location"] = location[0]
            slots["base_path"] = location[2]
        
        elif action_type in ["open_url"]:
            website = random.choice(self.fillers.WEBSITES)
            slots["url"] = website[1]
            slots["site_name"] = website[0]
        
        elif action_type in ["web_search"]:
            slots["query"] = random.choice(self.fillers.SEARCH_QUERIES)
        
        elif action_type in ["keyboard_action"]:
            key = random.choice(self.fillers.KEYBOARD_KEYS)
            slots["key"] = key[0]
            slots["key_code"] = key[1]
        
        elif action_type in ["type_text"]:
            slots["text"] = random.choice(self.fillers.TEXT_SAMPLES)
        
        elif action_type in ["scroll"]:
            direction = random.choice(self.fillers.SCROLL_DIRECTIONS)
            slots["direction"] = direction[0]
        
        elif action_type in ["set_brightness"]:
            slots["level"] = random.choice(self.fillers.BRIGHTNESS_LEVELS)
        
        elif action_type in ["run_command"]:
            commands = ["dir", "ipconfig", "systeminfo", "tasklist", "whoami", "hostname"]
            slots["command"] = random.choice(commands)
        
        return slots

    def _format_phrase(self, template: str, slots: Dict[str, Any]) -> str:
        """Format a phrase template with slots, adding natural variations."""
        result = template
        for key, value in slots.items():
            result = result.replace(f"{{{key}}}", str(value))
        
        # Add natural variations to increase uniqueness
        variations = [
            ("", ""),  # Original
            ("hey ", ""),
            ("hey zentrax ", ""),
            ("zentrax ", ""),
            ("please ", ""),
            ("can you ", ""),
            ("could you ", ""),
            ("i want to ", ""),
            ("i need to ", ""),
            ("help me ", ""),
            ("", " please"),
            ("", " now"),
            ("", " for me"),
            ("", " quickly"),
            ("", " right now"),
        ]
        
        # 50% chance to add a prefix/suffix variation
        if random.random() < 0.5:
            prefix, suffix = random.choice(variations[1:])  # Skip empty
            result = prefix + result + suffix
        
        return result

    def _build_action(self, action_type: str, slots: Dict[str, Any]) -> Action:
        """Build the action object from slots."""
        action = Action(action=action_type)
        
        if action_type in ["open_app", "kill_process"]:
            action.target = slots.get("target")
        
        elif action_type in ["open_file", "delete"]:
            action.target = slots.get("full_filename")
            base = slots.get("base_path", "")
            action.path = f"{base}\\{slots.get('full_filename', '')}"
        
        elif action_type in ["create_file", "create_and_open_file"]:
            action.target = slots.get("full_filename")
            base = slots.get("base_path", "")
            action.path = f"{base}\\{slots.get('full_filename', '')}"
        
        elif action_type in ["move", "copy"]:
            action.target = slots.get("full_filename")
            action.path = f"{slots.get('base_path', '')}\\{slots.get('full_filename', '')}"
            action.extra = {"destination": f"{slots.get('dest_path', '')}\\{slots.get('full_filename', '')}"}
        
        elif action_type == "rename":
            action.target = slots.get("full_filename")
            action.path = f"{slots.get('base_path', '')}\\{slots.get('full_filename', '')}"
            action.extra = {"new_name": slots.get("newname")}
        
        elif action_type in ["search", "search_and_open"]:
            action.target = f"*{slots.get('file_ext', '')}"
            action.path = slots.get("search_path")
        
        elif action_type == "open_folder":
            action.target = slots.get("folder_name")
            action.path = slots.get("path")
        
        elif action_type == "create_folder":
            action.target = slots.get("name")
            action.path = f"{slots.get('base_path', '')}\\{slots.get('name', '')}"
        
        elif action_type in ["switch_window"]:
            action.target = slots.get("target")
        
        elif action_type == "open_url":
            action.target = slots.get("url")
        
        elif action_type == "web_search":
            action.target = slots.get("query")
        
        elif action_type == "keyboard_action":
            action.target = slots.get("key_code")
        
        elif action_type == "type_text":
            action.target = slots.get("text")
        
        elif action_type == "scroll":
            action.target = slots.get("direction")
        
        elif action_type == "set_brightness":
            action.extra = {"level": slots.get("level")}
        
        elif action_type == "run_command":
            action.target = slots.get("command")
        
        return action

    def _generate_reasoning(self, action_type: str, slots: Dict[str, Any]) -> str:
        """Generate reasoning text for the sample."""
        template = REASONING_TEMPLATES.get(action_type, f"User wants to perform {action_type}. Action: {action_type}.")
        
        try:
            return template.format(**slots)
        except KeyError:
            return f"User wants to perform {action_type}. Executing the requested action."

    def _compute_difficulty(self, action_type: str, slots: Dict[str, Any]) -> str:
        """Compute sample difficulty."""
        simple_actions = ["open_app", "volume_up", "volume_down", "mute", "screenshot", 
                        "maximize_window", "minimize_window", "media_play_pause", "new_tab"]
        complex_actions = ["search_and_open", "move", "rename", "copy", "run_command"]
        
        if action_type in simple_actions:
            return "simple"
        elif action_type in complex_actions:
            return "complex"
        else:
            return "medium"

    def _extract_tags(self, action_type: str, slots: Dict[str, Any]) -> List[str]:
        """Extract relevant tags for the sample."""
        tags = [action_type]
        
        if "tags" in slots:
            tags.extend(slots["tags"])
        
        # Add category-based tags
        for category, data in ACTION_TAXONOMY.items():
            if action_type in data.get("actions", []):
                tags.append(category)
                break
        
        return list(set(tags))

    def _maybe_add_context(self) -> Optional[Dict[str, Any]]:
        """Optionally add context to a sample."""
        if random.random() < 0.3:  # 30% chance
            contexts = [
                {"os": "Windows 11", "time": f"{random.randint(0,23):02d}:{random.randint(0,59):02d}"},
                {"active_window": random.choice(["Chrome", "VS Code", "Explorer", "Word"])},
                {"os": "Windows 10"},
                {"recent_apps": random.sample(["chrome", "notepad", "explorer", "word"], 2)},
            ]
            return random.choice(contexts)
        return None

    def _is_unique(self, sample: Sample) -> bool:
        """Check if sample is unique by instruction hash."""
        h = hashlib.md5(sample.instruction.lower().strip().encode()).hexdigest()
        if h in self.seen_hashes:
            return False
        self.seen_hashes.add(h)
        return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate Zentrax training dataset")
    parser.add_argument("--output", "-o", type=str, default="data/zentrax_train.jsonl",
                       help="Output JSONL file path")
    parser.add_argument("--size", "-s", type=float, default=100.0,
                       help="Target dataset size in MB")
    parser.add_argument("--include-safety", action="store_true", default=True,
                       help="Include safety samples (default: True)")
    parser.add_argument("--no-safety", action="store_true",
                       help="Exclude safety samples")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducibility")
    parser.add_argument("--preview", type=int, default=0,
                       help="Preview N samples without saving")
    
    args = parser.parse_args()
    
    # Set random seed
    random.seed(args.seed)
    
    include_safety = args.include_safety and not args.no_safety
    
    print("=" * 60)
    print("   Zentrax Dataset Generator")
    print("=" * 60)
    print(f"  Target size: {args.size} MB")
    print(f"  Output: {args.output}")
    print(f"  Include safety: {include_safety}")
    print(f"  Random seed: {args.seed}")
    print("=" * 60)
    print()
    
    generator = DatasetGenerator(
        target_size_mb=args.size,
        include_safety=include_safety
    )
    
    if args.preview > 0:
        print(f"Preview mode: showing {args.preview} samples\n")
        for i, sample in enumerate(generator.generate()):
            if i >= args.preview:
                break
            print(json.dumps(asdict(sample), indent=2))
            print("-" * 40)
        return
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("Generating dataset...")
    
    sample_count = 0
    category_counts = {}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in generator.generate():
            f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
            sample_count += 1
            
            cat = sample.category
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print("\n\n" + "=" * 60)
    print("   Generation Complete!")
    print("=" * 60)
    print(f"  Total samples: {sample_count:,}")
    print(f"  Output file: {output_path}")
    print(f"  File size: {output_path.stat().st_size / (1024*1024):.2f} MB")
    print()
    print("  Category distribution:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        pct = (count / sample_count) * 100
        print(f"    {cat}: {count:,} ({pct:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
