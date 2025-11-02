# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
import sys, os
sys.path.append(os.path.abspath("."))

hidden_imports = (
    collect_submodules("parser.rules")
    + collect_submodules("typer")
    + collect_submodules("click")
    + collect_submodules("pydantic")
    + collect_submodules("lark") 
)


a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath(".")],
    binaries=[],
    datas=[
    ("config/rules/presets", "config/rules/presets"),
    ("parser/rules/script", "parser/rules/script"),
    ("parser/rules/structure", "parser/rules/structure"),
    ("parser/pmd_script_grammar.lark", "parser"),
    ("assets/icons", "assets"),  # Application icon
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")

ONEFILE_MODE = IS_WIN  # onefile for Windows, onedir for macOS

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ArcaneAuditorCLI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon='assets/icons/aa-mac.icns' if IS_MAC else 'assets/icons/aa-windows.ico',
    codesign_identity=os.environ.get('MAC_IDENTITY', None) if IS_MAC else None,
    entitlements_file='entitlements.plist' if IS_MAC else None,
    onefile=ONEFILE_MODE,
)

if not ONEFILE_MODE:
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        name='ArcaneAuditorCLI',
    )