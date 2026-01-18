# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\soura\\OneDrive\\Desktop\\MyTodoApp\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\soura\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python313\\site-packages\\customtkinter', 'customtkinter'), ('C:\\Users\\soura\\OneDrive\\Desktop\\MyTodoApp\\assets', 'assets')],
    hiddenimports=['plyer.platforms.win.notification', 'pystray', 'PIL', 'sqlalchemy.sql.default_comparator'],
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
    [],
    exclude_binaries=True,
    name='MyModernTodo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\soura\\OneDrive\\Desktop\\MyTodoApp\\assets\\logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MyModernTodo',
)
