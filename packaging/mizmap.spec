# PyInstaller spec for MizMap. One-folder build, no console (tray icon owns the
# lifecycle). Build with: `uv run pyinstaller packaging/mizmap.spec`.
#
# Key wrinkles handled here:
#   - mizmap/proto_gen/__init__.py manipulates sys.path so generated stubs
#     resolve under `from dcs.* import ...` rather than the deep dotted
#     name. PyInstaller's static analyzer can't follow that, so we ship the
#     entire proto_gen directory as data files; the on-disk sys.path shim
#     resolves them at runtime.
#   - web/ lives outside the mizmap package; bundled at the root of the
#     extraction dir, where mizmap.paths.web_dir() looks for it.
#   - grpcio has Cython extensions + many submodules; collect_all() pulls
#     them in.
#   - mizmap.dev (mock harness) is excluded; it's only useful in source-tree
#     development.

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).resolve().parent  # repo root
MIZMAP_PKG = ROOT / "mizmap"

grpc_datas, grpc_binaries, grpc_hiddenimports = collect_all("grpc")
# The generated *_pb2.py modules import `google.protobuf.*` and
# `google.protobuf.internal.*` dynamically — they're not statically reachable
# from any import in our codebase, so PyInstaller's analyzer misses them.
pb_datas, pb_binaries, pb_hiddenimports = collect_all("google.protobuf")

def _proto_gen_datas() -> list:
    """Enumerate mizmap/proto_gen/ .py files for bundling as data.

    Skips:
      - `__pycache__/*.pyc` — .pyc files embed the build host's absolute
        source path in `co_filename` (for tracebacks). Bundling the dev
        machine's pre-compiled bytecode leaks that path into the install.
        Python regenerates the .pyc on first import at runtime; the cost
        is a one-time compile.
      - `*.pyi` type stubs — runtime-unused, save a few KB.
    """
    src_root = MIZMAP_PKG / "proto_gen"
    bundle_prefix = Path("mizmap/proto_gen")
    out = []
    for src in src_root.rglob("*"):
        if not src.is_file():
            continue
        if "__pycache__" in src.parts:
            continue
        if src.suffix == ".pyi":
            continue
        # Keep proto_gen's structure under mizmap/proto_gen/ in the bundle so
        # mizmap.proto_gen.__init__'s sys.path shim resolves `from dcs.*` correctly.
        rel = src.relative_to(src_root).parent
        out.append((str(src), (bundle_prefix / rel).as_posix()))
    return out


datas = [
    (str(ROOT / "web"), "web"),
    (str(MIZMAP_PKG / "data" / "units.yaml"), "mizmap/data"),
    (str(MIZMAP_PKG / "data" / "mizmap.ico"), "mizmap/data"),
]
# proto_gen ships as data so mizmap.proto_gen.__init__'s sys.path hook can
# find `dcs/...` modules on disk at runtime.
datas += _proto_gen_datas()
datas += grpc_datas + pb_datas

hiddenimports = [
    # FastAPI / uvicorn workers and their loops.
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    # pystray Windows backend (otherwise lazy-imported via __import__).
    "pystray._win32",
    # Pillow is only used for the tray-icon glyph; PIL imports are dynamic.
    "PIL.ImageDraw",
    "PIL.ImageFont",
] + grpc_hiddenimports + pb_hiddenimports

excludes = [
    # Mock DCS-gRPC server is a dev tool, never useful in the frozen exe.
    "mizmap.dev",
    "mizmap.dev.mock_server",
    # grpcio-tools is dev-only (proto regen). Belt-and-braces — the
    # pyproject.toml change keeps it out of the env to begin with.
    "grpc_tools",
    "grpcio_tools",
]

a = Analysis(
    [str(ROOT / "packaging" / "mizmap_launcher.py")],
    pathex=[str(ROOT)],
    binaries=grpc_binaries + pb_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="mizmap",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # tray icon owns the lifecycle; no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(MIZMAP_PKG / "data" / "mizmap.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="mizmap",
)
