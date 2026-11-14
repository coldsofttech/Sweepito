#!/usr/bin/env python3
"""Build the Sweepito installers: a PyInstaller folder, then a native package for this OS.

    Windows   dist/installer/sweepito-<version>.setup.exe (NSIS) and a portable .zip
    Linux     dist/installer/sweepito_<version>_<arch>.deb and sweepito-<version>.<arch>.rpm (nfpm)
    macOS     dist/installer/sweepito-<version>-macos-<arch>.pkg and a .tar.gz

Names, version, description, author, homepage and license come from pyproject.toml and
``sweepito.__version__``, so renaming the project needs no edit here. Tool versions are pinned in
installer/tools.toml. An installer is built on the OS it is for: PyInstaller does not cross-compile.

Signing is off by default.
  Windows  set SIGN_COMMAND to a command that signs one file, with {file} where its path goes
           (a signtool or SignPath call); the executable and the setup.exe are signed.
  macOS    set MACOS_CODESIGN_IDENTITY ("Developer ID Application: ...") to sign the executables
           and MACOS_INSTALLER_IDENTITY ("Developer ID Installer: ...") to sign the .pkg.
           Notarization is a separate step (see docs/packaging.md).

Usage:  uv sync --group installer
        uv run python scripts/build_installer.py [--sync] [--smoke] [--formats deb rpm]
See docs/packaging.md for the details.
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build" / "installer"
WORK = ROOT / "build" / "installer-work"
OUT = ROOT / "dist" / "installer"
SPEC = ROOT / "installer" / "pyinstaller" / "cli.spec"
NSIS_FILE = ROOT / "installer" / "windows" / "cli.nsi"
NFPM_CONFIG = ROOT / "installer" / "linux" / "nfpm.yaml"
MACOS_DIR = ROOT / "installer" / "macos"

WINDOWS = sys.platform == "win32"
LINUX = sys.platform.startswith("linux")
MACOS = sys.platform == "darwin"

PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
NAME: str = PROJECT["name"]  # also the command's name ([project.scripts])
TITLE = NAME.capitalize()
URLS: dict[str, str] = PROJECT.get("urls", {})
AUTHOR: dict[str, str] = (PROJECT.get("authors") or [{}])[0]
PUBLISHER = AUTHOR.get("name", TITLE)
BUNDLE_ID = f"io.github.{PUBLISHER.lower()}.{NAME}"


def read_version() -> str:
    text = (ROOT / "src" / NAME / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit("__version__ not found in the package.")
    return match.group(1)


VERSION = read_version()


def run(command: list[str], *, env: dict[str, str] | None = None, cwd: Path = ROOT) -> None:
    print("+", " ".join(shlex.quote(part) for part in command), flush=True)
    subprocess.run(command, check=True, cwd=cwd, env=env)


def machine() -> str:
    """The CPU architecture, normalised: x86_64 or arm64."""
    return {"amd64": "x86_64", "aarch64": "arm64"}.get(
        platform.machine().lower(), platform.machine().lower()
    )


def sign_windows(files: list[Path]) -> None:
    """Sign ``files`` with SIGN_COMMAND, if it is set; otherwise do nothing."""
    template = os.environ.get("SIGN_COMMAND", "").strip()
    if not template:
        return
    if "{file}" not in template:
        raise SystemExit("SIGN_COMMAND must contain {file}, where the file to sign goes.")
    for file in files:
        command = template.replace("{file}", f'"{file}"')
        print("+", command, flush=True)
        # SIGN_COMMAND is set by whoever runs the build (a CI variable), so it is trusted input.
        subprocess.run(command, check=True, cwd=ROOT, shell=True)  # noqa: S602


# ---- PyInstaller -------------------------------------------------------------------------------
def freeze() -> Path:
    """Run PyInstaller and return its output folder (build/installer/sweepito)."""
    run(
        [
            sys.executable, "-m", "PyInstaller", str(SPEC), "--noconfirm",
            "--distpath", str(BUILD), "--workpath", str(WORK),
        ]
    )  # fmt: skip
    return BUILD / NAME


def executable(folder: Path) -> Path:
    return folder / (f"{NAME}.exe" if WINDOWS else NAME)


# ---- Windows: NSIS -----------------------------------------------------------------------------
def find_makensis() -> str:
    found = shutil.which("makensis")
    if found:
        return found
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        candidate = Path(os.environ.get(variable, "")) / "NSIS" / "makensis.exe"
        if candidate.is_file():
            return str(candidate)
    raise SystemExit("makensis not found. Install NSIS (version in installer/tools.toml).")


def numeric_version(version: str) -> str:
    numbers = re.findall(r"\d+", version)[:4]
    return ".".join(numbers + ["0"] * (4 - len(numbers)))


def optional_brand(pattern: str) -> Path | None:
    """The first file in brand/ matching ``pattern``, if the project has a brand folder."""
    folder = ROOT / "brand"
    return next(iter(sorted(folder.rglob(pattern))), None) if folder.is_dir() else None


def package_windows(folder: Path) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    sign_windows([executable(folder)])
    setup = OUT / f"{NAME}-{VERSION}.setup.exe"
    icon = optional_brand("*.ico")
    flags = {
        "APP_NAME": TITLE,
        "APP_VERSION": VERSION,
        "APP_VERSION_NUMERIC": numeric_version(VERSION),
        "SOURCE_DIR": str(folder),
        "OUT_FILE": str(setup),
        "ICON_FILE": str(icon) if icon else "",
        "LICENSE_FILE": str(ROOT / "LICENSE"),
        "PUBLISHER": PUBLISHER,
        "URL": URLS.get("Homepage", ""),
    }
    command = [find_makensis(), "/V2"]
    command += [f"/D{key}={value}" for key, value in flags.items() if value]
    run([*command, str(NSIS_FILE)])
    sign_windows([setup])
    portable = shutil.make_archive(
        str(OUT / f"{NAME}-{VERSION}-windows-{'x64' if machine() == 'x86_64' else machine()}"),
        "zip",
        root_dir=folder,
    )
    return [setup, Path(portable)]


# ---- Linux: nfpm -------------------------------------------------------------------------------
def normalise_modes(folder: Path) -> None:
    """Folders 755, files 644, and 755 for anything executable, whatever the build umask was."""
    for path in [folder, *folder.rglob("*")]:
        if path.is_symlink():
            continue
        if path.is_dir() or path.stat().st_mode & stat.S_IXUSR or ".so" in path.name:
            path.chmod(0o755)
        else:
            path.chmod(0o644)


def package_linux(folder: Path, formats: list[str]) -> list[Path]:
    """Build the deb and rpm packages."""
    normalise_modes(folder)
    OUT.mkdir(parents=True, exist_ok=True)
    maintainer = AUTHOR.get("name", "")
    if AUTHOR.get("email"):
        maintainer = f"{maintainer} <{AUTHOR['email']}>"
    license_value = PROJECT.get("license", "")
    if isinstance(license_value, dict):  # the legacy table form; "MIT" is an SPDX id
        license_value = "MIT"
    env = {
        **os.environ,
        "PKG_NAME": NAME,
        "PKG_VERSION": VERSION,
        "PKG_ARCH": {"x86_64": "amd64", "arm64": "arm64"}.get(machine(), machine()),
        "PKG_DESCRIPTION": str(PROJECT.get("description", NAME)),
        "PKG_MAINTAINER": maintainer,
        "PKG_HOMEPAGE": URLS.get("Homepage", ""),
        "PKG_LICENSE": str(license_value) or "MIT",
        "PKG_SOURCE_DIR": str(folder),
        "PKG_LICENSE_FILE": str(ROOT / "LICENSE"),
    }
    nfpm = shlex.split(os.environ.get("NFPM", "nfpm"))
    if shutil.which(nfpm[0]) is None:
        raise SystemExit("nfpm not found. Install it (version in installer/tools.toml) or set NFPM.")
    before = set(OUT.iterdir())

    def package(packager: str) -> None:
        run(
            [*nfpm, "package", "--config", str(NFPM_CONFIG), "--packager", packager,
             "--target", str(OUT)],
            env=env,
        )  # fmt: skip

    with ThreadPoolExecutor(max_workers=len(formats)) as pool:
        for future in [pool.submit(package, packager) for packager in formats]:
            future.result()
    return sorted(set(OUT.iterdir()) - before)


# ---- macOS: pkgbuild and productbuild ----------------------------------------------------------
def package_macos(folder: Path) -> list[Path]:
    """A system-wide .pkg (files in /usr/local/lib/sweepito, command in /usr/local/bin) and a tarball."""
    OUT.mkdir(parents=True, exist_ok=True)
    arch = machine()
    codesign = os.environ.get("MACOS_CODESIGN_IDENTITY", "").strip()
    if codesign:
        # Every Mach-O file (the executable, the interpreter library, extension modules) is signed
        # with the hardened runtime, which notarization requires.
        for path in sorted(p for p in folder.rglob("*") if p.is_file() and not p.is_symlink()):
            if path.suffix in {".so", ".dylib"} or path == executable(folder):
                run(["codesign", "--force", "--timestamp", "--options", "runtime",
                     "--sign", codesign, str(path)])  # fmt: skip
    normalise_modes(folder)

    stage = WORK / "macos"
    shutil.rmtree(stage, ignore_errors=True)
    payload = stage / "payload"
    lib = payload / "usr" / "local" / "lib" / NAME
    bin_dir = payload / "usr" / "local" / "bin"
    shutil.copytree(folder, lib, symlinks=True)
    shutil.copy2(MACOS_DIR / "uninstall.sh", lib / "uninstall.sh")
    (lib / "uninstall.sh").chmod(0o755)
    bin_dir.mkdir(parents=True)
    (bin_dir / NAME).symlink_to(f"../lib/{NAME}/{NAME}")

    component = stage / f"{NAME}-component.pkg"
    run(["pkgbuild", "--root", str(payload), "--identifier", BUNDLE_ID, "--version", VERSION,
         "--install-location", "/", str(component)])  # fmt: skip

    resources = stage / "resources"
    resources.mkdir()
    shutil.copy2(ROOT / "LICENSE", resources / "LICENSE.txt")
    distribution = (MACOS_DIR / "distribution.xml.in").read_text(encoding="utf-8")
    for key, value in {
        "TITLE": TITLE,
        "IDENTIFIER_PREFIX": PUBLISHER,
        "IDENTIFIER": BUNDLE_ID,
        "VERSION": VERSION,
        "COMPONENT": component.name,
        "HOST_ARCH": arch,
    }.items():
        distribution = distribution.replace(f"@{key}@", value)
    distribution_file = stage / "distribution.xml"
    distribution_file.write_text(distribution, encoding="utf-8")

    pkg = OUT / f"{NAME}-{VERSION}-macos-{arch}.pkg"
    command = ["productbuild", "--distribution", str(distribution_file),
               "--resources", str(resources), "--package-path", str(stage)]  # fmt: skip
    installer_identity = os.environ.get("MACOS_INSTALLER_IDENTITY", "").strip()
    if installer_identity:
        command += ["--sign", installer_identity, "--timestamp"]
    run([*command, str(pkg)])

    tarball = OUT / f"{NAME}-{VERSION}-macos-{arch}.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        archive.add(folder, arcname=NAME)
    return [pkg, tarball]


# ---- smoke test --------------------------------------------------------------------------------
def smoke(folder: Path) -> None:
    """Start the frozen program: it reports its version and loads the bundled profiles."""
    exe = str(executable(folder))
    result = subprocess.run([exe, "--version"], capture_output=True, text=True, check=True)
    if VERSION not in result.stdout + result.stderr:
        raise SystemExit(f"{exe} --version did not report {VERSION}: {result.stdout!r}")
    # The profiles are data files inside the bundle; this fails if PyInstaller left them out.
    result = subprocess.run([exe, "profiles", "--json"], capture_output=True, text=True)
    if result.returncode != 0 or "python" not in result.stdout.lower():
        raise SystemExit(f"{exe} profiles failed ({result.returncode}): {result.stderr}")
    print(f"smoke test passed: {exe}")


def sync() -> None:
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("--sync needs uv on PATH.")
    run([uv, "sync", "--inexact", "--group", "installer"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sync", action="store_true", help="uv sync the installer group first")
    parser.add_argument("--smoke", action="store_true", help="run the built executable and check it")
    parser.add_argument("--formats", nargs="+", default=["deb", "rpm"], choices=["deb", "rpm"],
                        help="Linux package formats")  # fmt: skip
    args = parser.parse_args()

    if not (WINDOWS or LINUX or MACOS):
        raise SystemExit("Installers are built on Windows, Linux and macOS only.")
    if args.sync:
        sync()
    folder = freeze()
    if args.smoke:
        smoke(folder)
    if WINDOWS:
        built = package_windows(folder)
    elif MACOS:
        built = package_macos(folder)
    else:
        built = package_linux(folder, args.formats)
    print("\nBuilt:")
    for path in built:
        print(f"  {path.relative_to(ROOT)}  ({path.stat().st_size / 1_048_576:.1f} MB)")


if __name__ == "__main__":
    main()
