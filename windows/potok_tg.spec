# -*- mode: python ; coding: utf-8 -*-
# Builds a single-file Windows executable (PotokBot.exe).
#
# ffmpeg.exe and .env.example are NOT bundled inside the exe here - they are
# copied next to it as plain files by windows/build.ps1 / the CI workflow.
# Keeping ffmpeg outside the onefile archive avoids re-extracting an ~80MB
# binary into a temp dir on every single launch.
#
# Usage: pyinstaller windows/potok_tg.spec  (run from the project root)
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 - injected by PyInstaller

a = Analysis(
    [str(ROOT / "windows" / "run.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PotokBot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
