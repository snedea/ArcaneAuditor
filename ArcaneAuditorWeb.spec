# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
import sys, os
sys.path.append(os.path.abspath("."))

hidden_imports = (
    collect_submodules("parser.rules")
    + collect_submodules("pydantic")
    + collect_submodules("lark") 
    + collect_submodules("fastapi")
    + collect_submodules("starlette")
    + collect_submodules("uvicorn")
)


a = Analysis(
    ['web/server.py'],
    pathex=[],
    binaries=[],
    datas = [
        # --- Web service config (for AppData seeding) ---
        ("config/web/web_service_config.json.sample", "config/web"),

        # --- Rule presets ---
        ("config/rules/presets", "config/rules/presets"),

        # --- Delivered rule directories ---
        ("parser/rules/script", "parser/rules/script"),
        ("parser/rules/structure", "parser/rules/structure"),

        # --- Frontend files (HTML, CSS, JS) ---
        ("web/frontend", "web/frontend"),

        # --- Grammar for PMD parsing ---
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
    name='ArcaneAuditorWeb',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # keep True for debug; set False later if you want silent mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=os.environ.get('CODESIGN_IDENTITY'),
    entitlements_file='entitlements.plist' if os.path.exists('entitlements.plist') else None,
)
