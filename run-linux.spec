# -*- mode: python -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['/Users/pierre/src/node-launcher'],
    binaries=[],
    datas=[
        ('node_launcher/assets/*.png', 'assets')
    ],
    hiddenimports=['setuptools'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# -*- mode: python -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['/home/tehelsper/github/node_launcher'],
    binaries=[],
    datas=[
        ('node_launcher/assets/*.png', 'assets')
    ],
    hiddenimports=['setuptools'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='node_launcher.bin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False
)
