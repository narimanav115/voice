"""
Build script for creating a standalone VoiceTranslator distribution.
Manually locates site-packages and forces inclusion of all dependencies.
"""

import subprocess
import sys
import os
import site
import json
from pathlib import Path


def find_site_packages():
    """Find the site-packages directory."""
    # Try multiple approaches
    for sp in site.getsitepackages():
        if os.path.isdir(sp):
            print(f"  Found site-packages: {sp}")
            return sp
    
    # Fallback: derive from sys.executable
    if sys.platform == 'win32':
        sp = os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages')
    else:
        sp = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 
                          'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 
                          'site-packages')
    
    if os.path.isdir(sp):
        print(f"  Found site-packages (fallback): {sp}")
        return sp
    
    raise RuntimeError("Could not find site-packages directory!")


def get_package_dirs(site_pkg):
    """Find actual package directories in site-packages."""
    # Critical packages that MUST be included
    critical_packages = [
        'torch', 'torchaudio', 'torchvision',
        'TTS',
        'transformers',
        'faster_whisper',
        'tokenizers',
        'huggingface_hub',
        'ctranslate2',
        'sentencepiece',
        'librosa',
        'soundfile', '_soundfile_data',
        'scipy',
        'numpy', 'numpy.libs',
        'PyQt6',
        'onnxruntime',
        'ffmpeg',
        'pydub',
        'resampy',
        'audioread',
        'numba',
        'llvmlite',
        'safetensors',
        'yaml', 'pyyaml',
        'regex',
        'filelock',
        'tqdm',
        'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna',
        'packaging',
        'fsspec',
        'coqpit',
        'gruut',
        'trainer',
    ]
    
    found = []
    sep = ';' if sys.platform == 'win32' else ':'
    
    for pkg in critical_packages:
        pkg_path = os.path.join(site_pkg, pkg)
        if os.path.isdir(pkg_path):
            found.append((pkg_path, pkg))
            print(f"  [OK] {pkg} ({_dir_size_mb(pkg_path):.1f} MB)")
        else:
            # Try lowercase
            pkg_lower = pkg.lower()
            pkg_path_lower = os.path.join(site_pkg, pkg_lower)
            if os.path.isdir(pkg_path_lower):
                found.append((pkg_path_lower, pkg_lower))
                print(f"  [OK] {pkg_lower} ({_dir_size_mb(pkg_path_lower):.1f} MB)")
            else:
                print(f"  [--] {pkg} - not found")
    
    # Also find .libs directories (e.g., torch.libs, numpy.libs)
    for item in os.listdir(site_pkg):
        if item.endswith('.libs') and os.path.isdir(os.path.join(site_pkg, item)):
            full_path = os.path.join(site_pkg, item)
            if not any(f[1] == item for f in found):
                found.append((full_path, item))
                print(f"  [OK] {item} (binary libs, {_dir_size_mb(full_path):.1f} MB)")
    
    return found


def _dir_size_mb(path):
    """Get directory size in MB."""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            total += os.path.getsize(os.path.join(dirpath, f))
    return total / (1024 * 1024)


def build():
    print("=" * 60)
    print("  VoiceTranslator - Standalone Build")
    print("=" * 60)
    print()

    # Step 1: Find site-packages
    print("[1/4] Locating site-packages...")
    site_pkg = find_site_packages()
    print()

    # Step 2: Find package directories
    print("[2/4] Finding package directories...")
    packages = get_package_dirs(site_pkg)
    print(f"\n  Found {len(packages)} packages to include\n")

    # Step 3: Build PyInstaller command
    print("[3/4] Building PyInstaller command...")
    
    sep = ';' if sys.platform == 'win32' else ':'

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        '--name=VoiceTranslator',
        '--onedir',
        '--windowed',
        f'--add-data=config.py{sep}.',
        f'--add-data=src{sep}src',
        f'--paths={site_pkg}',
    ]

    # Add each package as --add-data
    for pkg_path, pkg_name in packages:
        cmd.append(f'--add-data={pkg_path}{sep}{pkg_name}')
    
    # Hidden imports
    hidden = [
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip',
        'faster_whisper', 'transformers', 'TTS', 'TTS.api',
        'torch', 'torch.nn', 'torch.utils',
        'librosa', 'soundfile', 'ffmpeg', 'numpy', 'scipy', 'pydub',
        'huggingface_hub', 'tokenizers', 'sentencepiece', 'ctranslate2',
    ]
    for h in hidden:
        cmd.extend(['--hidden-import', h])

    # Excludes
    for exc in ['matplotlib', 'tkinter', 'IPython', 'jupyter', 'notebook', 'pytest']:
        cmd.extend(['--exclude-module', exc])

    if os.path.exists('icon.ico'):
        cmd.extend(['--icon', 'icon.ico'])

    cmd.append('main.py')

    # Print estimated size
    total_pkg_size = sum(_dir_size_mb(p) for p, _ in packages)
    print(f"  Estimated output size: ~{total_pkg_size:.0f} MB")
    print()

    # Step 4: Run build
    print("[4/4] Running PyInstaller (10-30 minutes)...")
    print()

    result = subprocess.run(cmd, cwd=os.getcwd())

    if result.returncode != 0:
        print("\nERROR: PyInstaller failed!")
        sys.exit(1)

    # Verify output
    dist_folder = os.path.join('dist', 'VoiceTranslator')
    exe_name = 'VoiceTranslator.exe' if sys.platform == 'win32' else 'VoiceTranslator'
    exe_path = os.path.join(dist_folder, exe_name)

    if os.path.exists(dist_folder):
        total_size = 0
        for dirpath, _, filenames in os.walk(dist_folder):
            for f in filenames:
                total_size += os.path.getsize(os.path.join(dirpath, f))
        size_mb = total_size / (1024 * 1024)

        print()
        print("BUILD COMPLETE!")
        print(f"  Folder: {dist_folder}")
        print(f"  Total size: {size_mb:.0f} MB")
        print()

        if size_mb < 100:
            print(f"ERROR: Build is only {size_mb:.0f} MB - dependencies missing!")
            
            # Debug: list what's in dist
            print("\nContents of dist/VoiceTranslator/:")
            for item in sorted(os.listdir(dist_folder)):
                full = os.path.join(dist_folder, item)
                if os.path.isdir(full):
                    print(f"  [DIR] {item} ({_dir_size_mb(full):.1f} MB)")
                else:
                    s = os.path.getsize(full) / (1024 * 1024)
                    print(f"  [FILE] {item} ({s:.1f} MB)")
            
            sys.exit(1)
        else:
            print(f"  Size OK! ({size_mb:.0f} MB)")
            print(f"\n  To run: {exe_path}")
    else:
        print("ERROR: dist folder not found!")
        sys.exit(1)


if __name__ == '__main__':
    build()
