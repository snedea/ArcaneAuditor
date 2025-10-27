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
        # --- Assets (logos) ---
        ("assets/arcane-auditor-splash.webp", "assets"),  # Splash screen image
        ("assets/icons", "assets"),  # Application icon

        # --- Web service config (for AppData seeding) ---
        ("config/web/web_service_config.json.sample", "config/web"),

        # --- Rule presets ---
        ("config/rules/presets", "config/rules/presets"),

        # --- Delivered rule directories ---
        ("parser/rules/script", "parser/rules/script"),
        ("parser/rules/structure", "parser/rules/structure"),

        # --- Frontend files (HTML, CSS, JS) ---
        # Note: splash.html goes in web/frontend/ and is bundled here
        ("web/frontend", "web/frontend"),

        # --- Grammar for PMD parsing ---
        ("parser/pmd_script_grammar.lark", "parser"),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'PIL', 'numpy', 'pandas', 'scipy', 'wx'],  # Exclude unused heavy packages
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if sys.platform == 'darwin':
    # macOS: Use onedir mode (no extraction delay)
    exe = EXE(
        pyz,
        a.scripts,
        [],  # Remove binaries and datas from EXE for onedir mode
        exclude_binaries=True,  # Key change for onedir mode
        name='ArcaneAuditor',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        icon='assets/icons/aa-mac.icns',
    )
    
    # COLLECT creates the onedir structure
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='ArcaneAuditor',
    )
    
    # Create .app bundle wrapping the onedir structure
    app = BUNDLE(
        coll,
        name='ArcaneAuditor.app',
        icon='assets/icons/aa-mac.icns',
        bundle_identifier='com.arcaneauditor.desktop',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2025',
        },
    )
else:
    # Windows: Use onefile mode (single executable)
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='ArcaneAuditor',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        icon='assets/icons/aa-windows.ico',
    )
