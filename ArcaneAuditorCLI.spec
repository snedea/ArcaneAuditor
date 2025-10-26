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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ArcaneAuditorCLI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=os.environ.get('CODESIGN_IDENTITY'),
    entitlements_file='entitlements.plist' if os.path.exists('entitlements.plist') else None,
)
