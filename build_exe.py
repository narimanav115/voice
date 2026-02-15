"""
Build script for creating a standalone VoiceTranslator distribution.
Creates a folder with EXE + all dependencies (onedir mode).
This is the only reliable way to bundle PyTorch + TTS + transformers.
"""

import subprocess
import sys
import os
import json


def get_installed_packages():
    """Get set of installed package names using pip list."""
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'list', '--format=json'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("WARNING: Could not get pip list, will pass all flags unconditionally")
        return None
    
    packages = json.loads(result.stdout)
    return {pkg['name'].lower().replace('-', '_') for pkg in packages}


def get_pyinstaller_args():
    """Generate PyInstaller arguments based on installed packages."""

    installed = get_installed_packages()

    # Packages to collect-all: (pip_name, lookup_name for pip list)
    collect_all_candidates = [
        ('TTS', 'tts'),
        ('transformers', 'transformers'),
        ('faster_whisper', 'faster_whisper'),
        ('torch', 'torch'),
        ('torchaudio', 'torchaudio'),
        ('tokenizers', 'tokenizers'),
        ('huggingface_hub', 'huggingface_hub'),
        ('ctranslate2', 'ctranslate2'),
        ('sentencepiece', 'sentencepiece'),
        ('librosa', 'librosa'),
        ('soundfile', 'soundfile'),
        ('scipy', 'scipy'),
        ('numpy', 'numpy'),
        ('PyQt6', 'pyqt6'),
        ('onnxruntime', 'onnxruntime'),
    ]

    hidden_imports = [
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip',
        'faster_whisper',
        'transformers', 'transformers.models', 'transformers.utils',
        'TTS', 'TTS.api', 'TTS.tts', 'TTS.tts.configs', 'TTS.tts.models',
        'TTS.utils', 'TTS.vocoder',
        'torch', 'torch.nn', 'torch.utils', 'torch.cuda',
        'torchaudio',
        'librosa', 'librosa.core', 'librosa.feature', 'librosa.effects', 'librosa.util',
        'soundfile', 'ffmpeg',
        'numpy', 'numpy.core',
        'scipy', 'scipy.signal', 'scipy.fft',
        'pydub',
        'huggingface_hub', 'tokenizers', 'sentencepiece',
        'ctranslate2', 'onnxruntime',
        'resampy', 'audioread', 'numba',
    ]

    excludes = [
        'matplotlib', 'tkinter', 'IPython', 'jupyter',
        'notebook', 'pytest', 'sphinx', 'docutils', 'pygments',
    ]

    args = []

    for pip_name, lookup_name in collect_all_candidates:
        # If we couldn't get pip list, include everything
        if installed is None or lookup_name in installed:
            args.extend(['--collect-all', pip_name])
            args.extend(['--collect-submodules', pip_name])
            print(f"  [OK] {pip_name}")
        else:
            print(f"  [SKIP] {pip_name} - not installed")

    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])

    for exc in excludes:
        args.extend(['--exclude-module', exc])

    return args


def build():
    print("=" * 60)
    print("  VoiceTranslator — Standalone Build")
    print("=" * 60)
    print()

    # Use --onedir (reliable for large ML projects)
    base_args = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        '--name=VoiceTranslator',
        '--onedir',
        '--windowed',
        '--add-data', f'config.py{os.pathsep}.',
        '--add-data', f'src{os.pathsep}src',
    ]

    if os.path.exists('icon.ico'):
        base_args.extend(['--icon', 'icon.ico'])

    print("[1/3] Scanning installed packages...")
    extra_args = get_pyinstaller_args()
    print()

    cmd = base_args + extra_args + ['main.py']

    print("[2/3] Building (this takes 10-20 minutes)...")
    print()

    result = subprocess.run(cmd, cwd=os.getcwd())

    if result.returncode != 0:
        print("\nERROR: Build failed!")
        sys.exit(1)

    # Verify output
    dist_folder = os.path.join('dist', 'VoiceTranslator')
    exe_path = os.path.join(dist_folder, 'VoiceTranslator.exe')

    if os.path.exists(exe_path):
        # Calculate total folder size
        total_size = 0
        for dirpath, _, filenames in os.walk(dist_folder):
            for f in filenames:
                total_size += os.path.getsize(os.path.join(dirpath, f))
        size_mb = total_size / (1024 * 1024)

        print()
        print("[3/3] Build complete!")
        print(f"  Folder: {dist_folder}")
        print(f"  EXE:    {exe_path}")
        print(f"  Total:  {size_mb:.0f} MB")
        print()

        if size_mb < 100:
            print(f"WARNING: Build is only {size_mb:.0f} MB — something is missing!")
            print("  Expected: 500+ MB")
            sys.exit(1)
        else:
            print("  Looks correct!")
            print()
            print("  To run: dist/VoiceTranslator/VoiceTranslator.exe")
    else:
        print("ERROR: EXE not found at", exe_path)
        sys.exit(1)


if __name__ == '__main__':
    build()
