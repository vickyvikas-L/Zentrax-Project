# -*- mode: python ; coding: utf-8 -*-
"""
Zentrax PyInstaller Spec File
For advanced customization of the build process.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# Collect all necessary packages
mediapipe_datas, mediapipe_binaries, mediapipe_hiddenimports = collect_all('mediapipe')
whisper_datas, whisper_binaries, whisper_hiddenimports = collect_all('whisper')

# Additional data files
added_datas = [
    ('training_data', 'training_data'),
    ('frontend', 'frontend'),
    ('src', 'src'),
]

# Combine all data files
all_datas = mediapipe_datas + whisper_datas + added_datas

# Hidden imports
hidden_imports = [
    'pyttsx3.drivers',
    'pyttsx3.drivers.sapi5',
    'speech_recognition',
    'pyautogui',
    'cv2',
    'numpy',
    'torch',
    'sounddevice',
    'scipy',
    'win32gui',
    'win32con',
    'win32api',
    'psutil',
    'requests',
    'PIL',
] + mediapipe_hiddenimports + whisper_hiddenimports

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=mediapipe_binaries + whisper_binaries,
    datas=all_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Zentrax',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False for no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='zentrax.ico' if os.path.exists('zentrax.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Zentrax',
)
