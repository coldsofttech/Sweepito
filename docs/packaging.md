# Packaging and installers

Sweepito ships as a Python package on PyPI and as native installers for each operating system.
The installers bundle the Python runtime, so they need no Python on the machine.

| OS | File | Installs to | On `PATH` |
| --- | --- | --- | --- |
| Windows | `sweepito-<version>.setup.exe` | `%LOCALAPPDATA%\Programs\ColdSoft Technologies\Sweepito` (this user) or `Program Files` (all users) | optional, on by default |
| Windows | `sweepito-<version>-windows-x64.zip` | wherever you unzip it | no (portable) |
| Debian, Ubuntu | `sweepito_<version>_<arch>.deb` | `/usr/lib/sweepito` | `/usr/bin/sweepito` |
| Fedora, RHEL, openSUSE | `sweepito-<version>.<arch>.rpm` | `/usr/lib/sweepito` | `/usr/bin/sweepito` |

`<arch>` is `x86_64`/`amd64` or `arm64`. Download the files from the
[GitHub releases](https://github.com/coldsofttech/Sweepito/releases); `SHA256SUMS.txt` lists their
checksums.

## Install and remove

**Windows.** Run the setup, or silently:

```powershell
sweepito-0.1.0.setup.exe /S /currentuser          # this user, no administrator needed
sweepito-0.1.0.setup.exe /S /allusers             # all users (UAC prompt)
sweepito-0.1.0.setup.exe /S /NOPATH /D=C:\Tools\Sweepito
```

Remove it in Settings > Apps, or run `uninstall.exe /S` from the install folder.

**Linux.**

```bash
sudo apt-get install ./sweepito_0.1.0_amd64.deb    # remove: sudo apt-get remove sweepito
sudo dnf install ./sweepito-0.1.0.x86_64.rpm       # remove: sudo dnf remove sweepito
```

Every installer removes only the files it installed. Settings and your projects are never touched.

## Build them yourself

An installer is built on the OS it is for (PyInstaller does not cross-compile), from the project's
metadata: names and version from `pyproject.toml` and `sweepito.__version__`.

```bash
uv sync --group installer
uv run python scripts/build_installer.py --smoke   # writes dist/installer/
```

`--smoke` starts the frozen program and checks that it reports its version and loads the bundled
profiles. Extra tools, pinned in `installer/tools.toml`:

- Windows: [NSIS](https://nsis.sourceforge.io/) (`makensis` on `PATH`)
- Linux: [nfpm](https://nfpm.goreleaser.com/) (`nfpm` on `PATH`, or set `NFPM`); `--formats deb` or
  `--formats rpm` builds one

| Path | Purpose |
| --- | --- |
| `installer/pyinstaller/cli.spec` | PyInstaller one-folder build, shared by every OS |
| `installer/windows/` | NSIS setup (`cli.nsi`, `common.nsh`) and the `PATH` helper (`path.ps1`) |
| `installer/linux/nfpm.yaml` | deb and rpm layout |
| `installer/tools.toml` | versions of NSIS and nfpm |

## Signing

Installers are unsigned by default, so Windows SmartScreen warns on first run.

- **Windows, any signing tool:** set `SIGN_COMMAND` to a command that signs one file, with `{file}` where its path
  goes. The executable and the setup are signed. In CI, store it as the repository variable
  `SIGN_COMMAND`.

## CI and releases

- `.github/workflows/installers.yml` builds every installer on pull requests that touch
  `installer/`, `src/` or the build script, and installs, runs and uninstalls each one.
- `.github/workflows/release.yml` builds them on a version tag and attaches them, with
  `SHA256SUMS.txt`, to the GitHub release. A failing installer stops the release before PyPI.
