# PyInstaller spec for the Sweepito command line: one console executable, one-folder build, any OS.
#
#   sweepito(.exe)   the command line
#   lib/             the Python runtime and the dependencies
#
# One-folder build on purpose (no one-file build): it starts faster and antivirus tools trust it
# more. scripts/build_installer.py runs this; by hand, from the repository root:
#   uv sync --group installer
#   uv run pyinstaller installer/pyinstaller/cli.spec --noconfirm \
#       --distpath build/installer --workpath build/installer-work

import sys
from pathlib import Path

from PyInstaller.config import CONF
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve().parents[1]
NAME = "sweepito"
WINDOWS = sys.platform == "win32"
ICON_DIR = ROOT / "brand"
ICON_SUFFIX = ".ico" if WINDOWS else None
ICON = next(iter(sorted(ICON_DIR.rglob(f"*{ICON_SUFFIX}"), key=lambda p: ("dark" not in p.parts, p))), None) if ICON_SUFFIX else None

# Profiles are TOML files read through importlib.resources, and the modules load lazily, so
# PyInstaller's own scan would miss them.
hiddenimports = collect_submodules("sweepito")
datas = collect_data_files("sweepito")

# A launcher, so the executable calls main() the way the console script does.
launcher = Path(CONF["workpath"]) / "sweepito_launcher.py"
launcher.parent.mkdir(parents=True, exist_ok=True)
launcher.write_text(
    "import sys\nfrom sweepito.cli import main\n\nif __name__ == '__main__':\n"
    "    sys.exit(main())\n",
    encoding="utf-8",
)

a = Analysis(
    [str(launcher)],
    pathex=[str(ROOT / "src")],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "_pytest", "setuptools", "pkg_resources", "pip"],
)
# Package metadata is only read to look up versions, which this program never does.
a.datas = [d for d in a.datas if ".dist-info" not in d[0]]
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    contents_directory="lib",
    name=NAME,
    console=True,
    icon=str(ICON) if ICON else None,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name=NAME, upx=False)
