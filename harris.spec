# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['harris_entry.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'harris.cli.login',
        'harris.cli.orders',
        'harris.cli.inventory',
        'harris.cli.listings',
        'harris.cli.pricing',
        'harris.cli.reports',
        'harris.cli.admin',
        'harris.cli.auth',
        'harris.platforms.amazon',
        'harris.platforms.base',
        'rich.logging',
        'typer',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='harris',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)
