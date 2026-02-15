"""
Build script for creating a standalone VoiceTranslator.exe
Dynamically discovers all installed packages and builds a single-file executable.
"""

import subprocess
import sys
import os
import importlib.metadata


def get_collect_args():
    """Generate --collect-all and --hidden-import args for all critical packages."""
    
    # Packages that need full collection (all data files, submodules, binaries)
    collect_all = [
        'TTS',
        'transformers',
        'faster_whisper',
        'torch',
        'torchaudio',
        'tokenizers',
        'huggingface_hub',
        'ctranslate2',
        'sentencepiece',
        'librosa',
        'soundfile',
        'scipy',
        'numpy',
        'PyQt6',
    ]

    # Additional hidden imports that PyInstaller misses
    hidden_imports = [
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'faster_whisper',
        'transformers',
        'transformers.models',
        'transformers.utils',
        'TTS',
        'TTS.api',
        'TTS.tts',
        'TTS.tts.configs',
        'TTS.tts.models',
        'TTS.utils',
        'TTS.vocoder',
        'torch',
        'torch.nn',
        'torch.utils',
        'torchaudio',
        'librosa',
        'librosa.core',
        'librosa.feature',
        'librosa.effects',
        'librosa.util',
        'soundfile',
        'ffmpeg',
        'numpy',
        'numpy.core',
        'scipy',
        'scipy.signal',
        'scipy.fft',
        'pydub',
        'huggingface_hub',
        'tokenizers',
        'sentencepiece',
        'ctranslate2',
        'onnxruntime',
        'resampy',
        'audioread',
        'numba',
        'sklearn',
        'sklearn.utils',
    ]

    # Modules to exclude (reduce size)
    excludes = [
        'matplotlib',
        'tkinter',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
        'docutils',
        'pygments',
    ]

    args = []

    # Only collect packages that are actually installed
    for pkg in collect_all:
        try:
            importlib.metadata.distribution(pkg)
            args.extend(['--collect-all', pkg])
        except importlib.metadata.PackageNotFoundError:
            # Try alternate names
            alt = pkg.replace('-', '_').replace('.', '_').lower()
            try:
                importlib.metadata.distribution(alt)
                args.extend(['--collect-all', alt])
            except importlib.metadata.PackageNotFoundError:
                print(f"  [SKIP] {pkg} not installed, skipping collect-all")

    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])

    for exc in excludes:
        args.extend(['--exclude-module', exc])

    return args


def build():
    """Run PyInstaller build."""
    print("=" * 60)
    print("  VoiceTranslator - Standalone EXE Builder")
    print("=" * 60)
    print()

    # Base PyInstaller arguments
    base_args = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        '--name=VoiceTranslator',
        '--onefile',
        '--windowed',
        '--add-data', f'config.py{os.pathsep}.',
        '--add-data', f'src{os.pathsep}src',
    ]

    # Add icon if it exists
    if os.path.exists('icon.ico'):
        base_args.extend(['--icon', 'icon.ico'])

    # Get dynamic collect/import args
    print("[1/3] Discovering installed packages...")
    extra_args = get_collect_args()
    print(f"  Found {len(extra_args) // 2} package directives")

    # Final command
    cmd = base_args + extra_args + ['main.py']

    print()
    print("[2/3] Building standalone EXE (this will take 10-20 minutes)...")
    print()

    result = subprocess.run(cmd, cwd=os.getcwd())

    if result.returncode != 0:
        print()
        print("ERROR: Build failed!")
        sys.exit(1)

    # Check output
    exe_path = os.path.join('dist', 'VoiceTranslator.exe')
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print()
        print("[3/3] Build complete!")
        print(f"  Output: {exe_path}")
        print(f"  Size:   {size_mb:.1f} MB")
        print()

        if size_mb < 50:
            print("WARNING: EXE is very small ({:.1f} MB).".format(size_mb))
            print("  Some dependencies may not be included.")
            print("  Expected size: 500-1500 MB")
        else:
            print("  Size looks correct for a standalone build.")
    else:
        print("ERROR: EXE not found at", exe_path)
        sys.exit(1)


if __name__ == '__main__':
    build()
