# -*- mode: python -*-
import sys

block_cipher = None

# Collect all the image files and data files
datas = [
    ('quadstickx.ico', '.'),
    ('logo.png', '.'),
    ('blue.png', '.'),
    ('blue.svg', '.'),
    ('grey.png', '.'),
    ('grey.svg', '.'),
    ('pink.png', '.'),
    ('purple.svg', '.'),
    ('red.png', '.'),
    ('red.svg', '.'),
    ('joystick active zones.svg', '.'),
]

try:
    import certifi
    datas.append((certifi.where(), 'certifi'))
except ImportError:
    print("Warning: certifi not installed, SSL certificates may not work in bundled app")

a = Analysis(
    ['QuadStick.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'wx',
        'wx.grid',
        'wx.adv',
        'serial',
        'hid',
        'pyrfc6266',
        'certifi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QuadStick',
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
    codesign_identity=None,
    entitlements_file=None,
    icon='quadstickx.ico',
)

collect = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QuadStick',
)

app = BUNDLE(
    collect,
    name='QuadStick.app',
    icon='quadstickx.ico',
    bundle_identifier='com.quadstick.manager',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
    },
)