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
    + collect_submodules("webview")  # Add pywebview
    + ["requests"] 
)

a = Analysis(
    ['arcane_auditor_desktop.py'],  # The desktop launcher
    pathex=[os.path.abspath(".")],
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
    name='ArcaneAuditor',  # Clean name without "CLI" or "Web" suffix
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # NO CONSOLE WINDOW - this is key for desktop app!
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Uncomment when you have an icon:
    # icon='assets/icon.ico',  # Windows
    # icon='assets/icon.icns',  # macOS (PyInstaller picks the right one)
)

# macOS: Create a .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='ArcaneAuditor.app',
        # icon='assets/icon.icns',  # Uncomment when you have an icon
        bundle_identifier='com.arcaneauditor.desktop',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2025',
        },
    )
