"""
Build script for VoiceTranslator Windows distribution.

Uses the SYSTEM Python (from GitHub Actions setup-python) to install 
all packages into a target directory via `pip install --target`, then
bundles that with the Python embeddable package.

Result: A folder with embedded Python + all packages + launcher.
"""

import subprocess
import sys
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

# Python embeddable version to use
PYTHON_VERSION = "3.10.11"
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"


def download_file(url, dest):
    """Download a file with progress."""
    print(f"  Downloading: {url}")
    urllib.request.urlretrieve(url, dest)
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    print(f"  Downloaded: {size_mb:.1f} MB")


def build():
    print("=" * 60)
    print("  VoiceTranslator - Windows Portable Build")
    print("=" * 60)
    print()

    dist_dir = Path("dist")
    app_dir = dist_dir / "VoiceTranslator"
    python_dir = app_dir / "python"
    site_packages = python_dir / "Lib" / "site-packages"
    
    # Clean previous build
    if app_dir.exists():
        print("Cleaning previous build...")
        shutil.rmtree(app_dir)
    
    app_dir.mkdir(parents=True, exist_ok=True)
    python_dir.mkdir(parents=True, exist_ok=True)
    site_packages.mkdir(parents=True, exist_ok=True)

    # Step 1: Download Python embeddable
    print("[1/6] Downloading Python embeddable package...")
    embed_zip = dist_dir / "python-embed.zip"
    if not embed_zip.exists():
        download_file(PYTHON_EMBED_URL, str(embed_zip))
    else:
        print("  Using cached download")
    
    print("  Extracting...")
    with zipfile.ZipFile(str(embed_zip), 'r') as z:
        z.extractall(str(python_dir))

    # Step 2: Configure embedded Python to use site-packages
    print("\n[2/6] Configuring embedded Python...")
    
    # Edit python310._pth to enable site-packages
    pth_files = list(python_dir.glob("python*._pth"))
    if pth_files:
        pth_file = pth_files[0]
        # Rewrite the _pth file completely
        pth_file.write_text(
            "python310.zip\n"
            ".\n"
            "Lib\\site-packages\n"
            "import site\n"
        )
        print(f"  Updated {pth_file.name}")
    else:
        print("  WARNING: No ._pth file found!")

    # Step 3: Install dependencies using SYSTEM Python's pip 
    # with --target pointing to our embedded Python's site-packages
    print("\n[3/6] Installing dependencies via system pip --target (10-20 min)...")
    print(f"  System Python: {sys.executable}")
    print(f"  Target: {site_packages.absolute()}")
    
    req_file = Path("requirements.txt").absolute()
    
    # First, upgrade system pip
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        check=True
    )
    
    # Install all requirements into the target directory
    subprocess.run(
        [sys.executable, "-m", "pip", "install",
         "-r", str(req_file),
         "--target", str(site_packages.absolute()),
         "--no-warn-script-location"],
        check=True
    )
    
    # Verify key packages were installed
    print("\n  Verifying installed packages:")
    key_packages = ['torch', 'transformers', 'TTS', 'faster_whisper', 'PyQt6', 'numpy']
    for pkg in key_packages:
        pkg_dir = site_packages / pkg
        if pkg_dir.exists():
            size = sum(f.stat().st_size for f in pkg_dir.rglob('*') if f.is_file()) / (1024*1024)
            print(f"    [OK] {pkg} ({size:.0f} MB)")
        else:
            print(f"    [!!] {pkg} - NOT FOUND")

    # Step 4: Copy application files
    print("\n[4/6] Copying application files...")
    
    # Copy source code
    for item in ["main.py", "config.py"]:
        src = Path(item)
        if src.exists():
            shutil.copy2(str(src), str(app_dir))
            print(f"  Copied {item}")
    
    # Copy src directory
    src_dir = Path("src")
    if src_dir.exists():
        dest_src = app_dir / "src"
        if dest_src.exists():
            shutil.rmtree(str(dest_src))
        shutil.copytree(str(src_dir), str(dest_src))
        print("  Copied src/")
    
    # Copy docs
    for doc in ["README.md", "QUICKSTART.md"]:
        if Path(doc).exists():
            shutil.copy2(doc, str(app_dir))

    # Create necessary directories
    for d in ["models", "downloads", "output", "logs"]:
        (app_dir / d).mkdir(exist_ok=True)

    # Step 5: Create launcher
    print("\n[5/6] Creating launcher...")
    
    # BAT launcher
    launcher_bat = app_dir / "VoiceTranslator.bat"
    launcher_bat.write_text(
        '@echo off\r\n'
        'cd /d "%~dp0"\r\n'
        'start "" python\\python.exe main.py\r\n',
        encoding='utf-8'
    )
    print("  Created VoiceTranslator.bat")

    # Also create a simple C launcher that can be compiled, 
    # or use a Python script to create a minimal .exe wrapper
    launcher_py = app_dir / "_launcher.py"
    launcher_py.write_text(
        'import subprocess, sys, os\n'
        'app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))\n'
        'python = os.path.join(app_dir, "python", "python.exe")\n'
        'main = os.path.join(app_dir, "main.py")\n'
        'subprocess.Popen([python, main], cwd=app_dir)\n',
        encoding='utf-8'
    )

    # Create a VBS launcher (invisible CMD window)
    launcher_vbs = app_dir / "VoiceTranslator.vbs"
    launcher_vbs.write_text(
        'Set WshShell = CreateObject("WScript.Shell")\r\n'
        'WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)\r\n'
        'WshShell.Run "python\\pythonw.exe main.py", 0, False\r\n',
        encoding='utf-8'
    )
    print("  Created VoiceTranslator.vbs (no console window)")

    # Step 6: Create info file
    info = app_dir / "FIRST_RUN.txt"
    info.write_text(
        "VoiceTranslator - Offline Voice-to-Voice Translator (RU -> EN)\r\n"
        "================================================================\r\n\r\n"
        "HOW TO RUN:\r\n"
        "  Double-click VoiceTranslator.bat\r\n"
        "  Or double-click VoiceTranslator.vbs (no console window)\r\n\r\n"
        "FIRST RUN:\r\n"
        "  ML models will be downloaded automatically (~7-8 GB)\r\n"
        "  This requires internet connection only once\r\n"
        "  After that, the app works fully offline\r\n\r\n"
        "REQUIREMENTS:\r\n"
        "  FFmpeg must be installed: https://ffmpeg.org/download.html\r\n"
        "  Or install via: choco install ffmpeg\r\n",
        encoding='utf-8'
    )

    # Calculate total size
    print("\n[6/6] Verifying build...")
    total_size = 0
    for dirpath, _, filenames in os.walk(str(app_dir)):
        for f in filenames:
            total_size += os.path.getsize(os.path.join(dirpath, f))
    size_mb = total_size / (1024 * 1024)

    print()
    print("=" * 60)
    print(f"  BUILD COMPLETE!")
    print(f"  Output: {app_dir}")
    print(f"  Size:   {size_mb:.0f} MB")
    print("=" * 60)

    if size_mb < 100:
        print(f"\nWARNING: Only {size_mb:.0f} MB - something may be missing")
        sys.exit(1)
    else:
        print(f"\n  Size looks correct ({size_mb:.0f} MB)")
        print(f"\n  To test: {app_dir / 'VoiceTranslator.bat'}")


if __name__ == '__main__':
    build()
