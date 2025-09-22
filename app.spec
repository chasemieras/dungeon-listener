# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_all

# Auto-discover ALL submodules for major packages
all_hiddenimports = []
all_datas = []
all_binaries = []

# List of packages to fully auto-discover
packages_to_discover = [
    'whisperx',
    'speechbrain', 
    'transformers',
    'torch',
    'torchaudio',
    'lightning_fabric',
    'pytorch_lightning',
    'pyannote',
    'asteroid_filterbanks',
    'asteroid',
    'librosa',
    'scipy',
    'numpy',
    'nltk',
    'faster_whisper',
    'ctranslate2',
    'matplotlib',
]

# Auto-discover everything for each package
for package in packages_to_discover:
    try:
        # Get all submodules
        submodules = collect_submodules(package)
        all_hiddenimports.extend(submodules)
        
        # Get all data files
        datas = collect_data_files(package, include_py_files=True)
        if datas:
            all_datas.extend(datas)
            
        print(f"Auto-discovered {len(submodules)} modules from {package}")
    except Exception as e:
        print(f"Could not auto-discover {package}: {e}")

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports + [
        # Add any specific modules that auto-discovery might miss
        'customtkinter',
        'pyaudio',
        'requests',
        'urllib3',
        'threading',
        'queue',
        'subprocess',
        'pathlib',
        'datetime',
        'gc',
        'pydoc',
        'doctest',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Only exclude if absolutely necessary
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disabled for AI libraries
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='app',
)