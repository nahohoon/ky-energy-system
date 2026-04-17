# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# 현재 spec 파일 위치를 기준으로 경로 설정
spec_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    [os.path.join(spec_dir, 'launcher.py')],
    pathex=[spec_dir],
    binaries=[],
    datas=[
        (os.path.join(spec_dir, 'templates'), 'templates'),
        (os.path.join(spec_dir, 'static'),    'static'),
        (os.path.join(spec_dir, 'app.py'),    '.'),
        (os.path.join(spec_dir, 'config.py'), '.'),
        (os.path.join(spec_dir, 'models.py'), '.'),
        (os.path.join(spec_dir, 'init_db.py'),'.'),
        (os.path.join(spec_dir, 'routes'),    'routes'),
    ],
    hiddenimports=[
        'flask',
        'flask.templating',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.routing',
        'werkzeug.serving',
        'werkzeug.middleware.shared_data',
        'sqlalchemy',
        'sqlalchemy.orm',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.pool',
        'flask_sqlalchemy',
        'sqlite3',
        'routes',
        'routes.dashboard',
        'routes.equipment',
        'routes.operation',
        'routes.energy',
        'routes.simulation',
        'routes.maintenance',
        'routes.inventory',
        'email.mime.text',
        'email.mime.multipart',
        'pkg_resources',
        'click',
        'itsdangerous',
        'markupsafe',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'pandas',
        'scipy', 'PIL', 'cv2', 'test', 'unittest',
    ],
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
    name='스마트에너지시스템',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='스마트에너지시스템',
)
